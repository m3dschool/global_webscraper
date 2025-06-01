from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog
from src.core.config import settings

logger = structlog.get_logger()

# Prometheus metrics
scrape_jobs_total = Counter(
    'scrape_jobs_total',
    'Total number of scrape jobs',
    ['config_id', 'status']
)

scrape_duration_seconds = Histogram(
    'scrape_duration_seconds',
    'Time spent scraping pages',
    ['config_id']
)

gemini_requests_total = Counter(
    'gemini_requests_total',
    'Total number of Gemini API requests',
    ['model', 'status']
)

gemini_cost_total = Counter(
    'gemini_cost_total',
    'Total cost of Gemini API requests in USD',
    ['model']
)

gemini_duration_seconds = Histogram(
    'gemini_duration_seconds',
    'Time spent on Gemini API requests',
    ['model']
)

active_scrape_jobs = Gauge(
    'active_scrape_jobs',
    'Number of currently running scrape jobs'
)

captcha_encounters_total = Counter(
    'captcha_encounters_total',
    'Total number of CAPTCHA encounters',
    ['config_id', 'solved']
)

http_errors_total = Counter(
    'http_errors_total',
    'Total number of HTTP errors',
    ['config_id', 'status_code']
)

# Application-specific metrics
configs_total = Gauge(
    'configs_total',
    'Total number of scrape configurations',
    ['active']
)

last_successful_scrape = Gauge(
    'last_successful_scrape_timestamp',
    'Timestamp of last successful scrape',
    ['config_id']
)


class MetricsCollector:
    """Collects and exports application metrics"""
    
    @staticmethod
    def record_scrape_job(config_id: int, status: str, duration: float):
        """Record a completed scrape job"""
        scrape_jobs_total.labels(config_id=config_id, status=status).inc()
        scrape_duration_seconds.labels(config_id=config_id).observe(duration)
        
        if status == 'success':
            import time
            last_successful_scrape.labels(config_id=config_id).set(time.time())
    
    @staticmethod
    def record_gemini_request(model: str, status: str, duration: float, cost: float = 0):
        """Record a Gemini API request"""
        gemini_requests_total.labels(model=model, status=status).inc()
        gemini_duration_seconds.labels(model=model).observe(duration)
        
        if cost > 0:
            gemini_cost_total.labels(model=model).inc(cost)
    
    @staticmethod
    def record_captcha_encounter(config_id: int, solved: bool):
        """Record a CAPTCHA encounter"""
        captcha_encounters_total.labels(
            config_id=config_id,
            solved='true' if solved else 'false'
        ).inc()
    
    @staticmethod
    def record_http_error(config_id: int, status_code: int):
        """Record an HTTP error"""
        http_errors_total.labels(
            config_id=config_id,
            status_code=status_code
        ).inc()
    
    @staticmethod
    def update_active_jobs(count: int):
        """Update the number of active scrape jobs"""
        active_scrape_jobs.set(count)
    
    @staticmethod
    def update_config_counts(total: int, active: int):
        """Update configuration counts"""
        configs_total.labels(active='true').set(active)
        configs_total.labels(active='false').set(total - active)


def start_metrics_server():
    """Start the Prometheus metrics server"""
    try:
        start_http_server(settings.prometheus_port)
        logger.info("Metrics server started", port=settings.prometheus_port)
    except Exception as e:
        logger.error("Failed to start metrics server", error=str(e))