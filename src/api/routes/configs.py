from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.models.database import get_db
from src.models.scrape_config import ScrapeConfig
from src.models.user import User
from src.api.auth import get_current_active_user
from src.api.schemas import (
    ScrapeConfig as ScrapeConfigSchema,
    ScrapeConfigCreate,
    ScrapeConfigUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[ScrapeConfigSchema])
def get_configs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    configs = db.query(ScrapeConfig).offset(skip).limit(limit).all()
    return configs


@router.get("/{config_id}", response_model=ScrapeConfigSchema)
def get_config(
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
    return config


@router.post("/", response_model=ScrapeConfigSchema)
def create_config(
    config: ScrapeConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Check if name already exists
    existing = db.query(ScrapeConfig).filter(ScrapeConfig.name == config.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Config with this name already exists"
        )
    
    db_config = ScrapeConfig(
        **config.model_dump(),
        created_by=current_user.username
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.put("/{config_id}", response_model=ScrapeConfigSchema)
def update_config(
    config_id: int,
    config_update: ScrapeConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    config = db.query(ScrapeConfig).filter(ScrapeConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scrape config not found"
        )
    
    # Check name uniqueness if name is being updated
    if config_update.name and config_update.name != config.name:
        existing = db.query(ScrapeConfig).filter(ScrapeConfig.name == config_update.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Config with this name already exists"
            )
    
    update_data = config_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}")
def delete_config(
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
    
    db.delete(config)
    db.commit()
    return {"message": "Config deleted successfully"}