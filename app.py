from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Annotated

from sqlalchemy.orm.base import state_attribute_str
from sqlalchemy.sql.functions import user
from starlette.status import HTTP_201_CREATED

from models import TodoItem, TodoItemBase, TodoTable
from database import SessionLocal, engine, Base

from security_utils import (
    create_access_token,
    verify_password, 
    fake_users_db,
    get_current_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from security_models import Token, TokenData

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail = "Incorrect username or password"
        )

    if not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_dict["username"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/todos/", response_model=List[TodoItem])
def read_todos(
    db: Session = Depends(get_db),
    current_user: Annotated[TokenData, Depends(get_current_user)] = None
):
    todos = db.query(TodoTable).all()
    return todos

@app.post("/todos/", response_model=TodoItem)
def create_todo(
    item: TodoItemBase, 
    db: Session = Depends(get_db),
    current_user: Annotated[TokenData, Depends(get_current_user)] = None
):
    db_item = TodoTable(**item.model_dump())

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/todos/{todo_id}", response_model=TodoItem, status_code=status.HTTP_201_CREATED)
def update_todo(
    todo_id: int, 
    item: TodoItemBase, 
    db: Session = Depends(get_db),
    current_user: Annotated[TokenData, Depends(get_current_user)] = None
):

    db_item = db.query(TodoTable).filter(TodoTable.id == todo_id).first()

    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = f"Task with ID {todo_id} not found."
        )

    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)

    return db_item

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(
    todo_id: int, 
    db: Session = Depends(get_db),
    current_user: Annotated[TokenData, Depends(get_current_user)] = None
):

    db_item = db.query(TodoTable).filter(TodoTable.id == todo_id)

    if db_item.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = f"Task with ID {todo_id} not found."
        )

    db_item.delete()
    db.commit()

    return {"message": "Task succesfully deleted."}