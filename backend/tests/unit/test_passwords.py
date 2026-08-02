from app.security.passwords import (
    hash_password,
    verify_and_update_password,
)


def test_password_is_hashed_and_verified() -> None:
    password = "StrongPassword9!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2")

    valid, updated_hash = verify_and_update_password(
        password,
        password_hash,
    )

    assert valid is True
    assert updated_hash is None


def test_wrong_or_unknown_hash_is_rejected() -> None:
    password_hash = hash_password("StrongPassword9!")

    valid, _ = verify_and_update_password(
        "WrongPassword9!",
        password_hash,
    )

    unknown_valid, unknown_update = verify_and_update_password(
        "StrongPassword9!",
        "not-a-valid-password-hash",
    )

    assert valid is False
    assert unknown_valid is False
    assert unknown_update is None
