# AI Job Discovery Ingestion Platform & ML Dataset Pipeline

A production-grade, real-time job collection and filtering pipeline in Python 3.12+ for scraping, cleaning, normalizing, deduplicating, and classifying technical job listings. It generates a high-fidelity dataset for ML training and downstream matching engines.

---

## Pipeline Architecture

```
                 Job Ingestion Sources
         (Greenhouse, Lever, Ashby, RSS, Web)
                          │
                          ▼
             [ Collection / Fetcher Layer ]
                          │
                          ▼
             [ HTML / Text Cleaner Layer ]
                          │
                          ▼
           [ Normalizer & Canonical Mapping ]
                          │
                          ▼
           [ Deduplication (RapidFuzz + TF-IDF) ]
             ├── Yes ──► [ Rejected Database ]
             └── No
                          │
                          ▼
             [ Rule Engine (Keyword Weights) ]
             ├── Fail ──► [ Rejected Database ]
             └── Pass
                          │
                          ▼
             [ AI Role Classification (LLM) ]
             ├── Reject ──► [ Rejected Database ]
             └── Accept
                          │
                          ▼
            [ Candidate Profile Relevance Scorer ]
                          │
                          ▼
            [ Export Layer / ML Dataset Output ]
         (CSV, JSON, JSONL, Parquet, SQLite, DuckDB)
```

---

## Directory Structure

```
.
├── app/
│   ├── cleaner/
│   │   └── pipeline.py       # HTML stripper, Unicode & Emoji normalizer, Lang filter
│   ├── classifier/
│   │   ├── base.py           # Provider abstract interface
│   │   ├── factory.py        # Dynamic provider selection
│   │   ├── gemini_provider.py# Gemini API implementation (structured JSON output)
│   │   └── mock_provider.py  # Local fallback classifier for dry-runs
│   ├── collectors/
│   │   ├── base.py           # Abstract BaseCollector (retries, rate-limits)
│   │   ├── greenhouse.py     # Greenhouse API connector
│   │   ├── lever.py          # Lever postings API connector
│   │   ├── ashby.py          # Ashby board API connector
│   │   ├── linkedin.py       # LinkedIn public RSS XML parser
│   │   ├── indeed.py         # Indeed public RSS XML parser
│   │   ├── naukri.py         # Naukri configurable simulation collector
│   │   └── company_site.py   # General BS4 / Playwright dynamic web scraper
│   ├── config/
│   │   └── settings.py       # Pydantic Settings env/yaml merger
│   ├── database/
│   │   ├── connection.py     # SQLAlchemy Async engine, sessions (SQLite/Postgres)
│   │   └── repository.py     # CRUD operations & Analytics stats aggregator
│   ├── dashboard/
│   │   ├── app.py            # FastAPI app & REST routes
│   │   └── templates/
│   │       └── index.html    # Translucent glassmorphism web dashboard
│   ├── models/
│   │   ├── database.py       # SQLAlchemy ORM schemas (raw, cleaned, rejected, etc.)
│   │   └── schemas.py        # Pydantic schemas (DTO validation)
│   ├── relevance/
│   │   └── scorer.py         # Job-Candidate profile scoring & experience regex parser
│   ├── services/
│   │   ├── pipeline_service.py # Core flow orchestrator
│   │   └── export_service.py  # Datasets generator (Parquet, DuckDB, etc.)
│   └── utils/
│       └── logger.py         # Rotating structured file logger
├── exports/                  # Generated ML datasets target directory
├── logs/                     # Application logs target directory
├── tests/                    # Unit & Integration test suites
├── config.yaml               # Central settings (keywords, rules, profile mapping)
├── docker-compose.yml        # Orchestrates App container with Postgres 16
├── Dockerfile                # Multi-stage image build setup
├── pyproject.toml            # Poetry configurations and packaging metadata
├── requirements.txt          # Explicit pip requirements
└── run_pipeline.py           # CLI Entrypoint for pipeline runs & server start
```

---

## Local Setup & Installation

### Prerequisite
Python 3.12+ is required.

### 1. Create and Activate Virtual Environment
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Setup Configuration
Rename `.env.example` to `.env`:
```bash
cp .env.example .env
```
Inside `.env`, configure your active LLM provider. To utilize the live Gemini classification, fill in:
```env
DATABASE_URL=sqlite+aiosqlite:///jobs.db
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
```
*(If no API keys are set and `AI_PROVIDER=mock`, the system runs a local rules-based fallback classifier automatically so you can test it immediately offline).*

---

## Command Line Usage

Use the CLI interface `run_pipeline.py` to trigger operations:

### Trigger Ingestion Cycle & Export Datasets
Executes the scraper engines, processes jobs through all layers, writes records to the database, and compiles the ML output files inside `exports/`:
```bash
python run_pipeline.py run
```

### Compile Exports Only
Directly reads existing database records and regenerates export files:
```bash
python run_pipeline.py export
```

### Start the Analytics Dashboard Server
Launches the FastAPI backend and serves the interactive dashboard UI at `http://127.0.0.1:8000`:
```bash
python run_pipeline.py server
```

---

## Testing

Run the automated test suite verifying each individual processing step (Cleaning, Normalization, Deduplication, Keywords Filtering, and Database Persistence):
```bash
pytest -v
```

---

## Docker Deployment (PostgreSQL Integration)

To launch the application using Docker Compose with a PostgreSQL database:

```bash
docker-compose up --build
```
This boots:
1. `db`: PostgreSQL 16 image serving the database on port `5432`.
2. `app`: Ingestion service running Uvicorn server on port `8000`.

Open `http://localhost:8000` to access the live dashboard interface in Docker.

---

## Scale & Future Architectures

This architecture is designed to scale to millions of jobs by adopting standard distributed data engineering patterns:
- **Distributed Scraping**: Base collectors can be decoupled from the core application and scheduled as serverless functions or separate task modules.
- **Message Queues**: Ingestion outputs can be pushed to **Apache Kafka** or **RabbitMQ** to decouple the collection layer from parsing, cleaning, and classification...
- **Distributed Job Worker**: The orchestrator in `pipeline_service.py` can be refactored into **Celery** tasks. Celery task workers can pull scraped URLs from a Redis broker, enabling massive horizontal scaling.
- **Data Orchestrator**: The pipeline can be scheduled, managed, and monitored using **Apache Airflow** or **Prefect** DAGs.
- **Vector Database**: Cleaned and approved descriptions can be embedded using Sentence-Transformers and saved to vector stores (e.g. **Chroma**, **Qdrant**, **pgvector**) to enable semantic resume matching and ATS recommendations.
