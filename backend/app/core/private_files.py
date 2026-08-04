from typing import Literal
from urllib.parse import quote

ContentDisposition = Literal["attachment", "inline"]


def build_private_file_headers(
    *,
    filename: str,
    sha256: str,
    size_bytes: int,
    disposition: ContentDisposition = "attachment",
) -> dict[str, str]:
    normalized_filename = filename.strip() or "resume"
    normalized_checksum = sha256.strip().lower()

    if len(normalized_checksum) != 64 or any(
        character not in "0123456789abcdef" for character in normalized_checksum
    ):
        raise ValueError("SHA-256 checksum must contain exactly 64 hexadecimal characters.")

    if size_bytes < 0:
        raise ValueError("File size must not be negative.")

    encoded_filename = quote(normalized_filename, safe="")

    return {
        "Content-Disposition": (f"{disposition}; filename*=UTF-8''{encoded_filename}"),
        "Content-Length": str(size_bytes),
        "Cache-Control": "private, no-store",
        "Pragma": "no-cache",
        "X-Content-SHA256": normalized_checksum,
        "X-Content-Type-Options": "nosniff",
    }
