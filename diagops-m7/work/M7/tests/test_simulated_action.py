"""L'outil à effet reste un contrat fictif ; l'arbitre de l'exercice respecte le contrat."""
import ast
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "simulated_action"))
import tabletop  # noqa: E402

CONTRACT = json.loads((HERE / "simulated_action/contract.json").read_text(encoding="utf-8"))
NETWORK_MODULES = {"socket", "http", "urllib", "requests", "httpx", "smtplib", "ftplib", "subprocess", "asyncio"}


class SimulatedActionTests(unittest.TestCase):
    def test_contract_stays_fictional(self):
        self.assertIs(CONTRACT["executable"], False)
        self.assertIs(CONTRACT["real_side_effects"], False)
        self.assertIsNone(CONTRACT["network_client"])
        self.assertIs(CONTRACT["registered_in_agent"], False)

    def test_tabletop_imports_nothing_that_reaches_outside(self):
        tree = ast.parse((HERE / "simulated_action/tabletop.py").read_text(encoding="utf-8"))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        self.assertFalse(imported & NETWORK_MODULES, imported & NETWORK_MODULES)

    def test_tool_absent_from_frozen_m6_registry(self):
        policy = (HERE.parents[1] / "M6/starter/agent/policy.yaml").read_text(encoding="utf-8")
        self.assertNotIn(CONTRACT["name"], policy)
        self.assertFalse(any(CONTRACT["name"] in p.read_text(encoding="utf-8")
                             for p in (HERE.parents[1] / "M6/starter/tools").glob("*.py")))

    def test_sequences(self):
        r = tabletop.play()
        self.assertTrue(r["1_nominal"]["recu"].startswith("RECU-FICTIF-"))
        s2 = r["2_refus_expiration_changement"]
        for key in ("rejet", "expiration", "changement", "reapprobation_ancien_apercu"):
            self.assertFalse(s2[key]["ok"], key)
        s3 = r["3_rejeu"]
        self.assertEqual(s3["premier_recu"], s3["second_recu"])
        self.assertEqual(s3["doublons"], 0)
        self.assertFalse(s3["meme_cle_autre_contenu"]["ok"])
        s4 = r["4_annulation_compensation"]
        self.assertEqual((s4["annulation"], s4["compensation"]), ("cancelled", "compensated"))
        self.assertFalse(s4["execution_apres_annulation"]["ok"])
        self.assertFalse(r["5_identite"]["role_technicien"]["ok"])
        self.assertFalse(r["5_identite"]["auto_approbation"]["ok"])


if __name__ == "__main__":
    unittest.main()
