from sqlalchemy import Column, Integer, String, Float
from db.connection import Base

class Car(Base):
    __tablename__ = "cars"
    
    id = Column(Integer, primary_key=True, index=True) # stock_id
    make = Column(String, index=True)
    model = Column(String, index=True)
    year = Column(Integer)
    price = Column(Float)
    version = Column(String)
    km = Column(Integer)
    color = Column(String, nullable=True)
    transmission = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Car(id={self.id}, make='{self.make}', model='{self.model}', price={self.price})>"

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String) # "user" or "assistant"
    content = Column(String)
    timestamp = Column(String) # ISO format
