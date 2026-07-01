# AI Job Discovery Platform
## Production Grade Real-Time Job Collection & ML Dataset Pipeline

# ROLE

You are acting as a team of:

- Senior Data Engineer
- Senior Backend Engineer
- AI/ML Engineer
- Data Scientist
- Web Automation Engineer
- System Architect
- Python Expert
- DevOps Engineer

Your goal is to build a production-quality job ingestion and AI filtering pipeline.

DO NOT build a demo.

DO NOT build a toy project.

Build it exactly like it would be built inside a real startup.

Everything must be modular, scalable, reusable and production ready.

Think deeply before implementing every module.

Always prioritize architecture over shortcuts.

------------------------------------------------------------

# PROJECT OBJECTIVE

The objective is to build a complete Job Discovery Pipeline.

The system should continuously collect jobs from multiple public sources, clean them, normalize them, classify them and finally produce an AI/ML focused dataset.

Pipeline:

Job Sources

↓

Collection Layer

↓

Parsing Layer

↓

Cleaning Layer

↓

Normalization Layer

↓

Duplicate Detection

↓

Rule Based Filtering

↓

AI Classification

↓

Relevance Scoring

↓

Final AIML Dataset

↓

Database

↓

Analytics Dashboard

------------------------------------------------------------

# IMPORTANT REQUIREMENTS

The project must support thousands to millions of jobs.

Everything should be modular.

Every source must be independent.

If tomorrow another source is added,
the remaining system should not change.

Follow SOLID principles.

Use clean architecture.

No spaghetti code.

------------------------------------------------------------

# TECHNOLOGY STACK

Python 3.12+

FastAPI

Playwright

BeautifulSoup4

lxml

httpx

requests

asyncio

SQLAlchemy

Pydantic

Pandas

Polars

RapidFuzz

Sentence Transformers

Scikit Learn

DuckDB

PostgreSQL

Redis

Docker

Docker Compose

Git

Pre Commit

Black

isort

ruff

pytest

Poetry

uv

or any modern dependency manager.

------------------------------------------------------------

# ENVIRONMENT SETUP

Create

.env.example

requirements.txt

pyproject.toml

Dockerfile

docker-compose.yml

README.md

.gitignore

.pre-commit-config.yaml

Everything should be ready to run.

------------------------------------------------------------

# INSTALL EVERYTHING

Automatically install every dependency.

Check versions.

Handle compatibility.

Generate commands.

Example

python -m venv venv

activate environment

install dependencies

verify installation

------------------------------------------------------------

# PROJECT STRUCTURE

Use clean architecture.

Example

app/

config/

collectors/

linkedin/

indeed/

greenhouse/

lever/

ashby/

company_sites/

parser/

cleaner/

normalizer/

rule_engine/

classifier/

relevance/

database/

models/

schemas/

services/

utils/

tests/

docs/

scripts/

logs/

exports/

dashboard/

------------------------------------------------------------

# DATA SOURCES

Support multiple sources.

Examples

Greenhouse

Lever

Ashby

Company Career Pages

Public APIs

Public RSS Feeds

Government Job APIs

LinkedIn connector module (configurable)

Indeed connector module (configurable)

Naukri connector module

Do NOT hardcode anything.

Each source should implement the same interface.

Example

collect()

parse()

normalize()

return standardized schema

------------------------------------------------------------

# SCRAPER ARCHITECTURE

Every collector must contain

Fetcher

Retry logic

Rate limiter

HTML parser

Structured extractor

Logger

Error handler

Validation

Data formatter

All collectors should return exactly the same output schema.

------------------------------------------------------------

# DATABASE SCHEMA

Create raw_jobs table

Create cleaned_jobs table

Create rejected_jobs table

Create ai_classified_jobs table

Create relevance_jobs table

Create logs table

Everything normalized.

------------------------------------------------------------

# STANDARD JOB SCHEMA

job_id

source

source_url

company

title

description

salary

location

employment_type

experience

skills

benefits

posted_date

scraped_date

language

raw_html

raw_json

clean_description

normalized_title

rule_score

ai_label

confidence

relevance_score

status

------------------------------------------------------------

# CLEANING PIPELINE

Remove

HTML

