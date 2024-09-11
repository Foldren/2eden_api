from os import environ
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

key = Fernet.generate_key()
print(key)
f = Fernet(environ["ADMIN_SECRET_KEY"])
hash_pasw = f.encrypt(b'c_aM8x3jGrJdBMOMHTc-xBp6hp0b-g')
print(hash_pasw)
