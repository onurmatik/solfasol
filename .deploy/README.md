
cd .deploy/
fab deploy

# Deploy will upload ../.env-prod (preferred) or ../.env to /srv/apps/{PROJECT_NAME}/.env

# Users
- `DEPLOY_USER`: SSH/sudo user. Hetzner hosts usually use `root`.
- `APP_USER`: runtime owner for the checkout, venv, `.env`, and Django commands.

# Node-free deploy
The deploy task does not run `npm` or restart `node@{PROJECT_NAME}.service`; built static assets must already be present in the repo before deploy.

# Files
- `.credentials.env`: GitHub App credentials used by `scripts/get_github_app_token.py`
- `deploy.env`: per-project deploy config (PROJECT_NAME, GITHUB_APP_REPO, DEPLOY_HOST, DOMAIN, etc.)

# Tip
Copy `.deploy` between projects and only edit `deploy.env` to point at the new repo/host/domain.

# Optional
- Set `ENABLE_CELERY=true` in `deploy.env` only for apps that actually run a Celery worker.
