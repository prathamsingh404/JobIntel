# 🚀 JobIntel

> A production-ready AI-powered job intelligence platform that collects jobs from multiple sources, cleans and standardizes them, identifies AI/ML-related roles, and ranks them based on relevance.

---

##  What is JobIntel?

JobIntel is a data pipeline designed to automate the process of collecting and processing job postings.

Instead of relying on manually downloaded datasets, JobIntel continuously gathers jobs from multiple sources, cleans the data, removes duplicates, identifies AI/ML-related roles, and creates a structured dataset that can be used for analytics, recommendation systems, or machine learning.

The goal is to build a scalable system that works with real-world job data rather than static datasets.

---

##  Features

- Collect jobs from multiple sources
- Clean and standardize raw job data
- Remove duplicate postings
- Normalize job titles
- AI-powered role classification
- Job relevance scoring
- Export datasets in multiple formats
- Analytics dashboard
- REST API using FastAPI
- Modular and scalable architecture

---

##  Pipeline

```

Job Sources
↓
Collection
↓
Parsing
↓
Cleaning
↓
Normalization
↓
Duplicate Detection
↓
Rule-Based Filtering
↓
AI Classification
↓
Relevance Scoring
↓
Database
↓
Analytics

```

---

## 📂 Project Structure

```

app/
├── collectors/
├── parser/
├── cleaner/
├── normalizer/
├── classifier/
├── scorer/
├── database/
├── api/
├── analytics/
└── utils/

```

Each module has a single responsibility, making the project easier to maintain and extend.

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| Backend | FastAPI |
| Language | Python |
| Parsing | BeautifulSoup, Playwright |
| AI | Gemini, OpenRouter, Groq |
| Database | PostgreSQL, DuckDB |
| Data Processing | Pandas, Polars |
| Similarity | RapidFuzz |
| ML | Sentence Transformers |
| Containerization | Docker |

---

## ⚙️ Getting Started

Clone the repository

```bash
git clone https://github.com/yourusername/jobintel.git

cd jobintel
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the API

```bash
uvicorn app.main:app --reload
```

---

## 📊 Example Output

```json
{
  "title": "Machine Learning Engineer",
  "company": "Google",
  "location": "Bangalore",
  "role": "ML Engineer",
  "confidence": 97,
  "relevance_score": 91
}
```

---

## 🧠 How it Works

The platform processes jobs in multiple stages.

1. Collect raw jobs from supported sources.
2. Parse webpages into structured data.
3. Clean and standardize the information.
4. Remove duplicate postings.
5. Filter out irrelevant jobs using rule-based logic.
6. Classify remaining jobs using AI.
7. Calculate a relevance score.
8. Store the results for search, analytics, and exports.

This approach improves accuracy while reducing AI inference costs.

---

## 📈 Future Improvements

Some features planned for future versions include:

- Resume matching
- Semantic job search
- Vector database support
- Job recommendation engine
- Skill gap analysis
- Company insights
- Real-time notifications

---

## 🤝 Contributing

Contributions are always welcome.

If you'd like to improve the project, feel free to open an issue or submit a pull request.

---

## 📜 License

This project is licensed under the MIT License.

---

## ⭐ Support

If you found this project useful, consider giving it a star ⭐.

It helps the project grow and motivates future development.
