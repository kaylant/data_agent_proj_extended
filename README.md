# Data Analysis Agent (Extended)

A production-ready GUI application for analyzing pipeline data using LangGraph and Anthropic/OpenAI LLMs.

## Features

- **React frontend** with Tailwind CSS
- **FastAPI backend** with LangGraph agent
- **Docker support** for easy deployment
- **Multi-turn conversations** with memory
- **12 analysis tools** including clustering, data quality checks, and robustness validation

## Quick Start

### Prerequisites
- Docker and Docker Compose

### Run with Docker (Recommended)

1. Clone the repo:
```bash
git clone https://github.com/yourusername/data-agent-extended.git
cd data-agent-extended
```

2. Create `.env` file:
```env
ANTHROPIC_API_KEY=your-key-here
```

3. Add dataset:
```bash
mkdir -p data
# Place pipeline_dataset.parquet in ./data/
```

4. Run:
```bash
docker-compose up --build
```

5. Open `http://localhost:3000`

### Development Mode

For hot-reloading during development:
```bash
docker-compose -f docker-compose.dev.yml up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/schema` | GET | Dataset schema and info |
| `/chat` | POST | Send a message to the agent |
| `/clear/{thread_id}` | POST | Clear conversation history |

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
│   │   └── ...
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

## Testing
```bash
uv run pytest -v
```