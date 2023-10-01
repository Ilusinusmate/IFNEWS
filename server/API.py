from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware # Necessário importart "fastapi[all]"
import os
import uvicorn

# Tendo em vista que este código é público, a estrutura raiz não é algo que possa ser mostrado, portanto fica escondido em um arquivo .txt
hidden_path = '\\'.join(__file__.split("\\")[:-1])
file_path = os.path.join(hidden_path, "hidebackend.txt")
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        __directory__ = file.read()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Substitua pelo domínio real em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





@app.get("/articles/")
def listArticle():
    articles = list()
    try:
        for file in os.listdir(__directory__):
            file_path = os.path.join(__directory__, file)
            if os.path.isfile(file_path):
                articles.append(file)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

    result = {"articles": articles}

    return JSONResponse(content=result, status_code=200)

@app.get("/articles/{file_name}")
def downloadArticle(file_name):
    file_path = os.path.join(__directory__, file_name)

    if os.path.exists(file_path):
        file_type = file_name.split('.')[-1]
        return FileResponse(file_path, status_code=200, media_type=file_type, content_disposition_type='file')
    else:
        return HTTPException(status_code=404, detail=f"Specified file name '{file_name}' does not match a file in articles directory.")

@app.post("/articles/")
def uploadArticle(file_name: str = Form(...), text:str = Form(...)):

    if not file_name.endswith(".txt"):
        file_name += ".txt"

    file_path = os.path.join(__directory__, file_name)

    if os.path.exists(file_path):
        return HTTPException(status_code=401, detail=f"Specified file name '{file_name}' already exists to change it data improve your privilege, login.")

    with open(file_path, 'w') as file:
        file.write(text)

    return JSONResponse(content={"message": "File saved succesfuly!", file_name: text},  status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8000)
