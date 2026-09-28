#!/usr/bin/env python3
"""Exercice sur table automatisé de `request_inspection_simulated`.

Ce module n'est PAS l'outil : c'est l'arbitre de l'exercice sur table. Il joue
les séquences de `approval_flow.md` sur un registre en mémoire et produit un
journal. Aucun import réseau, aucune écriture hors du dossier de sortie, aucun
enregistrement dans l'agent M6 (dont le registre est gelé). Les acteurs, les
équipements et les reçus sont fictifs.

    python simulated_action/tabletop.py --output results/action-simulee-r1
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

CONTRACT = json.loads((Path(__file__).with_name("contract.json")).read_text(encoding="utf-8"))
APPROVAL_TTL_S = CONTRACT["approval"]["ttl_seconds"]


class Refused(Exception):
    """Transition refusée : l'état ne change pas."""


def preview_hash(request: dict) -> str:
    fields = {key: request[key] for key in CONTRACT["request_fields"] if key != "idempotency_key"}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@dataclass
class Ledger:
    """Registre fictif : une entrée par clé d'idempotence, un journal append-only."""
    items: dict = field(default_factory=dict)
    journal: list = field(default_factory=list)
    receipts: int = 0

    def log(self, clock, actor, key, decision, reason, state_before, state_after, payload=""):
        self.journal.append({"t": clock, "fictional_actor": actor, "idempotency_key": key,
                             "payload_hash": payload, "decision": decision, "reason": reason,
                             "state": f"{state_before}->{state_after}"})

    # -- transitions ------------------------------------------------------------
    def draft(self, clock, actor, role, request):
        key = request["idempotency_key"]
        payload = preview_hash(request)
        if role != CONTRACT["authorized_role"]:
            self.log(clock, actor, key, "refus", "rôle non autorisé", "-", "-", payload)
            raise Refused("rôle non autorisé")
        existing = self.items.get(key)
        if existing:
            if existing["payload_hash"] != payload:
                self.log(clock, actor, key, "refus", "même clé, contenu différent", existing["state"], existing["state"], payload)
                raise Refused("même clé, contenu différent")
            self.log(clock, actor, key, "rejeu", "même clé, même contenu", existing["state"], existing["state"], payload)
            return existing
        item = {"request": request, "payload_hash": payload, "state": "previewed", "requester": actor,
                "approved_hash": None, "approved_at": None, "receipt": None}
        self.items[key] = item
        self.log(clock, actor, key, "aperçu", "contenu exact présenté", "draft", "previewed", payload)
        return item

    def approve(self, clock, approver, key, seen_hash, *, accept=True):
        item = self.items[key]
        if approver == item["requester"]:
            self.log(clock, approver, key, "refus", "le demandeur ne s'approuve pas lui-même", item["state"], item["state"])
            raise Refused("auto-approbation")
        if item["state"] != "previewed":
            self.log(clock, approver, key, "refus", f"état {item['state']}", item["state"], item["state"])
            raise Refused(f"état {item['state']}")
        if seen_hash != item["payload_hash"]:
            self.log(clock, approver, key, "refus", "l'aperçu approuvé n'est pas le contenu courant", item["state"], item["state"], seen_hash)
            raise Refused("aperçu périmé")
        before = item["state"]
        item["state"] = "approved" if accept else "rejected"
        item["approved_hash"], item["approved_at"] = (seen_hash, clock) if accept else (None, None)
        self.log(clock, approver, key, "approbation" if accept else "rejet", "décision humaine", before, item["state"], seen_hash)
        return item

    def amend(self, clock, actor, key, **changes):
        item = self.items[key]
        if item["state"] not in {"previewed", "approved"}:
            raise Refused(f"état {item['state']}")
        before = item["state"]
        item["request"] = {**item["request"], **changes}
        item["payload_hash"] = preview_hash(item["request"])
        item["state"], item["approved_hash"], item["approved_at"] = "previewed", None, None
        self.log(clock, actor, key, "modification", "l'approbation antérieure tombe", before, "previewed", item["payload_hash"])
        return item

    def execute(self, clock, actor, key):
        item = self.items[key]
        if item["state"] == "simulated_done":
            self.log(clock, actor, key, "rejeu", "déjà exécuté, même reçu", item["state"], item["state"], item["payload_hash"])
            return item["receipt"]
        if item["state"] != "approved":
            self.log(clock, actor, key, "refus", f"état {item['state']}", item["state"], item["state"])
            raise Refused(f"état {item['state']}")
        if clock - item["approved_at"] > APPROVAL_TTL_S:
            item["state"] = "expired"
            self.log(clock, actor, key, "refus", "approbation expirée", "approved", "expired")
            raise Refused("approbation expirée")
        if item["approved_hash"] != item["payload_hash"]:
            raise Refused("contenu changé après approbation")
        self.receipts += 1
        item["receipt"] = f"RECU-FICTIF-{self.receipts:04d}"
        item["state"] = "simulated_done"
        self.log(clock, actor, key, "effet simulé", item["receipt"], "approved", "simulated_done", item["payload_hash"])
        return item["receipt"]

    def cancel(self, clock, actor, key):
        item = self.items[key]
        if item["state"] in {"previewed", "approved"}:
            before, item["state"] = item["state"], "cancelled"
            self.log(clock, actor, key, "annulation", "avant effet", before, "cancelled")
            return "cancelled"
        if item["state"] == "simulated_done":
            item["state"] = "compensated"
            self.log(clock, actor, key, "compensation", f"nouvelle entrée, {item['receipt']} conservé", "simulated_done", "compensated")
            return "compensated"
        raise Refused(f"état {item['state']}")


