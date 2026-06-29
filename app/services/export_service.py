import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import polars as pl
import duckdb

from app.config.settings import BASE_DIR
from app.database.connection import AsyncSessionLocal
from app.database.repository import JobRepository
from app.utils.logger import logger

class ExportService:
    """Compiles and exports processed datasets into multiple production-grade formats."""

    def __init__(self):
        self.exports_dir = BASE_DIR / "exports"
        self.exports_dir.mkdir(exist_ok=True)

    async def export_all(self) -> Dict[str, str]:
        """Fetches the AI-classified, relevance-scored ML datasets and writes all formats."""
        logger.info("Starting dataset exports...")
        
        async with AsyncSessionLocal() as session:
            records = await JobRepository.get_all_relevant_records_for_export(session)

        if not records:
            logger.warning("No records found in database to export.")
            return {}

        paths = {}
        
        # 1. Export CSV
        csv_path = self.exports_dir / "ml_jobs_dataset.csv"
        df = pd.DataFrame(records)
        df.to_csv(csv_path, index=False, encoding="utf-8")
        paths["csv"] = str(csv_path)
        logger.info(f"Exported CSV: {csv_path}")

        # 2. Export JSON
        json_path = self.exports_dir / "ml_jobs_dataset.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        paths["json"] = str(json_path)
        logger.info(f"Exported JSON: {json_path}")

        # 3. Export JSONL
        jsonl_path = self.exports_dir / "ml_jobs_dataset.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        paths["jsonl"] = str(jsonl_path)
        logger.info(f"Exported JSONL: {jsonl_path}")

        # 4. Export Parquet (using Polars for performance)
        parquet_path = self.exports_dir / "ml_jobs_dataset.parquet"
        try:
            pl_df = pl.DataFrame(records)
            pl_df.write_parquet(parquet_path)
            paths["parquet"] = str(parquet_path)
            logger.info(f"Exported Parquet: {parquet_path}")
        except Exception as e:
            logger.error(f"Failed to export Parquet using Polars: {e}. Trying Pandas.")
            df.to_parquet(parquet_path, index=False)
            paths["parquet"] = str(parquet_path)

        # 5. Export SQLite database
        sqlite_path = self.exports_dir / "ml_jobs_dataset.sqlite"
        try:
            # Recreate/overwrite database
            if sqlite_path.exists():
                sqlite_path.unlink()
            conn = sqlite3.connect(sqlite_path)
            # Write dataframe to table
            df.to_sql("jobs", conn, index=False, if_exists="replace")
            conn.close()
            paths["sqlite"] = str(sqlite_path)
            logger.info(f"Exported SQLite DB: {sqlite_path}")
        except Exception as e:
            logger.error(f"Failed to export SQLite database: {e}")

        # 6. Export DuckDB database
        duckdb_path = self.exports_dir / "ml_jobs_dataset.duckdb"
        try:
            if duckdb_path.exists():
                duckdb_path.unlink()
            conn = duckdb.connect(str(duckdb_path))
            # Directly ingest from Pandas dataframe into duckdb table
            conn.execute("CREATE TABLE jobs AS SELECT * FROM df")
            conn.close()
            paths["duckdb"] = str(duckdb_path)
            logger.info(f"Exported DuckDB: {duckdb_path}")
        except Exception as e:
            logger.error(f"Failed to export DuckDB: {e}")

        return paths
