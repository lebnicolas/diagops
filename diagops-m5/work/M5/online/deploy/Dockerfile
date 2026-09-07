# Image d'inférence du détecteur de provenance M4.
#
# Version de base identique à celle du service RAG : une seule ligne de base à suivre pour les
# correctifs de sécurité, un seul digest à relever au registre de versions.
FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/online

# Les dépendances avant le code : une modification de src/ ne réinstalle pas scikit-learn.
COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

COPY src/ src/
COPY artefact/ artefact/

# L'artefact voyage DANS l'image, pas dans un volume : le modèle fait 1,9 ko et il définit ce que
# l'image fait. Les séparer permettrait de servir un autre modèle sous le même tag — exactement
# l'attribution qu'on cherche à rendre impossible.
RUN mkdir -p /workspace/online/artifacts && chown -R 65532:65532 /workspace/online

USER 65532:65532
EXPOSE 8000
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", \
     "--timeout-keep-alive", "10", "--timeout-graceful-shutdown", "10"]
