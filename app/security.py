
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Gera o hash seguro da senha."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Confere se a senha corresponde ao hash armazenado."""
    return password_hash.verify(password, hashed_password)


# Hash válido para fazer verificação também quando o e-mail não existe.
# Evita que uma conta existente seja identificada por diferenças óbvias de tempo.
DUMMY_HASH = hash_password("senha-artificial-usada-apenas-para-verificacao")
