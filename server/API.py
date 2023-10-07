from fastapi import FastAPI, Form, status
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware # Necessário importar "fastapi[all]"
from typing import Optional
import validations
import database
import bcrypt
import re
import os
import uvicorn


current_directory = os.path.dirname(os.path.abspath(__file__))
articles_directory = os.path.join(current_directory, "data", "articles")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Substituir pelo domínio real em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#LISTAR PUBLICAÇÕES
@app.get("/articles/search/{category}", status_code=200)
def list_articles(category: Optional[str]):
    if category in set(("{category}", "NULL", "none", "Null", "None")): category = None
    
    answer = database.list_publications(category=category)
    
    return Response(content=str(answer), status_code=answer["status_code"])

#VER PUBLICAÇÃO POR TITULO
@app.get("/articles/{title}", status_code=200)
def get_article(title: str):

    title = title.lower()
    temp = title[::]
    if not title.endswith(".txt"): temp += ".txt"

    file_path = os.path.join(articles_directory, temp)

    if os.path.exists(file_path):
        answer = database.get_publication(title=title)
        if answer["status_code"] != 404:

            with open(file_path, 'r') as file:
                answer["text"] = file.read()

            return answer
        
        raise HTTPException(status_code=404, detail=f"Specified file name '{title}' does not match a file in database")

    else:
        raise HTTPException(status_code=404, detail=f"Specified file name '{title}' does not match a file in articles directory.")

#CRIAR PUBLICAÇÃO
@app.post("/articles/", status_code=status.HTTP_201_CREATED)
def upload_article(args: validations.Article):

    #formatação
    args.title = args.title.lower()
    temp = args.title[::]
    if not args.title.endswith(".txt"): temp += ".txt"

    file_path = os.path.join(articles_directory, temp)

    if os.path.exists(file_path):
        raise HTTPException(status_code=400, detail=f"Specified title '{args.title}' already exists.")

    answer = database.create_publication(args, file_path)

    with open(file_path, 'w') as file:
        file.write(args.text)

    

    return Response(content=answer["message"], status_code=answer["status_code"])

#DELETAR PUBLICAÇÃO
@app.delete("/articles/{title}", status_code=204) # t
def delete_article(title):
    answer = database.get_publication(title=title)

    if answer["status_code"] == 404:
        raise HTTPException(status_code=404, detail=f"Does not exist any publication with {title} title.")

    if not title.endswith(".txt"): title += ".txt"
    os.remove(os.path.join(articles_directory, title)) 
    answer = database.delete_publication(title=title)
    return answer

#REGISTRAR USUÁRIO
@app.post("/auth/register", status_code=201)
def register(args: validations.RegisterForm):
    if not validations.is_valid_email(args.email):
        raise HTTPException(status_code=400, detail="Invalid email inserted.")   
    
    if not validations.is_valid_password(args.password):
        raise HTTPException(status_code=400, detail="The password must contain at least 1 upper leter, 1 lower leter, 1 number, 1 especial caractere and at least contain 8 caracteres.")
    
    if database.isRegistered(email=args.email):
        raise HTTPException(status_code=100, detail=f"This user is already registered. email: {email} Already in use.")
    
    password = args.password.encode("utf-8")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password, salt)

    status_code, message = database.registUser(user_name=args.user_name, email=args.email, password_hash=password_hash, suap_regist_number=args.suap_regist_number)
    
    return JSONResponse(status_code=status_code, content=message)
    

if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8000)
