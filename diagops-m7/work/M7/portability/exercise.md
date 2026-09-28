# Essai de portabilité du brief 1

Deux essais, deux natures de changement :

1. **changer le stockage** (starter `lab.py`) : JSON → SQLite, même score
   lexical ;
2. **changer le moteur de classement** (`fts5.py`) : score lexical → SQLite FTS5
   (tokenizer `unicode61`, BM25), même export et mêmes contrôles d'entrée.

Environnement : Windows 11, Python 3.12.10, SQLite 3.49.1 (FTS5 embarqué),
aucune dépendance, aucun téléchargement.

## Essai 1 — stockage JSON → SQLite

```bash
python lab.py --output results/decouverte-r2
```

| Mesure | Valeur |
|---|---|
| documents exportés | 7 actifs sur 8 (révision remplacée exclue) |
| classement JSON / SQLite / après rollback | identique sur les 12 questions |
| hit@3 avant / après | 1,0 / 1,0 |
| corruption du candidat | détectée ; retour au JSON |
| taille | export 9 835 octets ; SQLite 40 960 octets |
| durées sur ce poste | migration 4,9 ms ; reprise 9,7 ms |

### Incompatibilité trouvée avant même de chercher

Le starter ne passait pas ses propres tests sous Windows, et son export n'était
pas portable :

- les connexions SQLite ouvertes par `with sqlite3.connect(...)` ne sont pas
  fermées : sous Windows, le fichier reste verrouillé, et les 6 tests
  échouaient au nettoyage (`WinError 32`) ;
- l'export était écrit en CRLF sous Windows. Même corpus, deux empreintes :
  **`7c8fb23d…` (CRLF, 9 974 octets) contre `12ea939d…` (LF, 9 835 octets)**.
  Le classement ne bouge pas, mais `source_export_sha256`, enregistré dans
  l'index SQLite, ne correspond plus à un export refait sur un autre système.
  Un index construit sur un poste ne se rattache donc pas à sa source rejouée
  sur un autre.

Remédiation : `closing()` sur chaque connexion, et écriture LF imposée dans
`save()`. Les 6 tests passent, et l'avant/après est conservé dans
`results/decouverte-r1` (CRLF) et `results/decouverte-r2` (LF). Leçon pour le
contrat d'export du brief 2 : il fixe la sérialisation **au niveau des
octets** (encodage, fins de ligne, ordre des clés), sinon une empreinte ne
prouve rien d'un système à l'autre.

## Essai 2 — moteur de classement : lexical → FTS5

```bash
python scripts/portability_fts5.py --output results/portabilite-fts5-r1
```

### Incompatibilité provoquée, constatée, corrigée

Première écriture, celle qu'on fait naturellement : la question brute passée à
`MATCH`. **12 questions sur 12 échouent.** Les erreurs observées : `no such
column: il` (×4, « faut-il »), `no such column: t` et `elle` (formes
interrogatives à trait d'union), `no such column: on`, `syntax error near "?"`
(×2) et `near "."`. Le trait d'union et la ponctuation sont des opérateurs de
la syntaxe FTS5.

Correction : la question est tokenisée avec la même expression régulière que
`lab.py`, chaque terme est mis entre guillemets et les termes sont reliés par
`OR`. Un terme reste un terme, jamais un opérateur. Test :
`tests/test_fts5.py::test_raw_question_breaks_fts5_and_quoted_query_does_not`.

### Comparaison

| Backend | hit@3 | top 3 identique à la référence | top 1 identique | sans réponse avec résultats | p50 12 requêtes |
|---|---|---|---|---|---|
| lexical JSON (référence) | 1,0 | 12/12 | 12/12 | 2/2 | 4,4 ms |
| lexical SQLite | 1,0 | 12/12 | 12/12 | 2/2 | 8,9 ms |
| FTS5 index partagé | 1,0 | **3/12** | 10/12 | 2/2 | 7,6 ms |
| FTS5 index par rôle | 1,0 | 3/12 | 10/12 | 2/2 | 7,6 ms |

| Construction | Durée | Taille |
|---|---|---|
| SQLite lexical | 4,6 ms | 40 960 o |
| FTS5 partagé | 4,8 ms | 81 920 o |
| FTS5 par rôle | 6,5 ms | 184 320 o (×2,25) |

Lecture :

- **le hit@3 ne voit rien.** Il vaut 1,0 partout alors que le classement FTS5
  diffère de la référence sur 9 questions sur 12. Sur 7 documents, la mesure
  sature : le M4 avait fait le même constat (Recall@1 à 1,000 sur 8 documents).
  Parité du classement et qualité ne sont pas la même chose, et aucune des
  deux n'est la qualité d'une réponse générée ;
- **aucun backend ne sait s'abstenir** : les deux questions sans réponse
  (RAG-CAL-011 lubrifiant, RAG-CAL-012 date de panne) reçoivent trois
  documents partout ;
- **le tokenizer change le sens de l'égalité** : `unicode61` neutralise les
  accents (« procedure » trouve « procédure »), le lexical non. C'est un
  changement de comportement, pas une perte ;
- **perte de format** : le score FTS5 (BM25, négatif, relatif au corpus) n'est
  pas comparable au score lexical (entier, absolu). Tout seuil réglé sur l'un
  est à refaire sur l'autre.

### Droits : aucune fuite, un canal auxiliaire

11 phrases du document restreint utilisées comme requêtes, rôles `public` et
`technicien`, 4 backends : **0 renvoi**.

Mais dans l'**index partagé**, où tous les documents sont dans la même table
FTS et le rôle est filtré dans la même requête, le document restreint entre
dans les statistiques BM25. Comparé au même index sans ce document, il modifie
les scores visibles d'un technicien sur **10 requêtes sur 10** et son
classement sur **2** (RAG-CAL-004, RAG-CAL-007). L'**index par rôle** donne des
scores identiques au corpus sans le document restreint (10/10). Le filtre était
bien appliqué avant la sortie, pas avant le calcul. Ce constat n'était pas
prévu : il est apparu en vérifiant que « droits avant classement » tenait
toujours après la migration.

## Ce que l'essai établit, et ce qu'il n'établit pas

Établi : une alternative de classement fonctionne localement sans perte de
droits, à condition de neutraliser la syntaxe de requête et d'isoler les
statistiques par rôle. Le coût est un index 2,25 fois plus gros.

Non établi : qu'elle soit meilleure. La calibration ne peut pas le dire. Le
brief 2 écrira et gèlera ses propres cas avant de mesurer, avec des questions
qui départagent vraiment les deux classements.
