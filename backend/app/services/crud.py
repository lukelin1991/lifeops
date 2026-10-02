"""Small helpers shared by the module routers."""

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session


def get_or_404(db: Session, model, item_id: int, label: str):
    item = db.get(model, item_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail=f"{label} not found"
        )

    return item


def apply_update(item, update: BaseModel) -> None:
    """
    Copy the fields the client actually sent onto the ORM object.

    Sending null clears an optional column (e.g. notes), but is ignored
    for required columns so a stray null can't break the row.
    """
    columns = item.__table__.columns

    for name, value in update.model_dump(exclude_unset=True).items():
        if value is None and not columns[name].nullable:
            continue

        setattr(item, name, value)
