from app.main import app

REQUIRED_PHASE1_OPERATIONS = {
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


def test_phase1_openapi_contract_is_complete() -> None:
    paths = app.openapi()["paths"]
    missing = sorted(
        f"{method.upper()} {path}"
        for method, path in REQUIRED_PHASE1_OPERATIONS
        if path not in paths or method not in paths[path]
    )

    assert missing == []


def test_private_resume_operations_declare_authentication() -> None:
    paths = app.openapi()["paths"]
    private_operations = REQUIRED_PHASE1_OPERATIONS - {
        ("post", "/api/v1/auth/register"),
        ("post", "/api/v1/auth/login"),
        ("post", "/api/v1/auth/refresh"),
    }

    missing_security = sorted(
        f"{method.upper()} {path}"
        for method, path in private_operations
        if not paths[path][method].get("security")
    )

    assert missing_security == []
