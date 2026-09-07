# Rapport de capacité — service RAG DiagOps

> Phase 1 du brief 2, mesurée le **07/09/2026**. Outil : `game_day/charge.py`, local, sans aucun
> service externe. Toutes les valeurs viennent de mesures ; celles qui ne sont pas concluantes
> sont signalées comme telles.

## Profil annoncé

Le brief demande de mesurer **sur un profil annoncé**, pas de chercher le maximum absolu.

| | |
|---|---|
| Requêtes | les **12 questions de calibration** du jeu d'évaluation, avec leur rôle |
| Endpoint | `POST /search` |
| Paliers | concurrence 1, 2, 4, 6, 8, 12, 16 |
| Durée | 6 s par palier, plus une chauffe de 2 s **exclue des mesures** |
| Contrat annoncé | **p95 < 200 ms**, taux d'erreur < 1 % |
| Banc | stack RAG seule, service de scoring arrêté, poste 16 cœurs |

Charger un service RAG avec des chaînes inventées mesurerait la plomberie, pas le service : le
profil reprend les vraies questions. La chauffe est écartée parce que le premier appel paie
l'import, la lecture de l'index et l'établissement de connexion — le compter ferait passer un
coût de démarrage pour une latence.

## Mesures

| Concurrence | Débit (req/s) | p50 | p95 | p99 | max | Erreurs |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 172,2 | 5,95 ms | 8,76 ms | 10,19 ms | — | 0 |
| **2** | **177,5** | 11,12 ms | 16,48 ms | 21,64 ms | — | 0 |
| 4 | 148,9 | 25,44 ms | 40,31 ms | 51,45 ms | — | 0 |
| 6 | 134,8 | 38,49 ms | 86,95 ms | 125,38 ms | — | 0 |
| **8** | 110,3 | 52,46 ms | **187,62 ms** | 277,31 ms | — | 0 |
| 12 | 85,1 | 77,91 ms | 489,52 ms | 1 487 ms | — | 0 |
| 16 | 67,3 | 103,00 ms | 836,99 ms | 1 370 ms | — | 0 |

**Zéro erreur sur tous les paliers.** Le service ne casse pas sous charge — il ralentit.

## Premier point de saturation

Deux lectures, et elles ne donnent pas le même chiffre. Les deux comptent.

**Saturation en débit : dès la concurrence 2.** Le débit plafonne à ~175 req/s et **décroît**
ensuite. Ajouter des clients n'ajoute pas de travail accompli, seulement de l'attente : c'est la
signature d'un traitement sérialisé.

**Saturation contractuelle : concurrence 8.** C'est le dernier palier qui tient le p95 annoncé —
187,62 ms pour un seuil de 200 ms, sans marge. Au palier suivant le p95 est multiplié par 2,6.

> **Capacité retenue : 8 requêtes simultanées, ~110 req/s, p95 sous 200 ms.**
> Au-delà, le service répond toujours — mais plus dans son contrat.

Le p99 est le signal d'alerte avancé : il décroche dès la concurrence 12 (1 487 ms) alors que le
p50 reste à 78 ms. **La médiane rassure pendant que la queue s'effondre** — c'est la leçon des
estimateurs robustes du M3, transposée à la performance.

## Où passe le temps

C'est le résultat le plus utile de cette campagne, et il est contre-intuitif.

Relevé côté serveur après 14 275 requêtes :

| Mesure | Valeur | Part |
|---|---:|---:|
| Latence HTTP moyenne (serveur) | **5,01 ms** | 100 % |
| Dont retrieval lexical | **0,054 ms** | **1,1 %** |
| Dont framework, validation, sérialisation | ~4,96 ms | 98,9 % |

**Le retrieval représente 1 % du temps de traitement.** Optimiser la recherche — le réflexe
naturel sur un service RAG — ne donnerait rien : diviser 0,054 ms par dix économiserait 0,05 ms
sur 5. Le coût est ailleurs, dans le coût fixe par requête du framework.

Conséquence pour le game day : un scénario « latence du retrieval multipliée » devra multiplier
le retrieval par **environ cent** pour être seulement visible sur la latence HTTP.

## Ressources — ce qui ne limite pas

Relevé pendant la charge (limites du conteneur : 2,0 CPU, 1 Gio) :

