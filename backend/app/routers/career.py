import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.career import (
    Certification,
    Contact,
    Interview,
    JobApplication,
)
from app.schemas.career import (
    APPLICATION_STATUSES,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    CertificationCreate,
    CertificationRead,
    CertificationUpdate,
    ContactCreate,
    ContactRead,
    ContactUpdate,
    InterviewCreate,
    InterviewRead,
    InterviewUpdate,
    Pipeline,
)
from app.services.crud import apply_update, get_or_404
from app.services.dates import now, today

router = APIRouter(
    prefix="/career",
    tags=["Career"]
)

ACTIVE_STATUSES = ("applied", "screen", "interview", "offer")


def _check_application(db: Session, application_id: int | None) -> None:
    if application_id is not None and db.get(JobApplication, application_id) is None:
        raise HTTPException(status_code=400, detail="Application not found")


# ---------------------------------------------------------
# APPLICATIONS
# ---------------------------------------------------------

@router.get("/applications")
def list_applications(
    status: Literal[
        "applied", "screen", "interview", "offer", "rejected", "withdrawn"
    ] | None = None,
    work_mode: Literal["remote", "hybrid", "onsite"] | None = None,
    db: Session = Depends(get_db),
):
    query = select(JobApplication)

    if status:
        query = query.where(JobApplication.status == status)
    if work_mode:
        query = query.where(JobApplication.work_mode == work_mode)

    applications = db.scalars(
        query.order_by(
            JobApplication.applied_date.desc(), JobApplication.id.desc()
        )
    ).all()
    return {"data": [ApplicationRead.model_validate(a) for a in applications]}


@router.post("/applications", status_code=201)
def create_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
):
    values = application.model_dump()
    values["applied_date"] = values["applied_date"] or today()

    item = JobApplication(**values)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Application added", "data": ApplicationRead.model_validate(item)}


@router.get("/applications/{application_id}")
def get_application(application_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, JobApplication, application_id, "Application")
    interviews = db.scalars(
        select(Interview)
        .where(Interview.application_id == application_id)
        .order_by(Interview.scheduled_at)
    ).all()
    return {
        "data": ApplicationRead.model_validate(item),
        "interviews": [InterviewRead.model_validate(i) for i in interviews],
    }


@router.patch("/applications/{application_id}")
def update_application(
    application_id: int,
    application: ApplicationUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, JobApplication, application_id, "Application")
    apply_update(item, application)

    if (
        item.salary_min is not None
        and item.salary_max is not None
        and item.salary_max < item.salary_min
    ):
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="salary_max must be >= salary_min"
        )

    db.commit()
    db.refresh(item)
    return {"message": "Application updated", "data": ApplicationRead.model_validate(item)}


@router.delete("/applications/{application_id}")
def delete_application(application_id: int, db: Session = Depends(get_db)):
    # Interviews are deleted with it; linked contacts are kept.
    item = get_or_404(db, JobApplication, application_id, "Application")
    db.delete(item)
    db.commit()
    return {"message": "Application deleted"}


# ---------------------------------------------------------
# INTERVIEWS
# ---------------------------------------------------------

def _interview_read(db: Session, item: Interview) -> InterviewRead:
    data = InterviewRead.model_validate(item)
    application = db.get(JobApplication, item.application_id)
    if application:
        data.company = application.company
        data.title = application.title
    return data


@router.get("/interviews")
def list_interviews(
    application_id: int | None = None,
    upcoming_only: bool = False,
    db: Session = Depends(get_db),
):
    query = select(Interview)

    if application_id is not None:
        query = query.where(Interview.application_id == application_id)
    if upcoming_only:
        query = query.where(Interview.scheduled_at >= now())

    interviews = db.scalars(query.order_by(Interview.scheduled_at)).all()
    return {"data": [_interview_read(db, i) for i in interviews]}


