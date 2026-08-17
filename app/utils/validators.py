import re
import os
from werkzeug.utils import secure_filename

def validate_pan_format(pan):
    """Verifies standard Indian PAN format."""
    if not pan:
        return False
    return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan.upper()))

def validate_aadhar_format(aadhar):
    """Verifies standard 12-digit Aadhar format."""
    if not aadhar:
        return False
    return bool(re.match(r'^[0-9]{12}$', aadhar))

def validate_file_security(file_storage, allowed_extensions, max_size_bytes):
    """
    Validates uploaded file extension, size limits, and sanitizes filenames.
    Returns (is_secure, secure_name_or_error_msg)
    """
    if not file_storage or file_storage.filename == '':
        return False, "No file uploaded."

    filename = secure_filename(file_storage.filename)
    ext = os.path.splitext(filename)[1].lower().replace('.', '')

    # 1. Verify Allowed Extensions
    if ext not in allowed_extensions:
        return False, f"Unsupported file type. Allowed formats: {', '.join(allowed_extensions)}"

    # 2. Verify File Size Limits
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    if size > max_size_bytes:
        return False, f"File size ({size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit ({max_size_bytes / (1024 * 1024):.2f} MB)."

    return True, filename
