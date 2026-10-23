from pathlib import Path
import os
import shutil
import subprocess
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]


def run_deploy_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    if os.name == "nt":
        git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        bash = str(git_bash) if git_bash.is_file() else shutil.which("bash")
    else:
        bash = shutil.which("bash")
    assert bash, "bash is required to exercise the Linux deployment scripts"
    bash_path = Path(bash)

    def to_bash_path(path: str | Path) -> str:
        if os.name != "nt":
            return str(path)
        cygpath = bash_path.parent.parent / "usr" / "bin" / "cygpath.exe"
        converted = subprocess.run(
            [str(cygpath), "-u", str(path)], capture_output=True, check=True, text=True
        )
        return converted.stdout.strip()

    return subprocess.run(
        [str(bash_path), to_bash_path(script), *(to_bash_path(arg) for arg in args)],
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_frontend_workflow_targets_the_linux_frontend_server_and_document_root():
    workflow = (ROOT / ".github" / "workflows" / "deploy-frontend.yml").read_text(encoding="utf-8")

    assert "host: 100.100.100.101" in workflow
    assert 'port: "22"' in workflow
    assert "HTML_DIR: /var/www/html" in workflow
    assert "scripts/deploy/deploy-frontend.sh" in workflow


def test_backend_workflow_targets_the_linux_backend_home_directory():
    workflow = (ROOT / ".github" / "workflows" / "deploy-backend.yml").read_text(encoding="utf-8")

    assert "host: 100.100.100.102" in workflow
    assert 'port: "22"' in workflow
    assert "BACKEND_DIR: /home/test" in workflow
    assert "scripts/deploy/deploy-backend.sh" in workflow


def test_frontend_deployment_replaces_site_files_and_keeps_nginx_error_page():
    with TemporaryDirectory(prefix=".deploy-test-", dir=ROOT) as temp_dir:
        tmp_path = Path(temp_dir)
        staging_dir = tmp_path / "staging"
        dist_dir = staging_dir / "frontend" / "dist"
        html_dir = tmp_path / "html"
        dist_dir.mkdir(parents=True)
        html_dir.mkdir()
        (dist_dir / "index.html").write_text("new site", encoding="utf-8")
        (dist_dir / "50x.html").write_text("build error page", encoding="utf-8")
        (dist_dir / "assets").mkdir()
        (dist_dir / "assets" / "app.js").write_text("new bundle", encoding="utf-8")
        (html_dir / "index.html").write_text("old site", encoding="utf-8")
        (html_dir / "stale.js").write_text("old bundle", encoding="utf-8")
        (html_dir / "50x.html").write_text("nginx error page", encoding="utf-8")

        result = run_deploy_script(
            ROOT / "scripts" / "deploy" / "deploy-frontend.sh",
            staging_dir,
            html_dir,
        )

        assert result.returncode == 0, result.stderr
        assert (html_dir / "index.html").read_text(encoding="utf-8") == "new site"
        assert (html_dir / "assets" / "app.js").read_text(encoding="utf-8") == "new bundle"
        assert not (html_dir / "stale.js").exists()
        assert (html_dir / "50x.html").read_text(encoding="utf-8") == "nginx error page"


def test_backend_deployment_updates_code_without_touching_server_data_or_secrets():
    with TemporaryDirectory(prefix=".deploy-test-", dir=ROOT) as temp_dir:
        tmp_path = Path(temp_dir)
        staging_dir = tmp_path / "staging"
        backend_dir = tmp_path / "backend"
        (staging_dir / "app").mkdir(parents=True)
        (backend_dir / "app").mkdir(parents=True)
        (backend_dir / ".venv" / "bin").mkdir(parents=True)
        (backend_dir / "certs").mkdir()
        (staging_dir / "app" / "main.py").write_text("new code", encoding="utf-8")
        (backend_dir / "app" / "old.py").write_text("old code", encoding="utf-8")
        (staging_dir / "requirements.txt").write_text("fastapi==1.0", encoding="utf-8")
        (backend_dir / "requirements.txt").write_text("fastapi==0.9", encoding="utf-8")
        (backend_dir / ".env").write_text("SECRET_KEY=keep", encoding="utf-8")
        (backend_dir / "app.db").write_bytes(b"user data")
        (backend_dir / ".venv" / "bin" / "python").write_text("existing venv", encoding="utf-8")
        (backend_dir / "certs" / "private.key").write_text("existing certificate", encoding="utf-8")

        result = run_deploy_script(
            ROOT / "scripts" / "deploy" / "deploy-backend.sh",
            staging_dir,
            backend_dir,
        )

        assert result.returncode == 0, result.stderr
        assert (backend_dir / "app" / "main.py").read_text(encoding="utf-8") == "new code"
        assert not (backend_dir / "app" / "old.py").exists()
        assert (backend_dir / "requirements.txt").read_text(encoding="utf-8") == "fastapi==1.0"
        assert (backend_dir / ".env").read_text(encoding="utf-8") == "SECRET_KEY=keep"
        assert (backend_dir / "app.db").read_bytes() == b"user data"
        assert (backend_dir / ".venv" / "bin" / "python").read_text(encoding="utf-8") == "existing venv"
        assert (backend_dir / "certs" / "private.key").read_text(encoding="utf-8") == "existing certificate"


def test_runtime_examples_configure_direct_api_and_cross_origin_auth():
    backend_env = (ROOT / ".env.example").read_text(encoding="utf-8")
    frontend_env = (ROOT / "frontend" / ".env.example").read_text(encoding="utf-8")

    for setting in ("FRONTEND_URL", "FRONTEND_ORIGINS", "COOKIE_DOMAIN", "COOKIE_SECURE", "KAKAO_REDIRECT_URI"):
        assert setting in backend_env
    assert "VITE_API_BASE=https://api.kkoi.kro.kr" in frontend_env
