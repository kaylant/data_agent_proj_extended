# Data Analysis Agent (Extended)

A production-ready GUI application for analyzing pipeline data using LangGraph and Anthropic/OpenAI LLMs, featuring Auth0 SSO authentication, streaming responses, and PostgreSQL database support.

## Features

- **React frontend** with Tailwind CSS
- **FastAPI backend** with LangGraph agent
- **Auth0 SSO** authentication
- **Streaming responses** for real-time feedback
- **PostgreSQL database** support (local Docker or AWS RDS)
- **Docker support** for easy deployment
- **Multi-turn conversations** with memory
- **13 analysis tools** including SQL queries, clustering, data quality checks, and robustness validation

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Auth0 account (free tier works)

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/data-agent-extended.git
cd data-agent-extended
```

### 2. Set up Auth0

1. Create an account at https://auth0.com
2. Create a new **Single Page Application**:
   - Go to Applications → Create Application
   - Name: "Data Analysis Agent"
   - Type: Single Page Application
3. Configure the application settings:
   - Allowed Callback URLs: `http://localhost:5173, http://localhost:3000`
   - Allowed Logout URLs: `http://localhost:5173, http://localhost:3000`
   - Allowed Web Origins: `http://localhost:5173, http://localhost:3000`
4. Create an **API**:
   - Go to Applications → APIs → Create API
   - Name: "Data Analysis Agent API"
   - Identifier: `https://data-agent-api`
5. Authorize the application:
   - Go to APIs → Data Analysis Agent API → Application Access
   - Set "Data Analysis Agent" User Access to **Authorized**

### 3. Configure environment variables

Create `.env` in project root:
```env
ANTHROPIC_API_KEY=your-anthropic-key

# Auth0
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://data-agent-api

# Database (optional - defaults to local Docker)
# DATABASE_URL=postgresql://agent:agent_password@localhost:5432/pipeline_data
# USE_DATABASE=false
```

Create `frontend/.env`:
```env
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your-client-id
VITE_AUTH0_AUDIENCE=https://data-agent-api
```

### 4. Add dataset
```bash
mkdir -p data
# Place pipeline_dataset.parquet in ./data/
```

### 5. Run with Docker

**Production:**
```bash
docker-compose up --build
```

Open `http://localhost:3000`

**Development (with hot reload):**
```bash
docker-compose -f docker-compose.dev.yml up --build
```

Open `http://localhost:5173`

## Data Storage Modes

The application supports two data storage modes:

### File Mode (Default)
- Loads parquet file into memory at startup
- Fast queries (data in RAM)
- Best for: single-user, datasets that fit in memory
- No additional setup required
```bash
uv run uvicorn api:app --reload
```

### Database Mode
- Stores data in PostgreSQL
- Queries execute via SQL
- Best for: multi-user, larger datasets, production deployments
- Requires PostgreSQL (local Docker or AWS RDS)
```bash
# Start local PostgreSQL
docker-compose up db -d

# Load data into database
uv run python -c "
from src.database import init_database, load_parquet_to_db
init_database()
load_parquet_to_db('data/pipeline_dataset.parquet', use_copy=True)
"

# Run with database mode
USE_DATABASE=true uv run uvicorn api:app --reload
```

### AWS RDS Support

