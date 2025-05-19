from fastapi import FastAPI
from routers import audio_router

app = FastAPI()

app.include_router(audio_router.router)