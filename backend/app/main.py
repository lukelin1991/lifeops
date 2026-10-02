from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import check_auth_config, require_auth
from app.config import settings
from app.routers import (
    auth,
    calendar,
    career,
    dashboard,
    health,
    invest,
    money,
    system,
)

# Refuse to start with AUTH_ENABLED=true but no secret/password.
check_auth_config()


app = FastAPI(
    title="LifeOps API",
    description=(
        "Backend API for my personal "
        "LifeOps application"
    ),
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

origins = settings.cors_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

# Tables are created and changed by Alembic migrations now:
#   cd backend && alembic upgrade head
# (Base.metadata.create_all was removed on purpose.)


# ---------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------

# Public: health checks and login
app.include_router(system.router)
app.include_router(auth.router)

# Protected: everything else. require_auth is a no-op when
# AUTH_ENABLED=false, so local development works without logging in.
protected = [Depends(require_auth)]

app.include_router(health.router, dependencies=protected)
app.include_router(money.router, dependencies=protected)
app.include_router(calendar.router, dependencies=protected)
app.include_router(invest.router, dependencies=protected)
app.include_router(career.router, dependencies=protected)
app.include_router(dashboard.router, dependencies=protected)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "LifeOps API is running"
    }
