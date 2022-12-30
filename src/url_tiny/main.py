
import validators
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.datastructures import URL

from url_tiny.config import get_settings

from .crud import create_db_url

from . import models, schemas
from .database import SessionLocal, engine
from url_tiny import crud

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request):
    message = f"URL '{request.url}' does not exist"
    raise HTTPException(status_code=404, detail=message)


@app.get("/")
def read_root():
    return "Welcome to the URL shortener API :)"


@app.get("/{url_key}")
def foraward_to_target_url(
    url_key: str,
    request: Request,
    db: Session = Depends(get_db)):
    #TODO Move to data port
    
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url = create_db_url(db=db, url=url)
    return get_admin_info(db_url)

@app.get(
    "/admin/{secret_key}",
    name="administration_information",
    response_model=schemas.URLInfo
    )
def get_url_info(secret_key: str, request: Request, db: Session = Depends(get_db)):
    if db_url := crud.get_db_url_by_secret_key(db=db, secret_key=secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request=request)


def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)
    admin_endpoint= app.url_path_for(
        "administration_information", secret_key=db_url.secret_key
    )
    db_url.url = str(base_url.replace(path=db_url.key))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url