@router.post("/interviews", status_code=201)
def create_interview(interview: InterviewCreate, db: Session = Depends(get_db)):
    _check_application(db, interview.application_id)

    item = Interview(**interview.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Interview scheduled", "data": _interview_read(db, item)}


@router.patch("/interviews/{interview_id}")
def update_interview(
    interview_id: int,
    interview: InterviewUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Interview, interview_id, "Interview")
    apply_update(item, interview)
    db.commit()
    db.refresh(item)
    return {"message": "Interview updated", "data": _interview_read(db, item)}


@router.delete("/interviews/{interview_id}")
def delete_interview(interview_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Interview, interview_id, "Interview")
    db.delete(item)
    db.commit()
    return {"message": "Interview deleted"}


# ---------------------------------------------------------
# CONTACTS
# ---------------------------------------------------------

@router.get("/contacts")
def list_contacts(
    application_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Contact)
    if application_id is not None:
        query = query.where(Contact.application_id == application_id)

    contacts = db.scalars(query.order_by(Contact.name)).all()
    return {"data": [ContactRead.model_validate(c) for c in contacts]}


@router.post("/contacts", status_code=201)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    _check_application(db, contact.application_id)

    item = Contact(**contact.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Contact added", "data": ContactRead.model_validate(item)}


@router.patch("/contacts/{contact_id}")
def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Contact, contact_id, "Contact")
    _check_application(db, contact.application_id)
    apply_update(item, contact)
    db.commit()
    db.refresh(item)
    return {"message": "Contact updated", "data": ContactRead.model_validate(item)}


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Contact, contact_id, "Contact")
    db.delete(item)
    db.commit()
    return {"message": "Contact deleted"}


# ---------------------------------------------------------
# CERTIFICATIONS / STUDY GOALS
# ---------------------------------------------------------

@router.get("/certifications")
def list_certifications(db: Session = Depends(get_db)):
    certifications = db.scalars(
        select(Certification).order_by(
            Certification.target_date.asc().nulls_last(), Certification.id
        )
    ).all()
    return {"data": [CertificationRead.model_validate(c) for c in certifications]}


@router.post("/certifications", status_code=201)
def create_certification(
    certification: CertificationCreate,
    db: Session = Depends(get_db),
):
    item = Certification(**certification.model_dump())
    if item.status == "completed" and item.completed_date is None:
        item.completed_date = today()

    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Certification goal added", "data": CertificationRead.model_validate(item)}


@router.patch("/certifications/{certification_id}")
def update_certification(
    certification_id: int,
    certification: CertificationUpdate,
    db: Session = Depends(get_db),
):
    item = get_or_404(db, Certification, certification_id, "Certification")
    apply_update(item, certification)

    if item.status == "completed" and item.completed_date is None:
        item.completed_date = today()

    db.commit()
    db.refresh(item)
    return {"message": "Certification goal updated", "data": CertificationRead.model_validate(item)}


@router.delete("/certifications/{certification_id}")
def delete_certification(certification_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, Certification, certification_id, "Certification")
    db.delete(item)
    db.commit()
    return {"message": "Certification goal deleted"}


# ---------------------------------------------------------
# PIPELINE SUMMARY
# ---------------------------------------------------------

def pipeline_summary(db: Session, upcoming_days: int = 14) -> dict:
    rows = db.execute(
        select(JobApplication.status, func.count())
        .group_by(JobApplication.status)
    ).all()

    counts = {status: 0 for status in APPLICATION_STATUSES}
    for status, count in rows:
        counts[status] = count

    total = sum(counts.values())
    active = sum(counts[s] for s in ACTIVE_STATUSES)

    # Share of applications that got past "applied" (any reply at all).
    responded = total - counts["applied"] - counts["withdrawn"]
    response_rate = round(responded / total * 100, 1) if total else None

    start = now()
    end = start + datetime.timedelta(days=upcoming_days)
    interviews = db.scalars(
        select(Interview)
        .where(Interview.scheduled_at.between(start, end))
        .order_by(Interview.scheduled_at)
    ).all()

    return {
        "counts": counts,
        "total": total,
        "active": active,
        "response_rate": response_rate,
        "upcoming_interviews": [_interview_read(db, i) for i in interviews],
    }


@router.get("/pipeline", response_model=Pipeline)
def get_pipeline(
    upcoming_days: int = Query(default=14, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Application counts by status plus interviews coming up."""
    return pipeline_summary(db, upcoming_days)
