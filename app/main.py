import os
import random

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_sqlalchemy import DBSessionMiddleware, db
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext

from app.auth.jwt_token import create_access_token, decode_access_token
from app.models.db_models import Question, User
from app.models.schema import User as SchemaUser, Question as SchemaQuestion

load_dotenv(".env")

app = FastAPI()
app.add_middleware(DBSessionMiddleware, db_url=os.environ.get("DATABASE_URL"))
templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str, db):
    return (db.session.query(User)
            .filter(User.username == username).first())


def authenticate_user(db, username: str, password: str):
    user = get_user(username, db)
    if not user or not verify_password(password, user.password):
        return False
    return True


@app.post("/login")
async def login_for_access_token(db, form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password

    if not authenticate_user(db, username, password):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

    access_token = create_access_token(data={"sub": username}, expires_delta=1)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected_resource")
async def protected_resource(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(data=token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

    return {"message": "Access granted to protected resource"}


@app.get('/')
async def started_page(request: Request):
    context = {
        "message": "Welcome to the magic ball"
    }
    return templates.TemplateResponse("index.html", {"request": request, "context": context})


@router.post("/ask_question", response_model=SchemaQuestion)
async def ask_question(question: SchemaQuestion, request: Request):
    asked_question = db.session.query(Question).filter(user=request.user,
                                                       text=question.text).first()
    if not asked_question:
        asked_question.text = question.text
        asked_question.amount = 1
        asked_question.user = request.user
        db.session.add(asked_question)
        db.session.commit()
        context = {
            "question": asked_question,
        }
        return templates.TemplateResponse("ask_question.html", {"request": request, "context": context})

    asked_question.amount += 1
    db.session.add(asked_question)
    db.session.commit()
    context = {
        "question": asked_question,
    }
    return templates.TemplateResponse("ask_question.html", {"request": request, "context": context})


@router.get('/get_answer')
async def get_answer(request: Request):
    CHOICES = (
        "Да", "Нет", "Возможно", "Вопрос не ясен",
        "Абсолютно точно", "Никогда", "Даже не думай",
        "Сконцентрируйся и спроси опять"
    )

    choice = random.choice(CHOICES)
    context = {
        "answer": choice
    }
    return templates.TemplateResponse("answer.html", {"request": request, "context": context})
