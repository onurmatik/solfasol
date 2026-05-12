from __future__ import annotations

import base64
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fabric import Connection, task
from invoke import Collection


DEPLOY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DEPLOY_DIR.parent

load_dotenv(DEPLOY_DIR / ".credentials.env")
load_dotenv(DEPLOY_DIR / "deploy.env")


def get_env(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value is None:
            continue
        value = value.strip()
        if value:
            return value
    return None


def env_value(
    *names: str,
    default: Optional[str] = None,
    required: bool = False,
    hint: Optional[str] = None,
) -> Optional[str]:
    value = get_env(*names)
    if value:
        return value
    if required:
        if hint:
            raise RuntimeError(f"Missing required environment variable: {hint}")
        raise RuntimeError(f"Missing required environment variable: {' or '.join(names)}")
    return default


def require_env(*names: str, hint: Optional[str] = None) -> str:
    value = env_value(*names, required=True, hint=hint)
    assert value is not None
    return value


def env_bool(*names: str, default: bool = False) -> bool:
    raw = get_env(*names)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


ENV_GITHUB_APP_REPO = ("GITHUB_APP_REPO",)
ENV_DOMAIN = ("DOMAIN_NAME", "DOMAIN")
ENV_HOST = ("DEPLOY_HOST", "HOST")
ENV_DEPLOY_USER = ("DEPLOY_USER",)
ENV_APP_USER = ("APP_USER",)
ENV_KEY_FILENAME = ("KEY_FILENAME",)
ENV_PROJECT_NAME = ("PROJECT_NAME",)
ENV_ENABLE_CELERY = ("ENABLE_CELERY", "DEPLOY_ENABLE_CELERY")
ENV_SSH_PORT = ("SSH_PORT", "DEPLOY_PORT")
ENV_CONNECT_TIMEOUT = ("SSH_CONNECT_TIMEOUT", "DEPLOY_CONNECT_TIMEOUT")


USER = env_value(*ENV_DEPLOY_USER, default="ubuntu")
APP_USER = env_value(*ENV_APP_USER, default=USER)


PROJECT_NAME = env_value(*ENV_PROJECT_NAME, default=PROJECT_ROOT.name)


def debug(msg: str) -> None:
    print(f"[fab] {msg}")


def get_github_token() -> Optional[str]:
    if not get_env("GITHUB_APP_ID") or not get_env("GITHUB_APP_INSTALLATION_ID"):
        debug("GitHub App credentials not configured; continuing without installation token")
        return None

    debug("Refreshing GitHub token via helper script")
    script_path = Path(__file__).resolve().parent / "scripts" / "get_github_app_token.py"
    if not script_path.is_file():
        debug(f"Token helper {script_path} missing")
        return None
    debug(f"Running token helper {script_path}")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        debug("GitHub token helper failed; continuing without installation token")
        if result.stderr.strip():
            debug(result.stderr.strip())
        return None
    token = result.stdout.strip()
    if token:
        debug("Fetched GitHub App installation token via helper")
    else:
        debug("Helper returned empty token")
    return token or None


GITHUB_TOKEN = get_github_token()


def get_repo_url() -> str:
    github_repo = require_env(*ENV_GITHUB_APP_REPO)
    return f"https://github.com/{github_repo}.git"


PROJECT_DIR = f"/srv/apps/{PROJECT_NAME}"
VENV_DIR = f"{PROJECT_DIR}/venv"
PYTHON_BIN = f"{VENV_DIR}/bin/python"
ENV_FILE = f"{PROJECT_DIR}/.env"
ENV_FILE_CANDIDATES = [
    PROJECT_ROOT / ".env-prod",
    PROJECT_ROOT / ".env",
]
REQUIRED_SES_ENV_KEYS = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_DEFAULT_REGION",
]
PERSISTED_PATHS = [
    ".env",
    "db.sqlite3",
    "media",
    "venv",
    "staticfiles",
]


def quote(value: str) -> str:
    return shlex.quote(value)


def run_as_app_user(
    c,
    command: str,
    *,
    cwd: Optional[str] = None,
    warn: bool = False,
):
    if USER == APP_USER:
        if cwd:
            with c.cd(cwd):
                return c.run(command, warn=warn)
        return c.run(command, warn=warn)

    snippet = command
    if cwd:
        snippet = f"cd {quote(cwd)} && {command}"
    return c.sudo(f"bash -lc {quote(snippet)}", user=APP_USER, warn=warn)