def play() -> dict:
    """Les quatre séquences d'approval_flow.md, plus deux refus d'identité."""
    results = {}

    def request(key, reason="vibration 7,4 mm/s sur trois mesures"):
        return {"synthetic_equipment_id": "EQ-FICTIF-001", "reason": reason, "idempotency_key": key}

    def attempt(function, *args, **kwargs):
        try:
            return {"ok": True, "value": function(*args, **kwargs)}
        except Refused as exc:
            return {"ok": False, "refus": str(exc)}

    # 1. Nominal.
    ledger = Ledger()
    item = ledger.draft(0, "sup-A", "superviseur_fictif", request("K-1"))
    ledger.approve(10, "sup-B", "K-1", item["payload_hash"])
    results["1_nominal"] = {"recu": ledger.execute(20, "sup-A", "K-1"), "journal": ledger.journal}

    # 2. Refus, expiration, changement après approbation.
    ledger = Ledger()
    item = ledger.draft(0, "sup-A", "superviseur_fictif", request("K-2"))
    ledger.approve(5, "sup-B", "K-2", item["payload_hash"], accept=False)
    rejected = attempt(ledger.execute, 6, "sup-A", "K-2")
    item = ledger.draft(0, "sup-A", "superviseur_fictif", request("K-3"))
    ledger.approve(5, "sup-B", "K-3", item["payload_hash"])
    expired = attempt(ledger.execute, 5 + APPROVAL_TTL_S + 1, "sup-A", "K-3")
    item = ledger.draft(0, "sup-A", "superviseur_fictif", request("K-4"))
    old_hash = item["payload_hash"]
    ledger.approve(5, "sup-B", "K-4", old_hash)
    ledger.amend(6, "sup-A", "K-4", reason="arrêt immédiat demandé")
    changed = attempt(ledger.execute, 7, "sup-A", "K-4")
    stale_approval = attempt(ledger.approve, 8, "sup-B", "K-4", old_hash)
    results["2_refus_expiration_changement"] = {"rejet": rejected, "expiration": expired,
                                                "changement": changed, "reapprobation_ancien_apercu": stale_approval,
                                                "journal": ledger.journal}

    # 3. Rejeu.
    ledger = Ledger()
    item = ledger.draft(0, "sup-A", "superviseur_fictif", request("K-5"))
    ledger.approve(1, "sup-B", "K-5", item["payload_hash"])
    first = ledger.execute(2, "sup-A", "K-5")
    second = ledger.execute(3, "sup-A", "K-5")
    same_key_other_payload = attempt(ledger.draft, 4, "sup-A", "superviseur_fictif", request("K-5", "autre motif"))
    results["3_rejeu"] = {"premier_recu": first, "second_recu": second, "doublons": ledger.receipts - 1,
                          "meme_cle_autre_contenu": same_key_other_payload, "journal": ledger.journal}

    # 4. Annulation avant effet, compensation après.
    ledger = Ledger()
    item = ledger.draft(0, "sup-A", "superviseur_fictif", request("K-6"))
    ledger.approve(1, "sup-B", "K-6", item["payload_hash"])
    cancelled = ledger.cancel(2, "sup-A", "K-6")
    after_cancel = attempt(ledger.execute, 3, "sup-A", "K-6")
    item = ledger.draft(0, "sup-A", "superviseur_fictif", request("K-7"))
    ledger.approve(1, "sup-B", "K-7", item["payload_hash"])
    receipt = ledger.execute(2, "sup-A", "K-7")
    compensated = ledger.cancel(3, "sup-A", "K-7")
    results["4_annulation_compensation"] = {"annulation": cancelled, "execution_apres_annulation": after_cancel,
                                            "recu": receipt, "compensation": compensated,
                                            "entrees_journal_conservees": len(ledger.journal), "journal": ledger.journal}

    # 5. Identité : rôle non autorisé, auto-approbation.
    ledger = Ledger()
    wrong_role = attempt(ledger.draft, 0, "tech-C", "technicien", request("K-8"))
    item = ledger.draft(0, "sup-A", "superviseur_fictif", request("K-9"))
    self_approval = attempt(ledger.approve, 1, "sup-A", "K-9", item["payload_hash"])
    results["5_identite"] = {"role_technicien": wrong_role, "auto_approbation": self_approval, "journal": ledger.journal}
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    results = play()
    (args.output / "report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")
    for name, value in results.items():
        print(name, {k: v for k, v in value.items() if k != "journal"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