duplicate spaces

unicode issues

emoji

tracking URLs

duplicate descriptions

duplicate jobs

normalize whitespace

normalize punctuation

preserve original data

never lose raw information

------------------------------------------------------------

# NORMALIZATION

Normalize titles

Examples

Machine Learning Engineer

Machine-Learning Engineer

ML Engineer

↓

ml_engineer

Artificial Intelligence Engineer

↓

ai_engineer

Large Language Model Engineer

↓

llm_engineer

Create canonical mappings.

------------------------------------------------------------

# DEDUPLICATION

Use multiple signals.

Job Title Similarity

Company Similarity

Description Similarity

URL Similarity

Location Similarity

Hash Matching

RapidFuzz

Semantic Similarity

Only remove if confidence is high.

------------------------------------------------------------

# RULE ENGINE

Before AI

Run cheap filters.

Positive keywords

Python

TensorFlow

PyTorch

NLP

LLM

RAG

LangChain

CUDA

Computer Vision

AI Engineer

Machine Learning

MLOps

Data Science

Statistics

SQL

AWS

Negative keywords

Sales

Marketing

Recruiter

Graphic Designer

Finance

Content Creator

HR

Operations

Customer Support

Trainer

Use weighted scoring.

Everything configurable.

------------------------------------------------------------

# AI CLASSIFICATION

Run only on shortlisted jobs.

Use provider abstraction.

Support

Gemini

Groq

OpenRouter

Together AI

DeepSeek

Sarvam

OpenAI

Provider should be replaceable.

No vendor lock-in.

Return

Role

Confidence

Reason

Evidence

Accept Reject

------------------------------------------------------------

# RELEVANCE SCORING

Calculate score using

title

skills

description

experience

tool match

candidate profile

keyword overlap

semantic similarity

Rank

0-30 reject

31-50 weak

51-70 moderate

71-85 good

86-100 excellent

------------------------------------------------------------

# LOGGING

Everything logged.

Errors

Warnings

Source failures

Retries

Skipped jobs

Rejected jobs

Duplicates

Execution time

------------------------------------------------------------

# PERFORMANCE

Everything async wherever possible.

Batch processing.

Connection pooling.

Caching.

Retry logic.

Avoid duplicate requests.

------------------------------------------------------------

# CONFIGURATION

No hardcoded values.

Everything configurable.

Keywords

Thresholds

Sources

Schedules

Database

AI providers

All via YAML or .env

------------------------------------------------------------

# TESTING

Unit tests

Integration tests

Schema validation

Duplicate detection tests

Cleaning tests

Parser tests

Rule engine tests

------------------------------------------------------------

# EXPORTS

Generate

CSV

JSON

JSONL

SQLite

Postgres

Parquet

DuckDB

------------------------------------------------------------

# ANALYTICS

Generate

Top Skills

Top Companies

Top Locations

Top Roles

Role Distribution

Skill Distribution

Rejected Reasons

Duplicates

Source Statistics

------------------------------------------------------------

# DOCUMENTATION

Generate professional documentation.

Architecture

Flow diagrams

Folder explanation

API documentation

Database schema

Configuration guide

Deployment guide

Developer guide

------------------------------------------------------------

# FUTURE READY

Design for

millions of jobs

distributed scraping

message queues

Kafka

RabbitMQ

Celery

Airflow

vector database integration

resume matching

ATS matching

recommendation engine

semantic search

LLM powered ranking

------------------------------------------------------------

# FINAL DELIVERABLES

Produce

✅ Complete production-ready source code

✅ Documentation

✅ Docker setup

✅ Database schema

✅ Tests

✅ Example data

✅ API endpoints

✅ README

✅ Architecture diagrams

✅ Folder explanation

✅ Requirements documentation

Everything should be polished.

No placeholders.

No TODOs.

No incomplete functions.

No pseudo code.

Every module should compile and run.

Think like an engineer building an internal platform for a startup.

Quality is far more important than speed.hestrator in `pipeline_service.py` can be refactored into **Celery** tasks. Celery task workers can pull scraped URLs from a Redis broker, enabling massive horizontal scaling.
- **Data Orchestrator**: The pipeline can be scheduled, managed, and monitored using **Apache Airflow** or **Prefect** DAGs.
---

