"""Utilities to bootstrap the GTFS project from interactive environments like Jupyter notebooks.

These helpers wrap common setup steps (cloning the repository, creating a
virtual environment, installing dependencies and launching the FastAPI backend)
while providing clearer diagnostics on Windows when the ``git`` executable is
missing from the ``PATH``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import venv
from pathlib import Path
from typing import Iterable, Optional

try:  # GitPython is optional and only used as a fallback when git CLI is absent.
    from git import Repo as _GitRepo  # type: ignore
except Exception:  # pragma: no cover - GitPython is not a mandatory dependency.
    _GitRepo = None


def _default_repo_dir(repo_url: str) -> Path:
    repo_name = Path(repo_url.rstrip("/")).name
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    return Path.home() / repo_name


def _ensure_git_executable(explicit_git: Optional[str] = None) -> Optional[str]:
    if explicit_git:
        explicit_candidate = Path(explicit_git).expanduser()
        if explicit_candidate.exists():
            return str(explicit_candidate)
        resolved = shutil.which(explicit_git)
        if resolved:
            return resolved
        raise FileNotFoundError(f"Unable to locate git executable at '{explicit_git}'.")
    git_cli = shutil.which("git")
    if git_cli:
        return git_cli
    return None


def clone_or_update_repo(
    repo_url: str,
    repo_dir: Optional[Path | str] = None,
    git_executable: Optional[str] = None,
) -> Path:
    """Clone the repository if it does not exist or pull the latest changes.

    Parameters
    ----------
    repo_url:
        Remote Git URL.
    repo_dir:
        Target directory (defaults to ``~/repo-name``).
    git_executable:
        Optional explicit path (or command name) to the git executable.

    Returns
    -------
    Path
        Directory where the repository resides.
    """
    destination = Path(repo_dir).expanduser() if repo_dir else _default_repo_dir(repo_url)
    git_cli = _ensure_git_executable(git_executable)

    if git_cli:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            subprocess.run([git_cli, "-C", str(destination), "pull"], check=True)
        else:
            subprocess.run([git_cli, "clone", repo_url, str(destination)], check=True)
        return destination

    if _GitRepo is None:
        raise FileNotFoundError(
            "Git executable not found. Install Git (https://git-scm.com/downloads) "
            "and ensure it is on PATH, or install GitPython with "
            "`pip install gitpython` to use the fallback implementation."
        )

    if destination.exists():
        repo = _GitRepo(destination)
        repo.remotes.origin.pull()
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        _GitRepo.clone_from(repo_url, str(destination))
    return destination


def create_virtualenv(repo_dir: Path, env_name: str = ".venv") -> Path:
    """Create (or reuse) a virtual environment inside ``repo_dir``."""
    venv_dir = repo_dir / env_name
    if not venv_dir.exists():
        builder = venv.EnvBuilder(with_pip=True, clear=False)
        builder.create(venv_dir)
    return venv_dir


def get_python_binary(venv_dir: Path) -> Path:
    """Return the Python interpreter path for the virtual environment."""
    if os.name == "nt":
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"
    if not candidate.exists():
        raise FileNotFoundError(
            f"Python interpreter not found in virtualenv at '{candidate}'. "
            "The environment might be corrupted; recreate it with create_virtualenv()."
        )
    return candidate


def install_requirements(python_bin: Path, requirements_file: Path) -> None:
    """Install dependencies listed in ``requirements_file`` using pip."""
    subprocess.run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python_bin), "-m", "pip", "install", "-r", str(requirements_file)], check=True)


def run_command(args: Iterable[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess command and return the completed process."""
    return subprocess.run(list(map(str, args)), cwd=str(cwd) if cwd else None, check=True, text=True)


def launch_backend_api(
    python_bin: Path,
    repo_dir: Path,
    *,
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = True,
) -> subprocess.Popen[bytes]:
    """Launch the FastAPI backend using Uvicorn and return the process handle."""
    uvicorn_cmd = [
        str(python_bin),
        "-m",
        "uvicorn",
        "backend.app.main:create_app",
        "--factory",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        uvicorn_cmd.append("--reload")
    return subprocess.Popen(uvicorn_cmd, cwd=str(repo_dir))


def stop_process(process: subprocess.Popen[bytes]) -> None:
    """Terminate a background process started with :func:`launch_backend_api`."""
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
