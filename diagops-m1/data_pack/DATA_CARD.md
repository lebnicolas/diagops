# DiagOps Data Pack — data card

Statut : support apprenant.

## Description

Le DiagOps Data Pack est un corpus synthetique fourni pour un parcours de
formation a la conception et l'implementation de solutions d'intelligence
artificielle appliquees a la maintenance industrielle.

Il contient des rapports techniciens, des donnees d'equipements, des mesures
capteurs, des historiques d'interventions, des evenements de maintenance, des
retours utilisateurs et un corpus image externe pour le travail multimodal.

## Origine

Les donnees textuelles, tabulaires et temporelles sont synthetiques.
Elles ont ete creees pour exercer des competences de cadrage, preparation,
entrainement, evaluation, integration, deploiement et amelioration continue.

Le corpus image M7 provient d'une source externe qui doit etre documentee dans
le manifeste avant distribution.

## Usages autorises

- Travaux de formation.
- Prototypage pedagogique.
- Evaluation de livrables dans le cadre du parcours.
- Demonstration de pipelines d'IA sur donnees controlees.

## Usages exclus

- Analyse metier reelle de maintenance industrielle.
- Entrainement d'un systeme de production.
- Comparaison scientifique entre modeles.
- Decision operationnelle ou de securite.

## Limites

Ce corpus ne constitue pas une source de connaissance metier. Les distributions,
formulations, incidents et relations entre sources sont construits pour le
parcours de formation.

Les resultats obtenus sur ce corpus ne doivent pas etre generalises a un site
industriel reel sans donnees reelles, expertise metier et validation dediee.

## Donnees annotees M1

Le pack inclut un sous-ensemble annote pour M1 :

- environ 400 exemples d'entrainement ;
- environ 100 exemples de test ;
- tache : transformer un rapport technicien en JSON DiagOps conforme.

Ces annotations servent d'intrants pedagogiques pour entrainer et evaluer le
modele M1.