# 📂 Project Structure

The project follows a modular architecture where every folder has a single responsibility. This makes the codebase easier to understand, test, and scale as new features are added.

```
jobintel/
│
├── app/
│   ├── api/
│   ├── collectors/
│   ├── parser/
│   ├── cleaner/
│   ├── normalizer/
│   ├── rule_engine/
│   ├── classifier/
│   ├── scorer/
│   ├── analytics/
│   ├── exporters/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── config/
│
├── dashboard/
│
├── tests/
│
├── docs/
│
├── logs/
│
├── exports/
│
├── docker/
│
├── scripts/
│
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

# 📁 Folder Explanation

## 📡 collectors/

Responsible for collecting raw jobs from different sources.

Each source has its own independent connector.

Example:

```
collectors/

linkedin/

indeed/

greenhouse/

lever/

ashby/
```

Adding a new source only requires creating another collector without changing the rest of the system.

---

## 📄 parser/

Converts raw HTML pages into structured Python objects.

Example:

HTML

↓

Title

Company

Description

Salary

Location

↓

JSON Object

---

## 🧹 cleaner/

Removes unwanted noise from collected jobs.

Examples:

- HTML tags
- Duplicate spaces
- Invalid characters
- Broken formatting
- Tracking URLs
- Emojis

The goal is to keep meaningful information while preserving the original raw data.

---

## 🏷️ normalizer/

Different companies use different names for the same role.

Examples:

```
Machine Learning Engineer

↓

ml_engineer

--------------------

Machine-Learning Engineer

↓

ml_engineer

--------------------

ML Engineer

↓

ml_engineer
```

Normalization makes searching, filtering and analytics much more accurate.

---

## 🔍 rule_engine/

Runs before the AI layer.

Uses configurable keyword rules to quickly remove obviously irrelevant jobs.

This reduces:

- API costs
- Processing time
- Token usage

Only promising jobs move to the AI stage.

---

## 🤖 classifier/

Uses LLMs to understand the meaning of each job.

Supported providers include:

- Gemini
- Groq
- OpenRouter
- Together AI
- DeepSeek
- OpenAI

Instead of simply looking for keywords, the classifier understands context.

Example:

```
Title:

AI Content Creator

↓

Category:

Content Creation

↓

Rejected
```

Whereas

```
Applied AI Engineer

↓

AI Engineer

↓

Accepted
```

---

## 📈 scorer/

Calculates how well a job matches a target AI/ML profile.

Scoring considers:

- Required skills
- Experience
- Job description
- Technologies
- Semantic similarity

The final score helps rank jobs from most relevant to least relevant.

---

## 🗄️ database/

Handles all interactions with PostgreSQL.

Tables include:

- Raw Jobs
- Clean Jobs
- Rejected Jobs
- Classified Jobs
- Relevance Scores
- Logs

Keeping separate tables improves traceability and makes debugging easier.

---

## 📊 analytics/

Generates useful insights from collected data.

Examples:

- Top Companies
- Most Common Skills
- Most Popular Locations
- Hiring Trends
- AI Role Distribution
- Duplicate Statistics

---

## 📤 exporters/

Exports processed datasets into multiple formats.

Supported formats:

- CSV
- JSON
- JSONL
- Parquet
- DuckDB
- PostgreSQL

---

## 🧪 tests/

Contains unit and integration tests.

Every important module should have automated tests.

Examples:

- Parser Tests
- Cleaning Tests
- Duplicate Detection Tests
- AI Classification Tests
- Database Tests

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/jobintel.git

cd jobintel
```

---

## 2. Create Virtual Environment

Windows

```bash
python -m venv .venv

.venv\Scripts\activate
```

Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

or

```bash
poetry install
```

---

## 4. Configure Environment Variables

Create a new file

```
.env
```

Example

```env
DATABASE_URL=

REDIS_URL=

GEMINI_API_KEY=

OPENAI_API_KEY=

GROQ_API_KEY=

LOG_LEVEL=INFO

SCRAPE_INTERVAL=3600
```

Never commit API keys to GitHub.

---

# 🐳 Docker Setup

Build

```bash
docker compose build
```

Run

```bash
docker compose up
```

