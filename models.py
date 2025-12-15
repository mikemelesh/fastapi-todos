from pydantic import BaseModel, Field
from database import Base
from sqlalchemy import Column, Integer, String, Boolean, desc

class TodoItemBase(BaseModel):
    title: str = Field(
        max_length=100
    )
    description: str | None = Field(

    )
    completed: bool = False

class TodoItem(TodoItemBase):
    id: int 

    class Config:

        from_attributes = True

class TodoTable(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
