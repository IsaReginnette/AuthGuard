
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Gera o hash seguro da senha."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Confere se a senha corresponde ao hash armazenado."""
    return password_hash.verify(password, hashed_password)

