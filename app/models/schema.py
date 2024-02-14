from pydantic import BaseModel


class User(BaseModel):
    username: str
    password: str

    class Config:
        orm_mode = True


class Question(BaseModel):
    text: str
    amount: int

    class Config:
        orm_mode = True
