from fastapi import FastAPI
from routers import user, product, authentication  # auth modülünü ekledik

app = FastAPI(
    title="OmniVen API",
    version="1.0.0",
    docs_url="/docs"
)

app.include_router(user.router)
app.include_router(product.router)
app.include_router(authentication.router)  # auth router'ı ekledik

@app.get("/")
def root():
    return {"message": "OmniVen API", "docs_url": "/docs", "version": "1.0.0"}