Stop

```bash
docker compose down
```

Using Docker ensures the project runs consistently across different operating systems without manual dependency management.

---

# 🚀 Running the Project

Start the API

```bash
uvicorn app.main:app --reload
```

The API will be available at

```
http://localhost:8000
```

Swagger Documentation

```
http://localhost:8000/docs
```

ReDoc Documentation

```
http://localhost:8000/redoc
```

---

# 🗄️ Database Design

Instead of storing everything in a single table, JobIntel separates different stages of the pipeline.

```
Raw Jobs

↓

Clean Jobs

↓

Rejected Jobs

↓

AI Classified Jobs

↓

Final Ranked Jobs
```

This allows:

- Better debugging
- Easier analytics
- Reprocessing without re-scraping
- Historical tracking

---

# 📊 Data Flow

```
Collect Jobs

↓

Parse HTML

↓

Clean Data

↓

Normalize Titles

↓

Detect Duplicates

↓

Rule Engine

↓

AI Classification

↓

Relevance Scoring

↓

Database

↓

Analytics

↓

Export Dataset
```

Every stage has one responsibility.

This makes the system easier to maintain and scale.

---

# 🧠 AI Workflow

Unlike traditional scrapers, AI is not used immediately.

Instead:

```
Raw Jobs

↓

Rule Engine

↓

AI Model

↓

Confidence Score

↓

Accepted Jobs
```

This saves API costs while maintaining high classification accuracy.

---

# 🔄 Why Rule-Based Filtering Before AI?

Suppose we scrape

100,000 jobs.

Instead of sending all 100,000 jobs to an LLM, we first remove obvious non-AI roles using lightweight rules.

Example:

Marketing Manager

↓

Rejected immediately

Machine Learning Engineer

↓

Forwarded to AI

This approach significantly reduces inference cost and improves system performance.

---

# 📊 Analytics Dashboard

JobIntel doesn't just collect job postings—it transforms raw data into actionable insights.

The analytics layer helps answer questions such as:

- 📈 Which AI roles are currently in highest demand?
- 🏢 Which companies are hiring the most?
- 🌍 Which locations have the highest number of openings?
- 💰 What salary ranges are most common?
- 🧠 Which technical skills appear most frequently?
- 📅 Hiring trends over time
- 🚀 Which job sources provide the highest quality listings?
- ❌ Why are certain jobs rejected?

### Example Dashboard

```
+--------------------------------------------------------------+

                    JOBINTEL DASHBOARD

--------------------------------------------------------------

Jobs Collected Today             18,432

AI/ML Jobs Detected               4,761

Rejected Jobs                    11,598

Duplicate Jobs                      921

Average Relevance Score             82.6

Most Requested Skill             Python

Top Hiring Company               Microsoft

Top Location                     Bengaluru

--------------------------------------------------------------
```

---

# 🔌 API Endpoints

The platform exposes REST APIs through FastAPI.

## Collect Jobs

```http
POST /api/v1/jobs/collect
```

Starts the job collection pipeline.

---

## Clean Dataset

```http
POST /api/v1/jobs/clean
```

Runs cleaning and normalization.

---

## Classify Jobs

```http
POST /api/v1/jobs/classify
```

Runs the AI classification stage.

---

## Calculate Relevance

```http
POST /api/v1/jobs/score
```

Calculates job relevance.

---

## Export Dataset

```http
GET /api/v1/export/json
```

```http
GET /api/v1/export/csv
```

```http
GET /api/v1/export/parquet
```

---

## Analytics

```http
GET /api/v1/analytics
```

Returns dashboard statistics.

---

# 📈 Example Dataset

```json
{
  "job_id": "947352",
  "company": "Google",
  "title": "Machine Learning Engineer",
  "normalized_title": "ml_engineer",
  "location": "Bangalore",
  "skills": [
    "Python",
    "TensorFlow",
    "LLMs",
    "SQL"
  ],
  "rule_score": 94,
  "ai_label": "ML Engineer",
  "confidence": 97,
  "relevance_score": 91
}
```

---

# 🧠 AI Classification Flow

```
Job Description

↓

Rule Engine

↓

AI Provider

↓

Role Classification

↓

Confidence Score

↓

Relevance Scoring

↓

Database
```

