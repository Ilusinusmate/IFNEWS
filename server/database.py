from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from typing import Union, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import validations
import secrets
import os
import json

#config
path = '\\'.join(__file__.split("\\")[:-1])
file_path = os.path.join(path, "database.db")
primaryEngine = create_engine("sqlite:///"+file_path)
Base = declarative_base()
primarySession = sessionmaker(bind=primaryEngine)

class Users(Base):
    __tablename__ = "users"

    email = Column(String(255), primary_key=True, nullable=False)
    user_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    suap_registration_number = Column(String(255), nullable=True)
    register_date = Column(DateTime, default=datetime.utcnow)

class Publication(Base):
    __tablename__ = "publication_logs"

    title = Column(String(255), primary_key=True, nullable=False)
    resume = Column(String(255), nullable=False)
    file_path = Column(String, nullable=False)
    key_words = Column(String, nullable=True)
    category = Column(String, nullable=True)
    author = Column(String, ForeignKey("users.user_name"), nullable=True)
    publishiment_date_time = Column(DateTime, default=datetime.utcnow)
    edited = Column(Boolean, default=False)
    user = relationship("Users")
    
class AuthenticationTokens(Base):
    __tablename__ = "autentication_tokens"
    
    token = Column(String, primary_key=True, default=secrets.token_urlsafe)
    creation_date_time = Column(DateTime, default=datetime.utcnow)
    userId = Column(String, ForeignKey('users.email'))  

    user = relationship("Users")


def is_registered(email: Optional[str], suapRegistrationNumber: Optional[str] = None): # Query args: str -> bool
    currentSession = primarySession()

    if email:
        response = currentSession.query(Users).filter_by(email=email).first()
    elif suapRegistrationNumber:
        response = currentSession.query(Users).filter_by(suapRegistrationNumber=suapRegistrationNumber).first()
    else:
        raise Exception("Needs at least one argument, or email or suapRegistrationNumber")

    return True if response else False

def is_valid_token(token: str):
    currentSession = primarySession()

    response = currentSession.query(AuthenticationTokens).filter_by(token=token).first()
    if not response:
        return False, {"message": "Token does not exists."}
    if datetime.utcnow() - response.creationDateTime < timedelta(hours=10):
        return False, {"message": "Token is expired, login again."}
    
    return True


    
def resgist_user(email:str, userName:str, passwordHash:str, suapRegistrationNumber: Optional[str] = None):
    currentSession = primarySession()

    try:
        user = Users(email=email, userName=userName, passwordHash=passwordHash, suapRegistrationNumber=suapRegistrationNumber)
        currentSession.add(user)
        currentSession.commit()
        return 200, {"message": "User registered succesfuly."}

    except Exception as e:
        currentSession.rollback()
        return 500, {"erro": str(e)}


def create_token():
    NotImplemented


def list_publications(category: Optional[str]) -> dict: 
    currentSession = primarySession()
    try:
        if category is not None: 
            response = currentSession.query(Publication).filter_by(category=category).all()
        else:
            response = currentSession.query(Publication).all()
    except Exception as e:
        return {"message": str(e), "status_code": 500}
    print(response, category)
    if response is not None:
        return {"message": "Publications found successfuly", "status_code": 200, "articles": [element.title for element in response]}
    else:
        return {"message": "Publications not found", "status_code": 404}

def get_publication(title: str):

    currentSession = primarySession()
    response = currentSession.query(Publication).filter_by(title=title).first()

    if response:
        return {
            "title": response.title,
            "resume": response.resume,
            "file_path" : response.file_path,
            "author" : response.author,
            "publishiment_date_time" : response.publishiment_date_time,
            "key_words" : response.key_words.split(","),
            "category" : response.category,
            "edited" : response.edited,
            "status_code" : 200,
            "message" : "Publication found successfuly!"
        }
    else:
        return {"message": "Publication not found", "status_code": 404}

def create_publication(args: validations.Article, file_path: str):
    currentSession = primarySession()

    try:
        publication = Publication(title=args.title, resume=args.resume, file_path=file_path, key_words=','.join(args.key_words), category=args.category)
        currentSession.add(publication)
        currentSession.commit()
        return {"message": "Publication created succesfuly.", "status_code": 201}

    except Exception as e:
        currentSession.rollback()
        return {"message": str(e), "status_code": 500}

def delete_publication(title: str): # title: str -> status code 204 (deleted)  | 500 (error)
    currentSession = primarySession()
    try:
        response = currentSession.query(Publication).filter_by(title=title).delete()
        currentSession.commit()
        return {"message": "Publication deleted succesfuly.", "status_code": 204}
    except Exception as e:
        return {"message": str(e), "status_code": 500}

Base.metadata.create_all(primaryEngine)