def remote_exists(c, path: str) -> bool:
    return c.run(f"test -e {quote(path)}", warn=True, hide=True).ok


def remote_dir_is_empty(c, path: str) -> bool:
    return c.run(
        f"test -z \"$(find {quote(path)} -mindepth 1 -maxdepth 1 -print -quit)\"",
        warn=True,
        hide=True,
    ).ok


def ensure_project_dir(c) -> None:
    c.run(f"mkdir -p {quote(PROJECT_DIR)}")
    if USER != APP_USER:
        c.sudo(f"chown -R {quote(APP_USER)}:{quote(APP_USER)} {quote(PROJECT_DIR)}")


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def validate_env_file(path: Path) -> None:
    values = read_env_file(path)
    if values.get("EMAIL_BACKEND") != "django_ses.SESBackend":
        return

    missing = [key for key in REQUIRED_SES_ENV_KEYS if not values.get(key)]
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(f"{path.name} is missing required SES env keys: {missing_text}")


def upload_env_file(c) -> None:
    source = next((path for path in ENV_FILE_CANDIDATES if path.is_file()), None)
    if not source:
        debug("No .env file found; skipping environment upload")
        return

    validate_env_file(source)
    remote_tmp = f"/tmp/{source.name}"
    debug(f"Uploading env file {source} to {ENV_FILE}")
    c.put(str(source), remote_tmp)
    c.sudo(f"mv {quote(remote_tmp)} {quote(ENV_FILE)}")
    c.sudo(f"chown {quote(APP_USER)}:{quote(APP_USER)} {quote(ENV_FILE)}")
    c.sudo(f"chmod 600 {quote(ENV_FILE)}")


def git_with_header(c, git_command: str, token: str, cwd: Optional[str] = None) -> bool:
    auth = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    cmd = (
        f'GIT_TERMINAL_PROMPT=0 git -c credential.helper= -c http.extraHeader="Authorization: Basic {auth}" {git_command}'
    )
    location = cwd or "current directory"
    debug(f"Running git command in {location}: git {git_command}")
    result = run_as_app_user(c, cmd, cwd=cwd, warn=True)

    if result.failed:
        debug(f"git command failed with exit code {result.return_code}")
        return False
    return True


def run_plain_git(c, git_command: str, cwd: Optional[str] = None) -> None:
    debug(f"Running git command without token: git {git_command}")
    run_as_app_user(c, f"git {git_command}", cwd=cwd)


def run_git_command(c, git_command: str, cwd: Optional[str] = None, use_token: bool = False) -> None:
    global GITHUB_TOKEN
    if use_token and GITHUB_TOKEN:
        debug("Executing git command")
        if git_with_header(c, git_command, GITHUB_TOKEN, cwd=cwd):
            return
        raise RuntimeError("Git command failed")
    else:
        run_plain_git(c, git_command, cwd=cwd)


def clone_repo(c, repo_url: str, target_dir: str) -> None:
    clone_command = f"clone {quote(repo_url)} {quote(target_dir)}"
    if GITHUB_TOKEN and repo_url.startswith("https://"):
        debug("Cloning repository over HTTPS with token")
        run_git_command(c, clone_command, use_token=True)
        run_as_app_user(c, f"git -C {quote(target_dir)} remote set-url origin {quote(repo_url)}")
    else:
        debug(f"Cloning repository using {repo_url}")
        run_git_command(c, clone_command)


def bootstrap_existing_non_git_dir(c, repo_url: str) -> None:
    timestamp = c.run("date +%Y%m%d%H%M%S", hide=True).stdout.strip()
    backup_dir = f"{PROJECT_DIR}.pre-git-{timestamp}"

    debug(
        f"{PROJECT_DIR} exists but is not a git checkout; "
        f"moving it to {backup_dir} before cloning."
    )
    c.sudo(f"mv {quote(PROJECT_DIR)} {quote(backup_dir)}")
    c.sudo(f"mkdir -p {quote(PROJECT_DIR)}")
    c.sudo(f"chown {quote(APP_USER)}:{quote(APP_USER)} {quote(PROJECT_DIR)}")

    clone_repo(c, repo_url, PROJECT_DIR)

    for item in PERSISTED_PATHS:
        source = f"{backup_dir}/{item}"
        target = f"{PROJECT_DIR}/{item}"
        if not remote_exists(c, source):
            continue
        debug(f"Restoring persisted path: {item}")
        c.sudo(f"rm -rf {quote(target)}", warn=True)
        c.sudo(f"mv {quote(source)} {quote(target)}")
        c.sudo(f"chown -R {quote(APP_USER)}:{quote(APP_USER)} {quote(target)}")

    debug(f"Left one-time bootstrap backup at {backup_dir}")


