from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Import routers
from routes import auth, register, refresh, logout, employees, users

load_dotenv()

app = FastAPI()

# Include routers
app.include_router(auth.router)
app.include_router(register.router)
app.include_router(refresh.router)
app.include_router(logout.router)
app.include_router(employees.router, prefix="/employees", tags=["employees"])
app.include_router(users.router, prefix="/users", tags=["users"])

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
@app.get("/index", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def index():
    html_file_path = Path("static/html/index.html")
    if not html_file_path.exists():
        return HTMLResponse(content="<h1>Index file not found</h1>", status_code=404)
    with open(html_file_path, "r") as file:
        content = file.read()
    return HTMLResponse(content=content)


@app.api_route(
    "/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def catch_all(request: Request, full_path: str):
    # Build absolute path to 404.html
    html_404 = Path("static/html/404.html")
    if html_404.exists():
        return HTMLResponse(content=html_404.read_text(), status_code=404)
    return HTMLResponse(content="<h1>404 Not Found</h1>", status_code=404)
