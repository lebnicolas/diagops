#!/usr/bin/env python3
"""Test de capacité local du service RAG — profil annoncé, pas charge maximale.

Le brief demande de mesurer débit, latence p50/p95, erreurs et **le premier point de saturation**,
sans toucher à un service externe ni de production. Cet outil envoie un profil de requêtes défini
d'avance, à concurrence croissante, et rend des mesures comparables entre paliers.

Trois partis pris de méthode :

1. **Un palier de chauffe est exclu des mesures.** Le premier appel paie l'import, la lecture de
   l'index et l'établissement de connexion — le compter reviendrait à mesurer le démarrage.
2. **Les latences sont rendues en percentiles, jamais en moyenne.** Une moyenne cache exactement
   ce qu'on cherche : la queue de distribution. C'est la leçon des estimateurs robustes du M3,
   appliquée à la performance.
3. **Le profil vient des questions d'évaluation**, pas de chaînes inventées. Charger un service
   RAG avec des requêtes qui ne ressemblent pas aux vraies mesure la plomberie, pas le service.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

import httpx


def percentile(valeurs: list[float], part: float) -> float:
    """Percentile par interpolation linéaire, sur une liste déjà triée."""
    if not valeurs:
        return 0.0
    ordonnees = sorted(valeurs)
    if len(ordonnees) == 1:
        return ordonnees[0]
    position = part * (len(ordonnees) - 1)
    bas = int(position)
    haut = min(bas + 1, len(ordonnees) - 1)
    return ordonnees[bas] + (ordonnees[haut] - ordonnees[bas]) * (position - bas)


def profil(questions: Path, split: str = "calibration") -> list[dict]:
    """Profil réaliste : les questions d'évaluation, avec leur rôle."""
    entrees = [
        json.loads(ligne)
        for ligne in questions.read_text(encoding="utf-8").splitlines()
        if ligne.strip()
    ]
    return [
        {"question": entree["question"], "role": entree.get("role", "technicien")}
        for entree in entrees
        if entree.get("split") == split
    ]


async def un_appel(client: httpx.AsyncClient, url: str, charge: dict) -> tuple[float, int]:
    debut = time.perf_counter()
    try:
        reponse = await client.post(url, json=charge, timeout=10.0)
        return time.perf_counter() - debut, reponse.status_code
    except (httpx.HTTPError, asyncio.TimeoutError):
        return time.perf_counter() - debut, 0


async def palier(url: str, requetes: list[dict], concurrence: int, duree: float) -> dict:
    """Un palier à concurrence fixe, pendant `duree` secondes."""
    latences: list[float] = []
    codes: list[int] = []
    verrou = asyncio.Semaphore(concurrence)
    fin = time.perf_counter() + duree
    compteur = 0

    async with httpx.AsyncClient() as client:
        async def travailleur() -> None:
            nonlocal compteur
            while time.perf_counter() < fin:
                async with verrou:
                    charge = requetes[compteur % len(requetes)]
                    compteur += 1
                    latence, code = await un_appel(client, url, charge)
                    latences.append(latence)
                    codes.append(code)

        debut = time.perf_counter()
        await asyncio.gather(*[travailleur() for _ in range(concurrence)])
        ecoule = time.perf_counter() - debut

    reussies = [code for code in codes if 200 <= code < 300]
    return {
        "concurrence": concurrence,
        "duree_s": round(ecoule, 2),
        "requetes": len(codes),
        "debit_rps": round(len(codes) / ecoule, 1) if ecoule else 0.0,
        "erreurs": len(codes) - len(reussies),
        "taux_erreur": round((len(codes) - len(reussies)) / len(codes), 4) if codes else 0.0,
        "p50_ms": round(percentile(latences, 0.50) * 1000, 2),
        "p95_ms": round(percentile(latences, 0.95) * 1000, 2),
        "p99_ms": round(percentile(latences, 0.99) * 1000, 2),
        "max_ms": round(max(latences) * 1000, 2) if latences else 0.0,
        "moyenne_ms": round(statistics.fmean(latences) * 1000, 2) if latences else 0.0,
    }


async def campagne(url: str, requetes: list[dict], paliers: list[int], duree: float) -> list[dict]:
    # Palier de chauffe, écarté des résultats : il paie l'établissement des connexions et le
    # premier accès à l'index. Le garder ferait passer un coût de démarrage pour une latence.
    await palier(url, requetes, 1, 2.0)
    resultats = []
    for concurrence in paliers:
        resultats.append(await palier(url, requetes, concurrence, duree))
        # Respiration entre paliers : sans elle, la file du palier précédent pollue le suivant.
        await asyncio.sleep(1.0)
    return resultats


def saturation(resultats: list[dict], seuil_p95_ms: float) -> dict:
    """Premier palier où le service cesse de tenir son contrat.

    Deux critères, le premier atteint l'emporte : le p95 dépasse le seuil annoncé, ou le débit
    cesse de croître alors que la concurrence augmente (le service est en file d'attente).
    """
    precedent = None
    for resultat in resultats:
        if resultat["taux_erreur"] > 0.01:
            return {"palier": resultat["concurrence"], "motif": "taux d'erreur au-dessus de 1 %"}
        if resultat["p95_ms"] > seuil_p95_ms:
            return {"palier": resultat["concurrence"], "motif": f"p95 au-dessus de {seuil_p95_ms} ms"}
        if precedent and resultat["debit_rps"] < precedent["debit_rps"] * 1.05:
            return {
                "palier": resultat["concurrence"],
                "motif": "le débit ne progresse plus malgré la concurrence — mise en file",
            }
        precedent = resultat
    return {"palier": None, "motif": "aucune saturation atteinte sur les paliers testés"}


async def principal() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/search")
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--paliers", default="1,2,4,8,16,32,64")
    parser.add_argument("--duree", type=float, default=5.0, help="secondes par palier")
    parser.add_argument("--seuil-p95-ms", type=float, default=200.0)
    parser.add_argument("--sortie", type=Path, required=True)
    args = parser.parse_args()

    requetes = profil(args.questions)
    if not requetes:
        raise SystemExit("Profil vide : aucune question de calibration trouvée.")
    paliers = [int(p) for p in args.paliers.split(",")]

    print(f"Profil : {len(requetes)} requêtes distinctes, paliers {paliers}, {args.duree}s chacun")
    resultats = await campagne(args.url, requetes, paliers, args.duree)

    for resultat in resultats:
        print(
            f"  c={resultat['concurrence']:>3}  {resultat['debit_rps']:>7.1f} req/s  "
            f"p50={resultat['p50_ms']:>7.2f} ms  p95={resultat['p95_ms']:>8.2f} ms  "
            f"p99={resultat['p99_ms']:>8.2f} ms  erreurs={resultat['erreurs']}"
        )

    point = saturation(resultats, args.seuil_p95_ms)
    rapport = {
        "url": args.url,
        "profil": {"requetes_distinctes": len(requetes), "source": str(args.questions)},
        "duree_par_palier_s": args.duree,
        "seuil_p95_annonce_ms": args.seuil_p95_ms,
        "paliers": resultats,
        "saturation": point,
    }
    args.sortie.parent.mkdir(parents=True, exist_ok=True)
    args.sortie.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaturation : {point['motif']}" + (f" (c={point['palier']})" if point["palier"] else ""))
    print(f"Rapport : {args.sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(principal()))
