import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.weight import WeightEntry as WeightModel
from app.models.weight_goal import WeightGoal
from app.schemas.health import (
    WeightCreate,
    WeightGoalCreate,
    WeightGoalUpdate,
    WeightUpdate,
)

router = APIRouter(
    tags=["Health"]
)

# ---------------------------------------------------------
# WEIGHT CRUD
# ---------------------------------------------------------

@router.post("/weights")
def create_weight(
    entry: WeightCreate,
    db: Session = Depends(get_db)
):
    weight_entry = WeightModel(
        weight=entry.weight,
        measurement_date=entry.measurement_date
    )

    db.add(weight_entry)
    db.commit()
    db.refresh(weight_entry)

    return {
        "message": "Weight recorded",
        "data": weight_entry
    }


@router.get("/weights")
def get_weights(
    db: Session = Depends(get_db)
):
    weights = (
        db.query(WeightModel)
        .order_by(
            WeightModel.measurement_date.asc(),
            WeightModel.created_at.asc(),
            WeightModel.id.asc()
        )
        .all()
    )

    return {
        "data": weights
    }


@router.patch("/weights/{weight_id}")
def update_weight(
    weight_id: int,
    entry: WeightUpdate,
    db: Session = Depends(get_db)
):
    weight_entry = db.get(
        WeightModel,
        weight_id
    )

    if weight_entry is None:
        raise HTTPException(
            status_code=404,
            detail="Weight entry not found"
        )

    if entry.weight is not None:
        weight_entry.weight = entry.weight

    if entry.measurement_date is not None:
        weight_entry.measurement_date = (
            entry.measurement_date
        )

    db.commit()
    db.refresh(weight_entry)

    return {
        "message": "Weight updated",
        "data": weight_entry
    }


@router.delete("/weights/{weight_id}")
def delete_weight(
    weight_id: int,
    db: Session = Depends(get_db)
):
    weight_entry = db.get(
        WeightModel,
        weight_id
    )

    if weight_entry is None:
        raise HTTPException(
            status_code=404,
            detail="Weight entry not found"
        )

    db.delete(weight_entry)
    db.commit()

    return {
        "message": "Weight entry deleted"
    }


# ---------------------------------------------------------
# WEIGHT GOALS CRUD
# ---------------------------------------------------------

@router.post("/weight-goals")
def create_weight_goal(
    goal: WeightGoalCreate,
    db: Session = Depends(get_db)
):
    if goal.goal_weight >= goal.starting_weight:
        raise HTTPException(
            status_code=400,
            detail=(
                "Goal weight must be lower than "
                "starting weight"
            )
        )

    weight_goal = WeightGoal(
        starting_weight=goal.starting_weight,
        goal_weight=goal.goal_weight,
        status="planned"
    )

    db.add(weight_goal)
    db.commit()
    db.refresh(weight_goal)

    return {
        "message": "Weight goal created",
        "data": weight_goal
    }


@router.get("/weight-goals")
def get_weight_goals(
    db: Session = Depends(get_db)
):
    goals = (
        db.query(WeightGoal)
        .order_by(
            WeightGoal.created_at.desc()
        )
        .all()
    )

    return {
        "data": goals
    }


@router.get("/weight-goals/active")
def get_active_weight_goal(
    db: Session = Depends(get_db)
):
    goal = (
        db.query(WeightGoal)
        .filter(
            WeightGoal.status == "active"
        )
        .first()
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="No active weight goal found"
        )

    return {
        "data": goal
    }


@router.get("/weight-goals/{goal_id}")
def get_weight_goal(
    goal_id: int,
    db: Session = Depends(get_db)
):
    goal = db.get(
        WeightGoal,
        goal_id
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Weight goal not found"
        )

    return {
        "data": goal
    }


@router.patch("/weight-goals/{goal_id}")
def update_weight_goal(
    goal_id: int,
    goal_update: WeightGoalUpdate,
    db: Session = Depends(get_db)
):
    goal = db.get(
        WeightGoal,
        goal_id
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Weight goal not found"
        )

    if goal.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Completed goals cannot be edited"
        )

    new_starting_weight = (
        goal_update.starting_weight
        if goal_update.starting_weight is not None
        else goal.starting_weight
    )

    new_goal_weight = (
        goal_update.goal_weight
        if goal_update.goal_weight is not None
        else goal.goal_weight
    )

    if new_goal_weight >= new_starting_weight:
        raise HTTPException(
            status_code=400,
            detail=(
                "Goal weight must be lower than "
                "starting weight"
            )
        )

    if goal_update.starting_weight is not None:
        goal.starting_weight = (
            goal_update.starting_weight
        )

    if goal_update.goal_weight is not None:
        goal.goal_weight = (
            goal_update.goal_weight
        )

    db.commit()
    db.refresh(goal)

    return {
        "message": "Weight goal updated",
        "data": goal
    }


