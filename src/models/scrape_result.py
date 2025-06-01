from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.models.database import Base


class ScrapeResult(Base):
    __tablename__ = "scrape_results"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("scrape_configs.id"), nullable=False)
    
    # Scraping results
    status = Column(String(50), nullable=False)  # success, failed, timeout, blocked
    raw_html = Column(Text)
    extracted_data = Column(JSON)
    error_message = Column(Text)
    
    # Gemini enrichment
    gemini_response = Column(JSON)
    gemini_cost = Column(Float)  # USD cost for this enrichment
    gemini_model_used = Column(String(100))
    
    # Metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
    
    # Relationship
    config = relationship("ScrapeConfig", backref="results")