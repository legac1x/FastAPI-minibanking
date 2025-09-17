from fastapi import FastAPI, Depends
import uvicorn

from app.api.endpoints.users import user_router
from app.api.endpoints.banking import banking_router

app = FastAPI()
app.include_router(user_router)
app.include_router(banking_router)

@app.get('/test')
async def home() -> dict:
    return {"message": "Welcome to my API!"}

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)