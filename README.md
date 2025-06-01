# Universal Web Scraper & Gemini Enrichment Platform

A config-driven, resilient web scraper with Google Gemini AI enrichment capabilities.

## Features

- **Config-driven scraping**: No code changes needed for new sites
- **Anti-detection**: Playwright with stealth techniques and proxy rotation
- **AI enrichment**: Google Gemini integration for data analysis
- **Scheduling**: Cron-based job scheduling with Celery
- **Admin console**: React-based dark-mode UI
- **Observability**: Prometheus metrics and structured logging
- **Resilient**: Retry logic, CAPTCHA handling, and error recovery

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd global_webscraper
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

3. Start the services:
```bash
docker-compose up -d
```

4. Access the admin console at http://localhost:3000

### Manual Setup

1. Install Python 3.12+ and Node.js 18+

2. Install Python dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Set up PostgreSQL and Redis

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the services:
```bash
# API Server
python main.py

# Celery Worker
celery -A src.scheduler.celery_app worker --loglevel=info

# Celery Beat (Scheduler)
celery -A src.scheduler.celery_app beat --loglevel=info

# Frontend
cd src/frontend
npm install
npm start
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/webscraper` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `MAX_CONCURRENT_SCRAPES` | Max concurrent scrape jobs | `5` |
| `PROXY_ENABLED` | Enable proxy rotation | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Scrape Configuration

Each scrape configuration includes:

- **Name**: Unique identifier
- **Start URL**: Target website URL
- **CSS Selector**: Element selector for data extraction
- **Schedule**: Cron expression for scheduling
- **Gemini Prompt**: AI enrichment instructions
- **Anti-detection settings**: Proxy, wait times, retries

## API Endpoints

### Authentication
- `POST /api/auth/token` - Login
- `POST /api/auth/register` - Register user

### Configurations
- `GET /api/configs` - List configurations
- `POST /api/configs` - Create configuration
- `PUT /api/configs/{id}` - Update configuration
- `DELETE /api/configs/{id}` - Delete configuration

### Jobs
- `POST /api/jobs/trigger` - Trigger manual scrape
- `GET /api/jobs/status/{config_id}` - Get job status
- `GET /api/jobs/task/{task_id}` - Get task status

### Results
- `GET /api/results` - List scrape results
- `GET /api/results/{id}` - Get result details
- `GET /api/results/{id}/raw-html` - Get raw HTML

### Metrics
- `GET /api/metrics/dashboard` - Dashboard metrics
- `GET /api/metrics/status-breakdown` - Status breakdown
- `GET /api/metrics/config-performance` - Per-config metrics

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Admin   │    │   FastAPI API   │    │ Celery Workers  │
│     Console     │◄──►│     Server      │◄──►│   (Scraping)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │      Redis      │
                       │    Database     │    │   (Message      │
                       │                 │    │    Queue)       │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Google Gemini  │
                       │   AI Service    │
                       └─────────────────┘
```

## Development

### Project Structure
```
src/
├── api/           # FastAPI routes and schemas
├── core/          # Configuration and utilities
├── models/        # Database models
├── scraper/       # Scraping engine and Gemini adapter
├── scheduler/     # Celery tasks and scheduling
└── frontend/      # React admin console

alembic/           # Database migrations
config/            # Configuration files
tests/             # Test files (TODO)
```

### Running Tests
```bash
pytest
```

### Code Quality
```bash
# Format code
black src/

# Lint code
ruff src/

# Type checking
mypy src/
```

## Monitoring

### Prometheus Metrics

The application exposes metrics at `/metrics`:

- `scrape_jobs_total` - Total scrape jobs by status
- `scrape_duration_seconds` - Scrape duration histogram
- `gemini_requests_total` - Gemini API requests
- `gemini_cost_total` - Gemini API costs
- `captcha_encounters_total` - CAPTCHA encounters
- `http_errors_total` - HTTP errors

### Grafana Dashboard

Import the provided Grafana dashboard for visualization.

## Security

- JWT-based authentication
- RBAC with admin and user roles
- Input validation and sanitization
- Rate limiting (TODO)
- Secrets management with environment variables

## Deployment

### Production Considerations

1. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
2. **Redis**: Use managed Redis (AWS ElastiCache, Google Memorystore)
3. **Secrets**: Use proper secret management (AWS Secrets Manager, HashiCorp Vault)
4. **Monitoring**: Set up alerts for scrape failures
5. **Scaling**: Use multiple Celery workers for high throughput
6. **Proxy Pool**: Integrate with proxy providers for large-scale scraping

### Docker Production

```bash
# Build and tag
docker build -t webscraper:latest .

# Run with production settings
docker run -d \
  -e DATABASE_URL=postgresql://... \
  -e GEMINI_API_KEY=... \
  -e SECRET_KEY=... \
  -p 8000:8000 \
  webscraper:latest
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation
- Review logs in structured JSON format