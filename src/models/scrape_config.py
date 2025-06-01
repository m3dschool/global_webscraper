from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from src.models.database import Base


class ScrapeConfig(Base):
    __tablename__ = "scrape_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    start_url = Column(Text, nullable=False)
    css_selector = Column(Text, nullable=False)
    region = Column(String(50), default="US")
    proxy_enabled = Column(Boolean, default=False)
    schedule_cron = Column(String(100), nullable=False)
    gemini_prompt = Column(Text, nullable=False)
    gemini_model = Column(String(100), default="gemini-pro")
    active = Column(Boolean, default=True)
    
    # Additional scraping options
    wait_time = Column(Integer, default=5)  # seconds to wait after page load
    max_retries = Column(Integer, default=3)
    timeout = Column(Integer, default=30)  # request timeout in seconds
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    
    # Extra configuration as JSON
    extra_config = Column(JSON, default=dict)