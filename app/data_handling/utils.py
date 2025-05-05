# app/utils/file_utils.py
import os
try:
    import magic
    MAGIC = magic.Magic(mime=True)
except Exception:           # libmagic missing
    MAGIC = None

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME = {
    "text/plain",
    "application/json",
    "text/csv",
    "application/vnd.ms-excel",   # excel-style csv
}

MIME_TO_EXT = {
    "text/plain": ".txt",
    "application/json": ".json",
    "text/csv": ".csv",
    "application/vnd.ms-excel": ".csv",
}


def sniff_mime(file) -> str | None:
    """Detect MIME type of a file-like object.
    Returns the MIME type as a string or None if detection fails.
    """
    if MAGIC:
        head = file.read(2048)
        file.seek(0)
        return MAGIC.from_buffer(head).split(";", 1)[0].lower()
    # fallback
    return (getattr(file, "content_type", "") or "").split(";", 1)[0].lower()


def validate_file(file):
    """True/False, message"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return False, "File size exceeds 50 MB limit"

    
    mime = sniff_mime(file)
    if mime not in ALLOWED_MIME:
        return False, f"File type “{mime or 'unknown'}” not allowed"

    return True, "File is valid"