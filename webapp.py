from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from dotenv import load_dotenv
from dotenv import load_dotenv
import os

load_dotenv()

WEB_PORT = int(os.getenv("WEB_PORT", 8001))

app = FastAPI()
security = HTTPBasic()

USERNAME = os.getenv("WEB_USERNAME", "admin")
PASSWORD = os.getenv("WEB_PASSWORD", "password")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})
    return True


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "API_TOKEN": os.getenv("API_TOKEN", "supersecrettoken"),
        "API_URL": os.getenv("API_URL"),
        "CAM_URL" : os.getenv("CAM_URL")
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("webapp:app", host="0.0.0.0", port=WEB_PORT, reload=False)