Only high-quality jobs are forwarded to the AI stage.

This approach improves both speed and cost efficiency.

---

# ⚡ Performance Optimizations

JobIntel has been designed with scalability in mind.

Key optimizations include:

- Async requests using `asyncio`
- Parallel scraping
- Request retry mechanism
- Connection pooling
- Database indexing
- Redis caching
- Batch processing
- Configurable worker count
- Automatic duplicate detection
- Efficient similarity matching

These optimizations help the platform process large datasets more efficiently.

---

# 📚 Technologies Used

| Category | Technologies |
|----------|--------------|
| Backend | FastAPI |
| Language | Python |
| Parsing | BeautifulSoup, lxml |
| Browser Automation | Playwright |
| Database | PostgreSQL, DuckDB |
| AI | Gemini, Groq, OpenRouter, DeepSeek |
| ML | Sentence Transformers, Scikit-Learn |
| Similarity | RapidFuzz |
| Data Processing | Pandas, Polars |
| Containerization | Docker |
| Testing | Pytest |
| Version Control | Git |

---

# 🔮 Future Roadmap

This project is designed to grow over time.

Upcoming ideas include:

- ✅ Resume Matching
- ✅ ATS Resume Optimization
- ✅ Semantic Job Search
- ✅ Vector Database Integration
- ✅ AI-Powered Interview Preparation
- ✅ Skill Gap Analysis
- ✅ Company Intelligence
- ✅ Salary Prediction
- ✅ Job Recommendation Engine
- ✅ Personalized Alerts
- ✅ Real-Time Notifications
- ✅ Trend Forecasting
- ✅ LLM Agent Pipeline
- ✅ Graph Database Support
- ✅ Distributed Job Collection

---

# 🤝 Contributing

Contributions are welcome.

If you'd like to improve the project:

1. Fork the repository

2. Create a feature branch

```bash
git checkout -b feature/amazing-feature
```

3. Commit your changes

```bash
git commit -m "Added new feature"
```

4. Push

```bash
git push origin feature/amazing-feature
```

5. Open a Pull Request

Please make sure your code follows the existing project structure and passes all tests before submitting.

---

# 🧪 Running Tests

```bash
pytest
```

Run with coverage

```bash
pytest --cov=app
```

---

# ❓ Frequently Asked Questions

## Why not use AI for every job?

Because AI inference is relatively expensive.

A lightweight rule engine removes obvious irrelevant jobs first, so only high-quality candidates are sent to the AI model.

---

## Why normalize job titles?

Different companies use different names for the same role.

Normalization ensures they can all be treated consistently.

---

## Why store raw jobs?

Keeping the original data allows us to:

- Reprocess jobs with improved logic
- Debug issues
- Train future models
- Compare cleaning strategies

---

## Why multiple data sources?

Depending on a single source is risky.

Supporting multiple sources improves reliability and coverage.

---

# 🏆 Project Highlights

✔ Production-inspired architecture

✔ Modular design

✔ AI-powered role classification

✔ Multi-source collection

✔ Duplicate detection

✔ Data normalization

✔ Scalable pipeline

✔ REST API

✔ Docker support

✔ Analytics dashboard

✔ Machine-learning-ready datasets

✔ Future-ready architecture

---

# 📜 License

This project is licensed under the MIT License.

Feel free to use, modify, and extend it for learning, research, and production projects.

---

# 🙏 Acknowledgements

Special thanks to the open-source community and the developers behind:

- FastAPI
- Playwright
- BeautifulSoup
- PostgreSQL
- Docker
- Sentence Transformers
- RapidFuzz
- Hugging Face
- OpenRouter
- Gemini
- Groq

Their tools and libraries make projects like this possible.

---

<div align="center">

## ⭐ If you found this project useful, consider giving it a Star!

### Built with ❤️ using Python, AI and Modern Data Engineering.

*"Turning millions of scattered job postings into structured intelligence."*

</div>
- **Vector Database**: Cleaned and approved descriptions can be embedded using Sentence-Transformers and saved to vector stores (e.g. **Chroma**, **Qdrant**, **pgvector**) to enable semantic resume matching and ATS recommendations.
