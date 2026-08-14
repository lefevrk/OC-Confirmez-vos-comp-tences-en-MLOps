# Credit Scoring API

API de scoring crédit ("Prêt à Dépenser") — service d'inférence, monitoring
et CI/CD. Dépôt de déploiement (Repo 2) : l'expérimentation ML (notebooks,
feature engineering, entraînement) vit dans un dépôt séparé.

## Lancer l'API

```bash
uv sync --extra api
make run
```

## Docker

```bash
make docker-build
make docker-run
```

## Tests et lint

```bash
make test
make lint
```
