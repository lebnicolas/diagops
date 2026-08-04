"""Qualification des livraisons DiagOps.

Prolonge l'audit M2 pour repondre a une question qu'il ne se posait pas : un
nouveau lot peut-il rejoindre le socle publie sans en degrader la qualite ?

Le module ne corrige rien, n'integre rien et n'ecrit jamais dans `data_pack/`.
Il constate, classe, et produit une decision motivee.
"""

__all__ = ["policy", "batch", "incremental", "qualify", "report"]
