from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.scrape_config import ScrapeConfig
from src.models.user import User
from src.api.auth import get_current_active_user
from src.api.schemas import ScrapeJobTrigger
from src.scheduler.tasks import scrape_and_enrich

router = APIRouter()


@router.post("/trigger")
def trigger_scrape_job(
    job: ScrapeJobTrigger,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    config = db.query(ScrapeConfig).filter(ScrapeConfig.id == job.config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scrape config not found"
        )
    
    if not config.active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot trigger job for inactive config"
        )
    
    if job.run_immediately:
        # Use Celery to run the task
        task = scrape_and_enrich.delay(job.config_id)
        return {
            "message": f"Scrape job triggered for config {job.config_id}",
            "task_id": task.id
        }
    
    return {"message": f"Scrape job scheduled for config {job.config_id}"}


@router.get("/status/{config_id}")
def get_job_status(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    config = db.query(ScrapeConfig).filter(ScrapeConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scrape config not found"
        )
    
    # Get the most recent result for this config
    from src.models.scrape_result import ScrapeResult
    from sqlalchemy import desc
    
    latest_result = (
        db.query(ScrapeResult)
        .filter(ScrapeResult.config_id == config_id)
        .order_by(desc(ScrapeResult.started_at))
        .first()
    )
    
    return {
        "config_id": config_id,
        "config_name": config.name,
        "active": config.active,
        "latest_result": latest_result,
        "schedule": config.schedule_cron
    }


@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    """Get the status of a specific Celery task"""
    from src.scheduler.celery_app import celery_app
    
    task_result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result,
        "info": task_result.info
    }