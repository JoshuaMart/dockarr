# Mises à jour

Dockarr utilise un workflow **GitOps** : les versions d'images épinglées dans
`docker-compose.yml` sont l'unique source de vérité, et chaque changement passe
par Git.

## Le flux

1. **Renovate** surveille les tags d'images et ouvre une pull request dès
   qu'une nouvelle version sort.
2. Vous **relisez** la PR (changelog, ruptures de compatibilité) et fusionnez
   ce que vous voulez. Le reste est ignoré ou reporté.
3. Sur le VPS, déployez le changement fusionné :

   ```bash
   make update
   ```

   qui exécute `git pull --ff-only && docker compose pull && docker compose up -d`
   et nettoie les images orphelines.

Vous savez ainsi toujours exactement quelles versions tournent, vous lisez le
changelog avant d'appliquer, et vous pouvez revenir en arrière instantanément
avec `git revert`.

## Activer Renovate

1. Installez la [GitHub App Renovate](https://github.com/apps/renovate) sur le
   dépôt `dockarr`.
2. Le fichier `renovate.json` fourni fait déjà :
   - surveille tous les `docker-compose*.yml`,
   - épingle les tags flottants `latest` sur un digest (reproductibilité),
   - regroupe toutes les mises à jour dans une seule PR,
   - étiquette les montées de version majeures (ex. Jellyfin) et ne fusionne
     jamais automatiquement.
3. Renovate ouvre une issue **Dependency Dashboard** listant tout ce qu'il
   suit.

## Mise à jour manuelle

Sans Renovate, vous pouvez toujours monter une version en éditant le tag dans
`docker-compose.yml`, en committant, puis en lançant `make update` sur le VPS.
