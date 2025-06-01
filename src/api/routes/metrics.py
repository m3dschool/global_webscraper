from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.models.database import get_db
from src.models.scrape_config import ScrapeConfig
from src.models.scrape_result import ScrapeResult
from src.models.user import User
from src.api.auth import get_current_active_user
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get dashboard metrics for the admin console"""
    
    # Get configuration counts
    total_configs = db.query(ScrapeConfig).count()
    active_configs = db.query(ScrapeConfig).filter(ScrapeConfig.active == True).count()
    
    # Get total results
    total_results = db.query(ScrapeResult).count()
    
    # Get recent results (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_results = (
        db.query(ScrapeResult)
        .filter(ScrapeResult.started_at >= week_ago)
        .count()
    )
    
    # Calculate success rate (last 100 results)
    last_100_results = (
        db.query(ScrapeResult)
        .order_by(desc(ScrapeResult.started_at))
        .limit(100)
        .all()
    )
    
    if last_100_results:
        successful = sum(1 for r in last_100_results if r.status == 'success')
        success_rate = (successful / len(last_100_results)) * 100
    else:
        success_rate = 0
    
    # Get total Gemini cost (last 30 days)
    month_ago = datetime.utcnow() - timedelta(days=30)
    total_gemini_cost = (
        db.query(func.sum(ScrapeResult.gemini_cost))
        .filter(
            ScrapeResult.started_at >= month_ago,
            ScrapeResult.gemini_cost.isnot(None)
        )
        .scalar() or 0
    )
    
    # Get average scrape duration
    avg_duration = (
        db.query(func.avg(ScrapeResult.duration_seconds))
        .filter(
            ScrapeResult.duration_seconds.isnot(None),
            ScrapeResult.status == 'success'
        )
        .scalar() or 0
    )
    
    return {
        "configs": {
            "total": total_configs,
            "active": active_configs,
            "inactive": total_configs - active_configs
        },
        "results": {
            "total": total_results,
            "recent_week": recent_results,
            "success_rate": round(success_rate, 1)
        },
        "performance": {
            "avg_duration_seconds": round(float(avg_duration), 2),
            "total_gemini_cost_30d": round(float(total_gemini_cost), 4)
        }
    }


@router.get("/status-breakdown")
def get_status_breakdown(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get breakdown of result statuses over time"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    status_counts = (
        db.query(
            ScrapeResult.status,
            func.count(ScrapeResult.id).label('count')
        )
        .filter(ScrapeResult.started_at >= cutoff_date)
        .group_by(ScrapeResult.status)
        .all()
    )
    
    return {
        "period_days": days,
        "status_counts": [
            {"status": status, "count": count}
            for status, count in status_counts
        ]
    }


@router.get("/config-performance")
def get_config_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get performance metrics per configuration"""
    
    # Get performance stats per config
    config_stats = (
        db.query(
            ScrapeConfig.id,
            ScrapeConfig.name,
            func.count(ScrapeResult.id).label('total_runs'),
            func.sum(
                func.case([(ScrapeResult.status == 'success', 1)], else_=0)
            ).label('successful_runs'),
            func.avg(ScrapeResult.duration_seconds).label('avg_duration'),
            func.sum(ScrapeResult.gemini_cost).label('total_gemini_cost'),
            func.max(ScrapeResult.started_at).label('last_run')
        )
        .outerjoin(ScrapeResult, ScrapeConfig.id == ScrapeResult.config_id)
        .group_by(ScrapeConfig.id, ScrapeConfig.name)
        .all()
    )
    
    results = []
    for stat in config_stats:
        success_rate = 0
        if stat.total_runs and stat.total_runs > 0:
            success_rate = (stat.successful_runs / stat.total_runs) * 100
        
        results.append({
            "config_id": stat.id,
            "config_name": stat.name,
            "total_runs": stat.total_runs or 0,
            "successful_runs": stat.successful_runs or 0,
            "success_rate": round(success_rate, 1),
            "avg_duration": round(float(stat.avg_duration or 0), 2),
            "total_gemini_cost": round(float(stat.total_gemini_cost or 0), 4),
            "last_run": stat.last_run.isoformat() if stat.last_run else None
        })
    
    return {"configs": results}


@router.get("/recent-activity")
def get_recent_activity(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get recent scrape activity"""
    
    recent_results = (
        db.query(ScrapeResult)
        .join(ScrapeConfig, ScrapeResult.config_id == ScrapeConfig.id)
        .order_by(desc(ScrapeResult.started_at))
        .limit(limit)
        .all()
    )
    
    activity = []
    for result in recent_results:
        activity.append({
            "result_id": result.id,
            "config_id": result.config_id,
            "config_name": result.config.name,
            "status": result.status,
            "started_at": result.started_at.isoformat(),
            "duration_seconds": result.duration_seconds,
            "gemini_cost": result.gemini_cost,
            "extracted_count": len(result.extracted_data) if result.extracted_data else 0
        })
    
    return {"recent_activity": activity}