from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from typing import Union, Optional, Tuple
from datetime import datetime, timedelta
import bcrypt
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
    
    user_id = Column(String, ForeignKey('users.email'), primary_key=True)
    token = Column(String, nullable= False)
    creation_date_time = Column(DateTime, default=datetime.utcnow)
      
    user = relationship("Users")


def is_registered(email: Optional[str], suap_registration_number: Optional[str] = None): # -> 200 (is registered) | 400 (not registered)
    currentSession = primarySession()

    try:
        if email is not None:
            response = currentSession.query(Users).filter_by(email=email).first()
        elif suap_registration_number:
            response = currentSession.query(Users).filter_by(suap_registration_number=suap_registration_number).first()
    except Exception as e:
        raise Exception(str(e))

    if response is not None:
        return {"message": f"User {email} is registered.", "status_code": 200, "is_registered": True}
    else:
        return {"message": f"User {email} is not registered", "status_code": 400, "is_registered": False}

def is_valid_token(token: str): # -> 200 (valid token) | 401 ( expired token  | not valid )
    currentSession = primarySession()

    response = currentSession.query(AuthenticationTokens).filter_by(token=token).first()
    currentSession.close()
    if not response:
        return {"message": "Token does not exists.", "status_code": 401, "is_valid": False}
    if datetime.utcnow() - response.creation_date_time > timedelta(hours=3):
        return {"message": "Token is expired, login again.", "status_code": 401, "is_valid": False}
    
    return {"message": "Token is valid", "status_code": 200, "is_valid": True}
  
def resgist_user(email:str, user_name:str, password_hash:str, suap_registration_number: Optional[str] = None): # -> 200 (registered) | 500 (internal error)
    currentSession = primarySession()

    try:
        user = Users(email=email, user_name=user_name, password_hash=password_hash, suap_registration_number=suap_registration_number)
        currentSession.add(user)
        currentSession.commit()
        currentSession.close()
        return {"message": "User registered succesfuly.", "status_code": 200}

    except Exception as e:
        currentSession.rollback()
        currentSession.close()
        return {"message": str(e), "status_code": 500}

def create_token(args: validations.LoginForm):

    """  LoginForm -> 200 (valid) | 401 (wrong password) | 404 (user not registered) """

    currentSession = primarySession()
    try:
        vld = is_registered(args.email if args.email is not None else args.suap_registration_number)
        if not vld["is_registered"]: return {"message": "User not registered.", "status_code": 404}

        response = currentSession.query(Users).filter_by(email=args.email).first()
        if not bcrypt.checkpw(args.password.encode("utf-8"), response.password_hash): return {"message": "Password does not match", "status_code": 401}

        vld = currentSession.query(AuthenticationTokens).filter_by(user_id=args.email).first()
        if vld is not None and is_valid_token(vld.token)["is_valid"]: return {"message": "Token still valid.", "status_code": 200, "token": vld.token} 

        token = str(uuid.uuid4())

        new_token = AuthenticationTokens(token=token, user_id=response.email)
        currentSession.add(new_token)
        currentSession.commit()
        currentSession.close()
        return {"message": "Token created", "status_code": 200, "token": token}

    except Exception as e:
        currentSession.rollback()
        currentSession.close()
        raise Exception(str(e))

def list_publications(category: Optional[str]) -> dict: # -> 200 (found) | 404 (not found) | 500 (internal error)
    currentSession = primarySession()
    try:
        if category is not None: 
            response = currentSession.query(Publication).filter_by(category=category).all()
        else:
            response = currentSession.query(Publication).all()
    except Exception as e:
        currentSession.close()
        return {"message": str(e), "status_code": 500}
    print(response, category)
    if response is not None:
        currentSession.close()
        return {"message": "Publications found successfuly", "status_code": 200, "articles": [element.title for element in response]}
    else:
        currentSession.close()
        return {"message": "Publications not found", "status_code": 404}

def get_publication(title: str): # title: str -> 200 (founded) | 404 (not founded)

    currentSession = primarySession()
    response = currentSession.query(Publication).filter_by(title=title).first()
    currentSession.close()

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

def create_publication(args: validations.Article, file_path: str): # -> 201 (created) | 401 (unauthoraized) | 500 (error)

    if not is_valid_token(args.token)["is_valid"]: return {"message": "Unanuthoraized acess, not valid token, to improve your privilege Log-in.", "status_code": 401}

    currentSession = primarySession()

    author = currentSession.query(AuthenticationTokens).filter_by(token=args.token).first()
    author = author.user_id
    author = currentSession.query(Users).filter_by(email=author).first()
    author = author.user_name
    
    try:
        publication = Publication(title=args.title, resume=args.resume, file_path=file_path, key_words=','.join(args.key_words), category=args.category, author=author)
        currentSession.add(publication)
        currentSession.commit()
        currentSession.close()
        return {"message": "Publication created succesfuly.", "status_code": 201}

    except Exception as e:
        currentSession.rollback()
        currentSession.close()
        return {"message": str(e), "status_code": 500}

def delete_publication(title: str, token: str): # title: str -> status code 204 (deleted)  | 500 (error)

    if not is_valid_token(token)["is_valid"]: return {"message": "Unanuthoraized acess, not valid token, to improve your privilege Log-in.", "status_code": 401}

    currentSession = primarySession()
    try:
        response = currentSession.query(Publication).filter_by(title=title).delete()
        currentSession.commit()
        currentSession.close()
        return {"message": "Publication deleted succesfuly.", "status_code": 204}
    except Exception as e:
        raise Exception(str(e))

Base.metadata.create_all(primaryEngine)