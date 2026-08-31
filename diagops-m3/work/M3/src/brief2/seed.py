"""Graine unique du brief 2.

Toute production de ce brief — segmentation, augmentation, génération, tirage
de bruit — passe par ce module. Une exécution rejouée doit produire les mêmes
octets : la reproductibilité à graine fixe est une exigence minimale du brief,
et son absence un critère bloquant.

La graine du lot de contrôle amont est `20260825` : elle n'est volontairement
pas réutilisée ici, pour qu'aucune reproduction ne soit ambiguë.
"""

from __future__ import annotations

import numpy as np


SEED = 25082026


def rng(offset: int = 0) -> np.random.Generator:
    """Générateur aléatoire dérivé de la graine du brief.

    `offset` permet de donner à chaque procédé son propre flux sans changer la
    graine de référence : deux procédés distincts ne doivent pas consommer le
    même flux, sinon leurs résultats deviennent dépendants de l'ordre d'appel.
    """
    return np.random.default_rng(SEED + offset)