@router.delete("/weight-goals/{goal_id}")
def delete_weight_goal(
    goal_id: int,
    db: Session = Depends(get_db)
):
    goal = db.get(
        WeightGoal,
        goal_id
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Weight goal not found"
        )

    db.delete(goal)
    db.commit()

    return {
        "message": "Weight goal deleted"
    }


# ---------------------------------------------------------
# ACTIVATE WEIGHT GOAL
# ---------------------------------------------------------

@router.post("/weight-goals/{goal_id}/activate")
def activate_weight_goal(
    goal_id: int,
    db: Session = Depends(get_db)
):
    goal = db.get(
        WeightGoal,
        goal_id
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Weight goal not found"
        )

    if goal.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Completed goals cannot be activated"
        )

    if goal.status == "active":
        raise HTTPException(
            status_code=400,
            detail="Weight goal is already active"
        )

    active_goal = (
        db.query(WeightGoal)
        .filter(
            WeightGoal.status == "active"
        )
        .first()
    )

    if active_goal:
        raise HTTPException(
            status_code=400,
            detail="Another weight goal is already active"
        )

    goal.status = "active"
    goal.activated_at = datetime.datetime.now()

    db.commit()
    db.refresh(goal)

    return {
        "message": "Weight goal activated",
        "data": goal
    }


# ---------------------------------------------------------
# COMPLETE WEIGHT GOAL
# ---------------------------------------------------------

@router.post("/weight-goals/{goal_id}/complete")
def complete_weight_goal(
    goal_id: int,
    db: Session = Depends(get_db)
):
    goal = db.get(
        WeightGoal,
        goal_id
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Weight goal not found"
        )

    if goal.status == "planned":
        raise HTTPException(
            status_code=400,
            detail=(
                "Goal must be activated before "
                "it can be completed"
            )
        )

    if goal.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="Weight goal is already completed"
        )

    latest_weight = (
        db.query(WeightModel)
        .order_by(
            WeightModel.measurement_date.desc(),
            WeightModel.created_at.desc(),
            WeightModel.id.desc()
        )
        .first()
    )

    if latest_weight is None:
        raise HTTPException(
            status_code=400,
            detail="No weight entries found"
        )

    if latest_weight.weight > goal.goal_weight:
        raise HTTPException(
            status_code=400,
            detail=(
                "Goal cannot be completed because "
                "the goal weight has not been reached"
            )
        )

    goal.status = "completed"
    goal.completed_at = datetime.datetime.now()

    db.commit()
    db.refresh(goal)

    return {
        "message": "Weight goal completed",
        "data": goal
    }


# ---------------------------------------------------------
# WEIGHT PROGRESS
# ---------------------------------------------------------

@router.get("/weight-progress")
def get_weight_progress(
    db: Session = Depends(get_db)
):
    goal = (
        db.query(WeightGoal)
        .filter(
            WeightGoal.status == "active"
        )
        .first()
    )

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="No active weight goal found"
        )

    latest_weight = (
        db.query(WeightModel)
        .order_by(
            WeightModel.measurement_date.desc(),
            WeightModel.created_at.desc(),
            WeightModel.id.desc()
        )
        .first()
    )

    if latest_weight is None:
        raise HTTPException(
            status_code=404,
            detail="No weight entries found"
        )

    total_to_lose = (
        goal.starting_weight
        - goal.goal_weight
    )

    change_from_start = (
        latest_weight.weight
        - goal.starting_weight
    )

    weight_remaining = (
        latest_weight.weight
        - goal.goal_weight
    )

    weight_lost = (
        goal.starting_weight
        - latest_weight.weight
    )

    raw_progress = (
        weight_lost
        / total_to_lose
    ) * 100

    progress_percentage = max(
        0,
        min(raw_progress, 100)
    )

    if latest_weight.weight <= goal.goal_weight:
        progress_status = "goal_reached"

    elif latest_weight.weight > goal.starting_weight:
        progress_status = "above_start"

    elif latest_weight.weight < goal.starting_weight:
        progress_status = "progress"

    else:
        progress_status = "starting"

    return {
        "goal_id": goal.id,
        "starting_weight": goal.starting_weight,
        "current_weight": latest_weight.weight,
        "goal_weight": goal.goal_weight,

        "change_from_start": round(
            change_from_start,
            1
        ),

        "weight_remaining": round(
            max(weight_remaining, 0),
            1
        ),

        "progress_percentage": round(
            progress_percentage,
            1
        ),

        "status": progress_status,

        "goal_activated_at": goal.activated_at,

        "latest_measurement_date": (
            latest_weight.measurement_date
        )
    }
