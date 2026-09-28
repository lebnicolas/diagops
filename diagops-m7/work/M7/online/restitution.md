---
module: M7
brief: brief 1 — online
support: restitution à l'équipe technique (simulée)
maj: 2026-09-28
---

# Modèle de provenance M4 — revue d'architecture

---

## 1. Le modèle est rapide, petit et reconstructible

| | Valeur | Nature |
|---|---:|---|
| Bout en bout, 1 fenêtre | 1,6 ms (p95 2,1 ms) | mesuré |
| Parc entier par jour | 109 fenêtres, 0,2 s | estimé |
| Réajustement | empreinte identique au gel | mesuré |

**Message** : la performance n'est pas le sujet. Pas d'API, un batch suffit.

---

## 2. Le vrai risque : il répond à tout

| Entrée | Réponse |
|---|---|
| 30 valeurs manquantes | `réelle` |
| 1 ligne au lieu de 30 | `réelle` |
| capteur inconnu | `réelle` |
| capteur figé | `fabriquée` (1,000) |

6 entrées invalides sur 9 prédites sans erreur (mesuré).

**Message** : un contrat d'entrée bloquant, avant toute exploitation.

---

## 3. Un traitement inégal, qu'on ne sait pas encore juger

- `pressure_bar` signalé à 57 %, `rpm` à 0 %
- SITE-SUD 40 %, SITE-EST 12,5 %
- oracle non reçu : erreur ou réalité ? inconnu

**Message** : surveiller par segment ; ne rien adopter avant l'oracle.

---

## 4. Alternatives testées

| | Existant | Retenu | Preuve |
|---|---|---|---|
| Packaging | pickle, 290 Mo | JSON, 118 Mo | 60/60 décisions identiques |
| Stockage | CSV sans version | journal SQLite + purge | exécuté |
| Environnement | poste personnel | batch sur serveur interne | non exécuté |

**Message** : moins de dépendances, plus de traçabilité, même résultat.

---

## 5. Décision et suite

**`évaluer davantage`** — maintenu.

1. oracle (formateur)
2. contrat d'entrée, lock complet, export JSON, journal
3. file de revue humaine, surveillance
4. serveur interne

À trancher avec vous : seuil de rappel (métier), pickle (sécurité),
nom du relecteur au journal (DPO), hébergement (infra).
