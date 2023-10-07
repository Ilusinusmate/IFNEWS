from pydantic import BaseModel
from typing import Optional, List

class RegisterForm(BaseModel):
    user_name: str
    email: str
    password: str
    suap_regist_number: Optional[str]

class Article(BaseModel):
    title: str
    resume: str
    text: str
    key_words: Optional[List[str]]
    category: Optional[str]
    token: Optional[str]

def is_valid_email(email):
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_pattern, email)

def is_valid_password(password):
    # Conter ao menos 1 letra maiúsula, 1 letra minúscula, 1 numero, 1 caractere especial.
    pattern = r'^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])(?=.*[@#$%^&+=])[\w\d@#$%^&+=]{8,}$'
    return re.search(pattern, password) and len(password) >= 8


