from passlib.context import CryptContext  # to encrypt the password which users enters

# passlib's default algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# To Hash the password
def hash_password(password: str):
    return pwd_context.hash(password)


# To verify and decrypt the password for login uses
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
