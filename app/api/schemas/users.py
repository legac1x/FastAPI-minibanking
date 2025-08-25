from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class SignUp(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    email: str

class UserOut(BaseModel):
    first_name: str
    last_name: str
    username: str

class EmailVerificationRequest(BaseModel):
    email: str
    code: int