"""Registre de métriques minimal, au format d'exposition Prometheus.

Repris du service RAG (`work/M5/src/observability.py`) : le brief online est autonome, donc le
module est copié plutôt qu'importé — un service qui se déploie seul ne dépend pas du répertoire
d'un autre. Seules les bornes d'histogramme diffèrent, parce que ce service mesure des
probabilités là où l'autre comptait des documents.

Pas de `prometheus_client` : `requirements.lock` est le contrat de reproductibilité du module,
et ajouter une dépendance pour trois compteurs et un histogramme reviendrait à élargir la surface
à surveiller pour économiser cinquante lignes. Le starter écrivait déjà son `/metrics` à la main.

Deux règles tenues ici :

1. **Aucune donnée métier dans les labels.** Pas de texte de requête, pas d'extrait de document,
   pas d'identifiant d'utilisateur. Le brief l'exige (« ne journalisez ni document sensible
   complet, ni prompt contenant une donnée personnelle »), et c'est aussi ce qui empêche la
   cardinalité d'exploser : une requête libre en label, c'est une série temporelle par question.
2. **Des bornes d'histogramme choisies pour les objectifs**, pas des puissances de dix. Le brief 2
   demande une détection en moins de 2 minutes sur des latences p50/p95 : il faut de la résolution
   là où le seuil se joue.
"""

from __future__ import annotations

import threading
from collections import defaultdict


# Bornes en secondes. Un retrieval lexical sur 7 documents se compte en millisecondes ;
# les bornes hautes servent à voir une dégradation, pas à décrire le nominal.
LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)

# Un histogramme de comptage n'a rien à faire sur une échelle de secondes : le top-k vaut 0, 1,
# 2 ou 3, et des bornes en millisecondes rendraient le graphe illisible.
COUNT_BUCKETS = (0.0, 1.0, 2.0, 3.0, 5.0, 10.0)

BUCKETS_BY_METRIC = {
    # Probabilité rendue par le modèle : bornes sur [0, 1], centrées autour du seuil de 0,5.
    # Voir les prédictions s'agglutiner près du seuil est le signal d'un modèle qui hésite.
    "diagops_model_probability": (0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0),
}


def buckets_for(name: str) -> tuple[float, ...]:
    return BUCKETS_BY_METRIC.get(name, LATENCY_BUCKETS)


class Metrics:
    """Compteurs et histogrammes en mémoire, protégés par un verrou.

    En mémoire : les métriques repartent de zéro au redémarrage du conteneur, ce qui est le
    comportement attendu d'un compteur Prometheus (`rate()` gère la remise à zéro). La série
    durable vit dans Prometheus, pas dans le processus.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._histograms: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = defaultdict(list)

    @staticmethod
    def _key(name: str, labels: dict[str, str] | None):
        return name, tuple(sorted((labels or {}).items()))

    def increment(self, name: str, labels: dict[str, str] | None = None, value: float = 1.0) -> None:
        with self._lock:
            self._counters[self._key(name, labels)] += value

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        with self._lock:
            self._gauges[self._key(name, labels)] = value

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        with self._lock:
            self._histograms[self._key(name, labels)].append(value)

    def counter_value(self, name: str, labels: dict[str, str] | None = None) -> float:
        with self._lock:
            return self._counters.get(self._key(name, labels), 0.0)

    def reset(self) -> None:
        """Réservé aux tests : une remise à zéro en exploitation fausserait tous les `rate()`."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()

    # -- Rendu ------------------------------------------------------------------

    @staticmethod
    def _render_labels(labels: tuple[tuple[str, str], ...]) -> str:
        if not labels:
            return ""
        inner = ",".join(f'{key}="{_escape(value)}"' for key, value in labels)
        return "{" + inner + "}"

    def render(self, helps: dict[str, tuple[str, str]]) -> str:
        """Rend l'exposition texte. `helps` donne (type, description) par nom de métrique."""
        with self._lock:
            counters = dict(self._counters)
            gauges = dict(self._gauges)
            histograms = {key: list(values) for key, values in self._histograms.items()}

        lines: list[str] = []
        emitted: set[str] = set()

        def header(name: str) -> None:
            if name in emitted:
                return
            emitted.add(name)
            kind, description = helps.get(name, ("untyped", name))
            lines.append(f"# HELP {name} {description}")
            lines.append(f"# TYPE {name} {kind}")

        for (name, labels), value in sorted(gauges.items()):
            header(name)
            lines.append(f"{name}{self._render_labels(labels)} {_number(value)}")

        for (name, labels), value in sorted(counters.items()):
            header(name)
            lines.append(f"{name}{self._render_labels(labels)} {_number(value)}")

        for (name, labels), values in sorted(histograms.items()):
            header(name)
            rendered = self._render_labels(labels)
            base = rendered[1:-1] if rendered else ""
            # Les buckets Prometheus sont cumulatifs : chaque borne compte tout ce qui est
            # inférieur ou égal, et le dernier (`+Inf`) vaut le total des observations.
            for bound in buckets_for(name):
                count = sum(1 for value in values if value <= bound)
                suffix = f'{base + "," if base else ""}le="{bound}"'
                lines.append(f"{name}_bucket{{{suffix}}} {count}")
            suffix = f'{base + "," if base else ""}le="+Inf"'
            lines.append(f"{name}_bucket{{{suffix}}} {len(values)}")
            lines.append(f"{name}_sum{rendered} {_number(sum(values))}")
            lines.append(f"{name}_count{rendered} {len(values)}")

        return "\n".join(lines) + "\n"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else repr(value)


METRICS = Metrics()
