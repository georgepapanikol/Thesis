import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routers import esco, oja
import backend.config as config

app = FastAPI(title="Thesis", version="1.0")

app.include_router(esco.router, prefix="/api/esco", tags=["esco"])
app.include_router(oja.router, prefix="/api/oja", tags=["oja"])
app.mount("/static", StaticFiles(directory=str(config.frontend_dir)), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(str(config.frontend_dir / "index.html"))

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=config.server_ip, port=config.server_port, reload=False)


