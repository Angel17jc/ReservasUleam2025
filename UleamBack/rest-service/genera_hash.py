from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

password = 'admin123'
hash = pwd_context.hash(password)
print(hash)