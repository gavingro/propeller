# Executes ingestion pipeline from ingestion.py at top level.
import logging

from src.orchestration import ingestion

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingestion.awws_metar_ingestion_pipeline()