@task
def deploy(c):
    """Deploy the project to the server."""
    key_filename = require_env(*ENV_KEY_FILENAME)
    host = require_env(*ENV_HOST)
    port = int(env_value(*ENV_SSH_PORT, default="22"))
    connect_timeout = int(env_value(*ENV_CONNECT_TIMEOUT, default="10"))
    repo_url = get_repo_url()

    debug(f"Using repo URL: {repo_url}")
    debug(
        f"Connecting to {USER}@{host}:{port} with key {key_filename}; "
        f"app user={APP_USER}"
    )
    c = Connection(
        host=host,
        user=USER,
        port=port,
        connect_timeout=connect_timeout,
        connect_kwargs={
            "key_filename": str(Path(f"~/.ssh/{key_filename}").expanduser())
        },
    )

    try:
        ensure_project_dir(c)
    except TimeoutError as exc:
        print(
            f"SSH connection to {USER}@{host}:{port} timed out after "
            f"{connect_timeout}s. Check that the server is running, the IP is "
            "correct, and firewall/provider rules allow SSH from this network. "
            "If SSH uses a custom port, set SSH_PORT in deploy.env.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    repo_has_git = c.run(f"test -d {quote(PROJECT_DIR)}/.git", warn=True).ok
    debug(f"Repo exists on server: {repo_has_git}")

    if not repo_has_git:
        if remote_dir_is_empty(c, PROJECT_DIR):
            clone_repo(c, repo_url, PROJECT_DIR)
        else:
            bootstrap_existing_non_git_dir(c, repo_url)
    else:
        debug("Updating existing repo with hard reset + pull on main")
        use_token = bool(GITHUB_TOKEN and repo_url.startswith("https://"))
        if use_token:
            run_git_command(c, "fetch origin main --prune", cwd=PROJECT_DIR, use_token=True)
        else:
            run_git_command(c, "fetch origin main --prune", cwd=PROJECT_DIR)
        run_git_command(c, "checkout main", cwd=PROJECT_DIR, use_token=False)
        run_git_command(c, "reset --hard origin/main", cwd=PROJECT_DIR, use_token=False)
        if use_token:
            run_git_command(c, "pull --ff-only origin main", cwd=PROJECT_DIR, use_token=True)
        else:
            run_git_command(c, "pull --ff-only origin main", cwd=PROJECT_DIR)

    upload_env_file(c)

    if c.run(f"test -d {quote(VENV_DIR)}", warn=True).failed:
        debug("Creating virtualenv")
        run_as_app_user(c, f"python3 -m venv {quote(VENV_DIR)}")

    debug("Installing Python requirements")
    run_as_app_user(c, f"{quote(VENV_DIR)}/bin/pip install --upgrade pip", cwd=PROJECT_DIR)
    run_as_app_user(c, f"{quote(VENV_DIR)}/bin/pip install -r requirements.txt", cwd=PROJECT_DIR)
    debug("Running collectstatic & migrate")
    run_as_app_user(c, f"{quote(PYTHON_BIN)} manage.py collectstatic --noinput", cwd=PROJECT_DIR)
    run_as_app_user(c, f"{quote(PYTHON_BIN)} manage.py migrate", cwd=PROJECT_DIR)

    enable_celery = env_bool(*ENV_ENABLE_CELERY, default=False)

    debug("Restarting services (best effort)")
    c.sudo(f"systemctl stop app@{PROJECT_NAME}.service", warn=True)
    c.sudo(f"systemctl restart app@{PROJECT_NAME}.socket", warn=True)
    if enable_celery:
        c.sudo(f"systemctl try-restart celery@{PROJECT_NAME}.service", warn=True)
    else:
        debug(
            f"Skipping celery@{PROJECT_NAME}.service restart "
            f"(ENABLE_CELERY/DEPLOY_ENABLE_CELERY is not enabled)"
        )
    reset_units = f"app@{PROJECT_NAME}.service app@{PROJECT_NAME}.socket"
    if enable_celery:
        reset_units = f"{reset_units} celery@{PROJECT_NAME}.service"
    c.sudo(f"systemctl reset-failed {reset_units}", warn=True)

ns = Collection(deploy)
