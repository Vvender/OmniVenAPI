from fastapi import FastAPI
from routers import user, authentication

app = FastAPI(
    title="OmniVen API",
    version="1.0.0",
    docs_url="/docs"
)
# Added routers
app.include_router(user.router)
app.include_router(authentication.router)

@app.get("/")
def root():
    return {
        "message": "OmniVen API",
        "docs_url": "/docs",
        "version": "1.0.0"
    }