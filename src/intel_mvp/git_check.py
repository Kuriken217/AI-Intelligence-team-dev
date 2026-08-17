from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitPreflightResult:
    is_git_repo: bool
    branch: str
    clean: bool
    has_remote: bool
    gh_available: bool
    status: str
    remotes: str


def run_git_preflight(repo_path: Path) -> GitPreflightResult:
    git = find_git()
    if not git:
        return GitPreflightResult(False, "", False, False, False, "git executable not found", "")

    is_repo = command_ok([git, "rev-parse", "--is-inside-work-tree"], repo_path)
    if not is_repo:
        return GitPreflightResult(False, "", False, False, gh_available(), "not a git repository", "")

    branch = command_output([git, "branch", "--show-current"], repo_path)
    status = command_output([git, "status", "--short"], repo_path)
    remotes = command_output([git, "remote", "-v"], repo_path)
    return GitPreflightResult(
        is_git_repo=True,
        branch=branch.strip(),
        clean=not status.strip(),
        has_remote=bool(remotes.strip()),
        gh_available=gh_available(),
        status=status,
        remotes=remotes,
    )


def find_git() -> str | None:
    bundled = Path(r"C:\Users\kurib\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe")
    if bundled.exists():
        return str(bundled)
    return shutil.which("git")


def gh_available() -> bool:
    return shutil.which("gh") is not None


def command_ok(command: list[str], cwd: Path) -> bool:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True).returncode == 0


def command_output(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return completed.stdout if completed.returncode == 0 else completed.stderr


def format_preflight(result: GitPreflightResult) -> str:
    lines = [
        f"is_git_repo={str(result.is_git_repo).lower()}",
        f"branch={result.branch}",
        f"clean={str(result.clean).lower()}",
        f"has_remote={str(result.has_remote).lower()}",
        f"gh_available={str(result.gh_available).lower()}",
    ]
    if result.remotes.strip():
        lines.append("remotes:")
        lines.append(result.remotes.strip())
    if result.status.strip():
        lines.append("status:")
        lines.append(result.status.strip())
    return "\n".join(lines)


def main() -> int:
    result = run_git_preflight(Path.cwd())
    print(format_preflight(result))
    return 0 if result.is_git_repo and result.clean else 1


if __name__ == "__main__":
    raise SystemExit(main())

