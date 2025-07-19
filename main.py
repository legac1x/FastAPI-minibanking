from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get('/test')
async def home() -> dict:
    return {"message": "Welcome to my API!"}


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=8000)