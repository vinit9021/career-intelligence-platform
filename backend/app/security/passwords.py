from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

_PASSWORD_HASH = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _PASSWORD_HASH.hash(password)


def verify_and_update_password(
    password: str,
    password_hash: str,
) -> tuple[bool, str | None]:
    try:
        return _PASSWORD_HASH.verify_and_update(
            password,
            password_hash,
        )
    except UnknownHashError:
        return False, None
