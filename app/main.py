from fastapi import FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from . import schemas, models, databases
from .routers import auth, posts, votes

models.Base.metadata.create_all(bind=databases.engine)

app = FastAPI(title="Social App",
              version="0.0.1",
              description="A sample social app",
              docs_url="/docs/",
              redoc_url="/redoc/")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# initial root
@app.get("/", name="root", tags=["root"])
def root():
    message = "Welcome to social app"
    response_model = schemas.CommonMessageResponse(message=message)
    return response_model


app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(votes.router)
