from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app  # noqa: E402

REQUIRED_DOCUMENTS = (
    "README.md",
    "docs/database.md",
    "docs/resume-storage.md",
    "docs/resume-parsing.md",
    "docs/resume-api.md",
    "docs/phase1-completion.md",
)

REQUIRED_MIGRATIONS = (
    "backend/migrations/versions/20260803_0001_create_users_profiles_and_refresh_tokens.py",
    "backend/migrations/versions/20260803_0002_create_resumes.py",
    "backend/migrations/versions/20260803_0003_add_resume_parsing.py",
)

REQUIRED_OPERATIONS = {
    ("post", "/api/v1/auth/register"),
    ("post", "/api/v1/auth/login"),
    ("post", "/api/v1/auth/refresh"),
    ("get", "/api/v1/auth/me"),
    ("get", "/api/v1/users/me"),
    ("patch", "/api/v1/users/me"),
    ("delete", "/api/v1/users/me"),
    ("post", "/api/v1/users/me/profile"),
    ("get", "/api/v1/users/me/profile"),
    ("patch", "/api/v1/users/me/profile"),
    ("delete", "/api/v1/users/me/profile"),
    ("post", "/api/v1/resume/upload"),
    ("get", "/api/v1/resume/history"),
    ("get", "/api/v1/resume/{resume_id}"),
    ("delete", "/api/v1/resume/{resume_id}"),
    ("post", "/api/v1/resume/{resume_id}/parse"),
    ("get", "/api/v1/resume/{resume_id}/parse-status"),
    ("get", "/api/v1/resume/{resume_id}/parsed"),
    ("get", "/api/v1/resume/{resume_id}/viewer"),
    ("get", "/api/v1/resume/{resume_id}/file"),
}

FORBIDDEN_SUFFIXES = {
    ".db",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".sqlite",
    ".sqlite3",
}

FORBIDDEN_SEGMENTS = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "htmlcov",
    "storage",
}

SECRET_ASSIGNMENT = re.compile(
    r"(?im)^[ \t]*(POSTGRES_PASSWORD|JWT_ACCESS_SECRET|JWT_REFRESH_SECRET|"
    r"AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN)"
    r"[ \t]*=[ \t]*([^\r\n]*)$"
)

PLACEHOLDER_MARKERS = (
    "change",
    "dummy",
    "example",
    "fake",
    "not-set",
    "none",
    "null",
    "placeholder",
    "replace",
    "sample",
    "test",
    "your-",
    "your_",
    "<",
)

TEXT_SUFFIXES = {
    ".env",
    ".example",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def run_git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=PROJECT_ROOT,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def tracked_files() -> list[str]:
    result = run_git("ls-files", "-z")
    return [path for path in result.stdout.split("\0") if path]


def check_required_files() -> list[str]:
    failures: list[str] = []

    for relative in (*REQUIRED_DOCUMENTS, *REQUIRED_MIGRATIONS):
        if not (PROJECT_ROOT / relative).is_file():
            failures.append(f"Required file is missing: {relative}")

    return failures


def check_required_operations() -> list[str]:
    paths = app.openapi()["paths"]
    return [
        f"Required API operation is missing: {method.upper()} {path}"
        for method, path in sorted(REQUIRED_OPERATIONS)
        if path not in paths or method not in paths[path]
    ]


def check_ignore_rules() -> list[str]:
    failures: list[str] = []

    for relative in (
        "backend/.env",
        "backend/storage/.phase1-audit-probe",
    ):
        result = run_git(
            "check-ignore",
            "--quiet",
            "--no-index",
            relative,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"Git ignore rule is missing for: {relative}")

    return failures


def check_forbidden_tracked_files(paths: list[str]) -> list[str]:
    failures: list[str] = []

    for relative in paths:
        path = Path(relative)
        lower_parts = {part.lower() for part in path.parts}
        lower_name = path.name.lower()

        if lower_name == ".env":
            failures.append(f"Private environment file is tracked: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append(f"Sensitive/generated file is tracked: {relative}")
        if lower_parts & FORBIDDEN_SEGMENTS:
            failures.append(f"Cache or uploaded storage is tracked: {relative}")
        if lower_name in {".coverage", "coverage.xml"}:
            failures.append(f"Coverage artifact is tracked: {relative}")

    return failures


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name == ".env.example"


def is_placeholder(value: str) -> bool:
    normalized = value.strip().strip("\"'").strip().lower()
    return not normalized or any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def check_committed_secrets(paths: list[str]) -> list[str]:
    failures: list[str] = []

    for relative in paths:
        path = PROJECT_ROOT / relative
        if not path.is_file() or not is_text_candidate(path):
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for match in SECRET_ASSIGNMENT.finditer(content):
            key, value = match.groups()
            if not is_placeholder(value):
                line_number = content.count("\n", 0, match.start()) + 1
                failures.append(f"Possible committed secret in {relative}:{line_number} ({key})")

    return failures


def check_whitespace() -> list[str]:
    result = run_git("diff", "--check", check=False)
    if result.returncode == 0:
        return []
    return [result.stdout.strip() or result.stderr.strip()]


def main() -> int:
    checks = (
        ("required files", check_required_files()),
        ("API contract", check_required_operations()),
        ("Git ignore rules", check_ignore_rules()),
    )

    paths = tracked_files()
    extended_checks = (
        ("tracked generated files", check_forbidden_tracked_files(paths)),
        ("tracked secrets", check_committed_secrets(paths)),
        ("whitespace", check_whitespace()),
    )

    failures: list[str] = []
    for label, messages in (*checks, *extended_checks):
        if messages:
            print(f"[FAIL] {label}")
            for message in messages:
                print(f"  - {message}")
            failures.extend(messages)
        else:
            print(f"[PASS] {label}")

    if failures:
        print(f"\nPhase 1 audit failed with {len(failures)} issue(s).")
        return 1

    print("\nPhase 1 repository audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
