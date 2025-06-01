import asyncio
from datetime import datetime
from typing import Dict, Any
from celery import current_task
from sqlalchemy.orm import Session
from src.scheduler.celery_app import celery_app
from src.models.database import SessionLocal
from src.models.scrape_config import ScrapeConfig
from src.models.scrape_result import ScrapeResult
from src.scraper.engine import ScrapeEngine
from src.scraper.gemini_adapter import GeminiAdapter
from src.scheduler.cron_parser import should_run_now
import structlog

logger = structlog.get_logger()


def get_db_session() -> Session:
    """Get database session for tasks"""
    return SessionLocal()


@celery_app.task(bind=True)
def scrape_and_enrich(self, config_id: int) -> Dict[str, Any]:
    """Main task that scrapes a page and enriches it with Gemini"""
    
    task_id = self.request.id
    logger.info("Starting scrape task", task_id=task_id, config_id=config_id)
    
    db = get_db_session()
    try:
        # Get the configuration
        config = db.query(ScrapeConfig).filter(ScrapeConfig.id == config_id).first()
        if not config:
            raise ValueError(f"Scrape config {config_id} not found")
        
        if not config.active:
            raise ValueError(f"Scrape config {config_id} is not active")
        
        # Update task status
        current_task.update_state(
            state="PROGRESS",
            meta={"step": "scraping", "config_name": config.name}
        )
        
        # Run the scraping
        scrape_result = asyncio.run(_run_scrape(config))
        
        # Save scrape result to database
        db_result = ScrapeResult(
            config_id=config.id,
            status=scrape_result['status'],
            raw_html=scrape_result.get('raw_html'),
            extracted_data=scrape_result.get('extracted_data'),
            error_message=scrape_result.get('error_message'),
            started_at=scrape_result['started_at'],
            duration_seconds=scrape_result.get('duration_seconds')
        )
        
        # If scraping was successful, try Gemini enrichment
        if scrape_result['status'] == 'success' and scrape_result.get('extracted_data'):
            current_task.update_state(
                state="PROGRESS",
                meta={"step": "enriching", "config_name": config.name}
            )
            
            gemini_result = asyncio.run(_run_gemini_enrichment(
                scrape_result['extracted_data'],
                config.gemini_prompt,
                config.gemini_model
            ))
            
            # Update result with Gemini data
            db_result.gemini_response = gemini_result.get('enriched_data')
            db_result.gemini_cost = gemini_result.get('cost')
            db_result.gemini_model_used = gemini_result.get('model_used')
            
            if gemini_result.get('error'):
                logger.warning("Gemini enrichment failed", 
                             config_id=config_id, 
                             error=gemini_result['error'])
        
        # Mark completion time
        db_result.completed_at = datetime.utcnow()
        
        # Save to database
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        
        result = {
            "task_id": task_id,
            "config_id": config_id,
            "config_name": config.name,
            "result_id": db_result.id,
            "status": db_result.status,
            "extracted_count": len(scrape_result.get('extracted_data', [])),
            "gemini_cost": db_result.gemini_cost,
            "duration": db_result.duration_seconds
        }
        
        logger.info("Scrape task completed", **result)
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error("Scrape task failed", 
                    task_id=task_id, 
                    config_id=config_id, 
                    error=error_msg)
        
        # Save failed result
        db_result = ScrapeResult(
            config_id=config_id,
            status='failed',
            error_message=error_msg,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=0
        )
        db.add(db_result)
        db.commit()
        
        raise
    
    finally:
        db.close()


async def _run_scrape(config: ScrapeConfig) -> Dict[str, Any]:
    """Run the scraping process"""
    async with ScrapeEngine() as engine:
        return await engine.scrape_with_retries(config)


async def _run_gemini_enrichment(
    extracted_data: Dict[str, Any], 
    prompt: str, 
    model: str
) -> Dict[str, Any]:
    """Run Gemini enrichment"""
    adapter = GeminiAdapter()
    return await adapter.enrich_with_retry(extracted_data, prompt, model)


@celery_app.task
def check_scheduled_jobs():
    """Check for jobs that should be run based on their cron schedule"""
    
    db = get_db_session()
    try:
        # Get all active configurations
        configs = db.query(ScrapeConfig).filter(ScrapeConfig.active == True).all()
        
        scheduled_count = 0
        
        for config in configs:
            try:
                if should_run_now(config.schedule_cron):
                    # Check if we already have a recent run
                    from sqlalchemy import desc
                    recent_result = (
                        db.query(ScrapeResult)
                        .filter(ScrapeResult.config_id == config.id)
                        .order_by(desc(ScrapeResult.started_at))
                        .first()
                    )
                    
                    # Don't run if we've run in the last minute (to avoid duplicates)
                    if recent_result:
                        time_diff = datetime.utcnow() - recent_result.started_at
                        if time_diff.total_seconds() < 60:
                            continue
                    
                    # Schedule the task
                    scrape_and_enrich.delay(config.id)
                    scheduled_count += 1
                    
                    logger.info("Scheduled scrape job", 
                               config_id=config.id, 
                               config_name=config.name)
                    
            except Exception as e:
                logger.error("Failed to check schedule for config", 
                            config_id=config.id, 
                            error=str(e))
        
        if scheduled_count > 0:
            logger.info("Scheduled jobs", count=scheduled_count)
        
        return {"scheduled_jobs": scheduled_count}
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_results(days_to_keep: int = 30):
    """Clean up old scrape results to manage storage"""
    
    db = get_db_session()
    try:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete old results
        deleted_count = (
            db.query(ScrapeResult)
            .filter(ScrapeResult.started_at < cutoff_date)
            .delete()
        )
        
        db.commit()
        
        logger.info("Cleaned up old results", 
                   deleted_count=deleted_count, 
                   days_to_keep=days_to_keep)
        
        return {"deleted_results": deleted_count}
        
    finally:
        db.close()