The application is configured to work with AWS RDS PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@your-instance.rds.amazonaws.com:5432/postgres
USE_DATABASE=true
```

**Note:** For optimal performance with 16M+ rows, use at least `db.t3.medium` instance. Free tier (`db.t3.micro`) will be slow for complex queries.

## Local Development (Without Docker)

### Backend
```bash
uv sync
uv run uvicorn api:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/schema` | GET | Yes | Dataset schema and info |
| `/chat` | POST | Yes | Send a message (non-streaming) |
| `/chat/stream` | POST | Yes | Send a message (streaming SSE) |
| `/clear/{thread_id}` | POST | Yes | Clear conversation history |

## Project Structure
```
data-agent-extended/
├── src/
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── _shared.py
│   │   ├── pandas_tool.py
│   │   ├── sql_tool.py
│   │   ├── stats.py
│   │   ├── outliers.py
│   │   ├── time_series.py
│   │   ├── patterns.py
│   │   ├── clustering.py
│   │   ├── data_quality.py
│   │   └── validation.py
│   ├── agent.py
│   ├── database.py
│   ├── data_loader.py
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── nginx.conf
│   └── package.json
├── tests/
├── api.py
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── pyproject.toml
└── README.md
```

## Available Tools

| Tool | Description |
|------|-------------|
| `execute_pandas_code` | Run arbitrary pandas code |
| `execute_sql_query` | Run SQL queries (database mode) |
| `get_column_stats` | Column statistics |
| `find_correlations` | Correlation analysis |
| `detect_outliers` | Outlier detection (IQR/z-score) |
| `analyze_time_series` | Time series trends |
| `find_patterns` | Group-by aggregations |
| `cluster_analysis` | K-means clustering |
| `find_segments` | Segment entities by metric |
| `data_quality_report` | Data quality assessment |
| `compare_with_without_issues` | Impact of data issues |
| `check_confounders` | Confounder analysis |
| `robustness_check` | Validate findings |

## Example Queries

- "How many unique pipelines are there?"
- "Find correlations between capacity columns"
- "Are there outliers in total_scheduled_quantity?"
- "Run a data quality report"
- "Find segments of pipelines by total_scheduled_quantity"
- "Run robustness checks on top pipelines"
- "Check if the relationship between design_capacity and total_scheduled_quantity is confounded by region"

## Testing
```bash
uv run pytest -v
```

## Production Considerations

This application is designed with production deployment in mind. Here are the recommended AWS services and configurations:

### Secrets Management

Use AWS Secrets Manager for sensitive configuration:
```python
# Example: Fetching secrets in production
import boto3
import json

def get_secrets():
    client = boto3.client('secretsmanager', region_name='us-east-2')
    response = client.get_secret_value(SecretId='data-agent/prod')
    return json.loads(response['SecretString'])

# Secrets to store:
# - ANTHROPIC_API_KEY
# - AUTH0_CLIENT_SECRET
# - DATABASE_URL
```

### Logging & Monitoring

CloudWatch integration for observability:
```python
# Example: Structured logging for CloudWatch
import logging
import json

class CloudWatchFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "trace_id": getattr(record, 'trace_id', None),
        })

# Key metrics to track:
# - Query latency (p50, p95, p99)
# - Tool usage by type
# - Error rates by endpoint
# - Token usage per request
```

### Recommended CloudWatch Alarms

| Metric | Threshold | Action |
|--------|-----------|--------|
| API 5xx errors | > 5/min | Alert |
| Query latency p95 | > 30s | Alert |
| Memory utilization | > 80% | Scale up |
| Database connections | > 80% pool | Alert |

### Infrastructure as Code

For production deployment, use Terraform or AWS CDK:
```hcl
# Example Terraform resources
- aws_ecs_cluster
- aws_ecs_service (Fargate)
- aws_lb (Application Load Balancer)
- aws_rds_cluster (PostgreSQL)
- aws_secretsmanager_secret
- aws_cloudwatch_log_group
- aws_cloudwatch_metric_alarm
```

### Scaling Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| Backend API | ECS auto-scaling on CPU/memory |
| Database | RDS read replicas or Aurora Serverless |
| Frontend | S3 + CloudFront (infinitely scalable) |
| LLM calls | Queue with SQS for rate limiting |

## Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│   React     │────▶│   Auth0     │
│             │◀────│   Frontend  │◀────│   SSO       │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           │ JWT Token + SSE Stream
                           ▼
                    ┌─────────────┐
                    │   FastAPI   │
                    │   Backend   │
                    └─────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │  Parquet    │          │ PostgreSQL  │
       │  (File Mode)│          │ (DB Mode)   │
       └─────────────┘          └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  LangGraph  │
                    │   Agent     │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Tools     │
                    │ (SQL/Pandas)│
                    └─────────────┘
```

## Deployment

### AWS (Recommended)

For production deployment on AWS:

1. **ECR** - Store Docker images
2. **ECS Fargate** - Run containers
3. **ALB** - Load balancer with HTTPS
4. **RDS PostgreSQL** - Database (db.t3.medium or larger)
5. **S3** - Store dataset files (optional)
6. **Secrets Manager** - Store API keys
7. **CloudWatch** - Logging and monitoring

### Environment Variables for Production
```env
# Required
ANTHROPIC_API_KEY=your-key
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://data-agent-api

# Database
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/dbname
USE_DATABASE=true

# Optional
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=data-agent-prod
```