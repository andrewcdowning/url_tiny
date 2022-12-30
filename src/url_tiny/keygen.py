
import secrets
import string

from sqlalchemy.orm import Session

from . import crud

def generate_key(length: int = 5):
    return "".join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(length))

def create_uniq_random_key(db: Session):
    key = generate_key()
    while crud.get_db_url_by_key(db, key):
        key = generate_key()
    return key 