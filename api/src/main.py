from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from match_settings_api import router   as match_settings_router
from match_api          import router   as match_router
from game_session_api   import router   as game_session_router
from join_game_session  import router   as student_join_router
from game_session_management_api import router as game_session_management_router
from student_results_api import router as student_results_router
from leaderboard_api import router as leaderboard_router
from authentication.routes.auth_routes import router as auth_router
from phase_one import router as phase_one_router
from phase_two import router as phase_two_router
from user_api import router as user_router
from badges_api import router as badges_router
from admin_api import router as admin_router
from authentication.config import validate_required_env_vars

app = FastAPI()

# Configure CORS first (applied first, so outer)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Add SessionMiddleware after CORS (applied last, so inner)
# In production, use a secure secret key from environment variables
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key"))

# Validate required environment variables at startup
@app.on_event("startup")
def validate_config():
    validate_required_env_vars()

app.include_router(match_settings_router)
app.include_router(match_router)
app.include_router(game_session_router)
app.include_router(student_join_router)
app.include_router(game_session_management_router)
app.include_router(student_results_router)
app.include_router(leaderboard_router)
app.include_router(auth_router)
app.include_router(phase_one_router)
app.include_router(phase_two_router)
app.include_router(user_router)
app.include_router(badges_router)
app.include_router(admin_router)

@app.get("/")
def read_root():
    db_url = os.getenv("DATABASE_URL", "DATABASE_URL not set")
    return {
        "message": "FastAPI server is running",
        "database_url_check": db_url
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}