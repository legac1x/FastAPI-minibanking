from fastapi import FastAPI
import uvicorn

from app.api.endpoints.users import user_router

app = FastAPI()
app.include_router(user_router)

@app.get('/test')
async def home() -> dict:
    return {"message": "Welcome to my API!"}


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)