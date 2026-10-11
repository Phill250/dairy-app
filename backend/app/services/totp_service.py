import hashlib, json, secrets, time
import pyotp
from cryptography.fernet import Fernet
from app.core.config import settings

ISSUER = "Smart Dairy Manager"

def _fernet() -> Fernet:
    return Fernet(settings.totp_encryption_key.encode())

def new_secret() -> str:
    return pyotp.random_base32()

def encrypt(secret: str) -> str:
    return _fernet().encrypt(secret.encode()).decode()

def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()

def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)

def verify_code(user, code: str) -> bool:
    """True if the 6-digit code is valid and newer than any code already used."""
    code = (code or "").strip().replace(" ", "")
    if not (user.totp_secret_encrypted and code.isdigit() and len(code) == 6):
        return False
    totp = pyotp.TOTP(decrypt(user.totp_secret_encrypted))
    now_step = int(time.time()) // 30
    for step in (now_step - 1, now_step, now_step + 1):   # tolerate clock drift
        if step > (user.totp_last_step or 0) and secrets.compare_digest(totp.at(step * 30), code):
            user.totp_last_step = step
            return True
    return False

def _hash(code: str) -> str:
    return hashlib.sha256(code.strip().lower().encode()).hexdigest()

def generate_recovery_codes(user, n: int = 8) -> list[str]:
    codes = [secrets.token_hex(4) + "-" + secrets.token_hex(4) for _ in range(n)]
    user.recovery_code_hashes = json.dumps([_hash(c) for c in codes])
    return codes          # shown to the admin once, never stored in plain text

def consume_recovery_code(user, code: str) -> bool:
    hashes = json.loads(user.recovery_code_hashes or "[]")
    h = _hash(code)
    if h in hashes:
        hashes.remove(h)
        user.recovery_code_hashes = json.dumps(hashes)
        return True
    return False