| Ressource | Observé | Limite | Marge |
|---|---|---|---|
| CPU | **20 – 45 %** d'un cœur | 200 % | très large |
| Mémoire | **47,6 Mio** | 1 024 Mio | 95 % libre |
| Stockage | index 14,9 ko, historique 1 version | — | négligeable |
| Coût | **aucun appel facturé** | — | retrieval local et déterministe |

**Le service sature en n'utilisant qu'un cinquième d'un cœur.** Relever les limites du conteneur
ne changerait rien : le goulot est la sérialisation du traitement, pas la ressource allouée.

## Hypothèse testée, et non confirmée

L'explication naturelle du plafond était le mono-worker : `uvicorn` sans `--workers`, endpoints
synchrones exécutés dans un threadpool que le GIL sérialise.

**Testé** — même campagne avec `--workers 4` :

| Concurrence | Mono-worker | 4 workers |
|---:|---:|---:|
| 1 | **172,2 req/s** (p50 5,95 ms) | 20,9 req/s (p50 48,03 ms) |
| 4 | **148,9 req/s** | 80,0 req/s |
| 8 | 110,3 req/s | **137,3 req/s** |
| 16 | 67,3 req/s | 65,9 req/s |

Le résultat ne va pas dans le sens attendu : à faible concurrence, quatre workers sont **huit
fois plus lents**, avec un p50 de 48 ms remarquablement stable (p95 à 51,6 ms) — un délai fixe,
pas de la contention.

**Cause non élucidée.** Un délai constant de ~48 ms évoque un coût de répartition ou un
comportement du chemin réseau de Docker Desktop, mais ces mesures ne permettent pas de trancher,
et il vaut mieux le dire que d'habiller une hypothèse en conclusion. La configuration
**mono-worker est conservée** : c'est celle qui donne le meilleur débit sur le profil annoncé.

À instruire avant tout usage réel : ce que devient ce plafond avec plusieurs workers derrière un
vrai proxy, sur un hôte Linux.

## Limites du banc

**Le client et le service partagent le poste.** Le générateur de charge est un processus Python
sur la même machine, et le trafic traverse le port mapping de Docker Desktop (WSL2). Une part
des latences appartient à ce chemin, pas au service.

Contre-mesure tentée : rejouer le profil **en process**, sans réseau, avec `TestClient` —
**116 req/s, p50 9,85 ms**, soit *plus lent* que via HTTP conteneurisé. Le `TestClient` porte son
propre coût et ne constitue pas une référence. **Le chemin réseau n'est donc pas disqualifié
comme goulot, mais rien ne prouve qu'il en soit un.**

**Durée courte.** 6 secondes par palier : suffisant pour un p95, insuffisant pour voir une fuite
mémoire ou une dégradation lente. La mémoire est restée plate à 47 Mio, sans que cela vaille
preuve d'absence de fuite.

**Un seul endpoint.** `/search` seulement. `/metrics` est scrappé toutes les 15 s en parallèle et
n'a pas été isolé.

## Ce que cette campagne apporte au game day

| Constat | Conséquence pour l'incident |
|---|---|
| Capacité 8 req/s simultanées, p95 < 200 ms | Le profil d'injection doit rester sous ce palier, sinon on mesure la file au lieu de la panne |
| Zéro erreur, seulement du ralentissement | Une alerte sur le **taux d'erreur** ne verrait rien : le seuil utile est le **p95** |
| Le p99 décroche avant le p50 | Alerter sur le p95 ou le p99, jamais sur la moyenne ni la médiane |
| Le retrieval pèse 1 % du temps | Le scénario « latence du retrieval multipliée » doit l'être d'un facteur ~100 pour être visible |
| CPU et mémoire très en dessous des limites | Une saturation de ressource ne sera pas le mode de défaillance ; ne pas l'attendre |

## Objectifs annoncés pour le game day

Repris des objectifs formateur, **inchangés** — les mesures du brief 1 (détection 3 s, décision
75 s, restauration 4 s) les tiennent avec une marge confortable, il n'y a pas lieu de se donner
des cibles plus dures sur un dispositif dont l'incident sera cette fois choisi par un tiers.

| Étape | Objectif |
|---|---|
| Détection | < 2 min |
| Décision | < 5 min |
| Restauration | < 10 min |
| Perte de données | aucune |

Contrat de service ajouté pour cette phase : **p95 < 200 ms à concurrence 8**, taux d'erreur < 1 %.
