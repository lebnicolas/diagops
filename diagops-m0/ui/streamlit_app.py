"""Interface de test DiagOps.

Permet de soumettre un rapport technicien a l'API et d'afficher le
diagnostic structure. Les rapports du jeu de donnees sont proposes en
selection pour tester rapidement plusieurs cas.

Prerequis : l'API doit tourner.
    uvicorn app.main:app --reload

Lancement :
    streamlit run ui/streamlit_app.py
"""

import json
import os
from pathlib import Path

import httpx
import streamlit as st

API_URL = os.getenv("DIAGOPS_UI_API", "http://localhost:8000")
DATA = Path(__file__).parent.parent / "data_pack/2026-S1/reports/reports.jsonl"
TIMEOUT = 180.0  # ~5 s en regime etabli, mais le 1er appel charge le modele

COULEURS = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}


@st.cache_data
def charger_rapports() -> list[dict]:
    """Charge les rapports du jeu de donnees (JSONL : un objet par ligne)."""
    if not DATA.exists():
        return []
    return [
        json.loads(ligne)
        for ligne in DATA.read_text(encoding="utf-8").splitlines()
        if ligne.strip()
    ]


def appeler_api(note: str, equipment_id: str | None, report_id: str | None) -> dict:
    """Envoie le rapport a POST /diagnose et renvoie la reponse JSON."""
    reponse = httpx.post(
        f"{API_URL}/diagnose",
        json={
            "technician_note": note,
            "equipment_id": equipment_id or None,
            "report_id": report_id or None,
        },
        timeout=TIMEOUT,
    )
    reponse.raise_for_status()
    return reponse.json()


# --- Interface -----------------------------------------------------------
st.set_page_config(page_title="DiagOps", page_icon="🔧", layout="centered")
st.title("🔧 DiagOps")
st.caption("Assistance au diagnostic de maintenance industrielle")

rapports = charger_rapports()

with st.sidebar:
    st.header("Source du rapport")
    mode = st.radio(
        "Choisir",
        ["Rapport du jeu de donnees", "Saisie libre"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"API : `{API_URL}`")
    try:
        etat = httpx.get(f"{API_URL}/health", timeout=3).json()
        st.success(f"API en ligne — modele `{etat['model']}`")
    except httpx.HTTPError:
        st.error("API injoignable. Lancer `uvicorn app.main:app --reload`")

note, equipment_id, report_id = "", "", ""

if mode == "Rapport du jeu de donnees" and rapports:
    libelles = [
        f"{r['report_id']} — {r['equipment_id']}" for r in rapports
    ]
    index = st.selectbox(
        "Rapport", range(len(libelles)), format_func=lambda i: libelles[i]
    )
    choisi = rapports[index]
    equipment_id, report_id = choisi["equipment_id"], choisi["report_id"]
    note = st.text_area("Note du technicien", choisi["technician_note"], height=160)
else:
    if mode == "Rapport du jeu de donnees":
        st.warning(f"Jeu de donnees introuvable : {DATA}")
    note = st.text_area(
        "Note du technicien",
        placeholder="La pompe P-204 vibre fortement depuis deux jours...",
        height=160,
    )
    colonne_1, colonne_2 = st.columns(2)
    equipment_id = colonne_1.text_input("equipment_id (optionnel)")
    report_id = colonne_2.text_input("report_id (optionnel)")

if st.button("Diagnostiquer", type="primary", disabled=not note.strip()):
    with st.spinner("Analyse en cours (~5 s, plus le chargement au premier appel)..."):
        try:
            resultat = appeler_api(note, equipment_id, report_id)
        except httpx.HTTPStatusError as exc:
            detail = exc.response.json().get("detail", exc.response.text)
            st.error(f"Erreur {exc.response.status_code} : {detail}")
            st.stop()
        except httpx.HTTPError as exc:
            st.error(f"API injoignable : {exc}")
            st.stop()

    severite = resultat["severity"]
    st.subheader(f"{COULEURS.get(severite, '⚪')} Severite : {severite}")

    colonne_1, colonne_2 = st.columns(2)
    colonne_1.metric("Confiance", f"{resultat['confidence']:.0%}")
    colonne_2.metric(
        "Revision humaine",
        "Requise" if resultat["requires_human_review"] else "Non requise",
    )

    st.markdown(f"**Equipement** — {resultat['equipment_id']}")
    st.markdown(f"**Symptome** — {resultat['symptom']}")
    st.markdown(f"**Hypothese de panne** — {resultat['failure_hypothesis']}")
    st.markdown(f"**Action recommandee** — {resultat['recommended_action']}")

    if resultat.get("evidence"):
        st.markdown("**Elements retenus**")
        for element in resultat["evidence"]:
            st.markdown(f"- {element}")

    with st.expander("Reponse JSON brute"):
        st.json(resultat)
