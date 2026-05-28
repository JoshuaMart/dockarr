# Updates

Dockarr uses a **GitOps** workflow: the pinned image versions in
`docker-compose.yml` are the single source of truth, and every change goes
through Git.

## The flow

1. **Renovate** watches the image tags and opens a pull request when a new
   version is released.
2. You **review** the PR (changelog, breaking changes) and **merge** what you
   want. Skip or schedule the rest.
3. On the VPS, deploy the merged change:

   ```bash
   make update
   ```

   which runs `git pull --ff-only && docker compose pull && docker compose up -d`
   and prunes dangling images.

This means you always know exactly which versions run, you read the changelog
before applying, and you can roll back instantly with `git revert`.

## Enabling Renovate

1. Install the [Renovate GitHub App](https://github.com/apps/renovate) on the
   `dockarr` repository.
2. The included `renovate.json` already:
   - watches every `docker-compose*.yml`,
   - pins floating `latest` tags to a digest for reproducibility,
   - groups all stack updates into one PR,
   - labels major bumps (e.g. Jellyfin) and never auto-merges.
3. Renovate opens a **Dependency Dashboard** issue listing everything it tracks.

!!! note "Why not Watchtower?"
    Watchtower is archived and updates containers in place with no review and
    no version history. The Renovate + `make update` flow keeps you in control
    and makes every deployment traceable in Git.

## Manual update

Without Renovate you can still bump a version by editing the tag in
`docker-compose.yml`, committing, then running `make update` on the VPS.
