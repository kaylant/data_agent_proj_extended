# Data Analysis Agent (Extended)

A production-ready GUI application for analyzing pipeline data using LangGraph and Anthropic/OpenAI LLMs, featuring Auth0 SSO authentication and streaming responses.

## Features

- **React frontend** with Tailwind CSS
- **FastAPI backend** with LangGraph agent
- **Auth0 SSO** authentication
- **Streaming responses** for real-time feedback
- **Docker support** for easy deployment
- **Multi-turn conversations** with memory
- **12 analysis tools** including clustering, data quality checks, and robustness validation

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
│   │   ├── stats.py
│   │   ├── outliers.py
│   │   ├── time_series.py
│   │   ├── patterns.py
│   │   ├── clustering.py
│   │   ├── data_quality.py
│   │   └── validation.py
│   ├── agent.py
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
                           ▼
                    ┌─────────────┐
                    │  LangGraph  │
                    │   Agent     │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Pandas    │
                    │   Tools     │
                    └─────────────┘
```

## Deployment

### AWS (Recommended)

For production deployment on AWS:

1. **ECR** - Store Docker images
2. **ECS Fargate** - Run containers
3. **ALB** - Load balancer with HTTPS
4. **S3** - Store dataset files
5. **Secrets Manager** - Store API keys
6. **CloudWatch** - Logging and monitoring

### Environment Variables for Production
```env
# Required
ANTHROPIC_API_KEY=your-key
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://data-agent-api

# Optional
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=data-agent-prod
```