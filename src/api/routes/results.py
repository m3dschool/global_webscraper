from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.models.database import get_db
from src.models.scrape_result import ScrapeResult
from src.models.user import User
from src.api.auth import get_current_active_user
from src.api.schemas import ScrapeResultsResponse

router = APIRouter()


@router.get("/", response_model=ScrapeResultsResponse)
def get_results(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    config_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = db.query(ScrapeResult)
    
    if config_id:
        query = query.filter(ScrapeResult.config_id == config_id)
    
    if status_filter:
        query = query.filter(ScrapeResult.status == status_filter)
    
    total = query.count()
    
    results = (
        query.order_by(desc(ScrapeResult.started_at))
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    
    return ScrapeResultsResponse(
        results=results,
        total=total,
        page=page,
        size=size
    )


@router.get("/{result_id}")
def get_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = db.query(ScrapeResult).filter(ScrapeResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scrape result not found"
        )
    return result


@router.get("/{result_id}/raw-html")
def get_result_raw_html(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = db.query(ScrapeResult).filter(ScrapeResult.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scrape result not found"
        )
    
    return {
        "result_id": result.id,
        "raw_html": result.raw_html,
        "url": result.config.start_url if result.config else None
    }