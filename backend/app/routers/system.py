from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(
    tags=["System"]
)


@router.get("/healthz")
def healthz():
    """Liveness: the process is up. Never touches the database."""
    return {"status": "ok"}


@router.get("/readyz")
def readyz(db: Session = Depends(get_db)):
    """Readiness: the app can reach Postgres (SELECT 1)."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "unreachable"},
        )

    return {"status": "ok", "database": "ok"}
