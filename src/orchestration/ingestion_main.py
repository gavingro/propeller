import logging

import src.data.scraping as scraping
import src.data.database as database


def awws_metar_ingestion_pipeline():
    """
    Scrapes (Extracts) relevent data from Abbotsford and Vancouver
    AWWS METAR-TAF, Transforms them into usable (parsable) info,
    and writes (loads) to the project DynamoDB.
    """
    # Abbotsford Data
    abbotsford_page_source = scraping.scrape_awws_metar_pagesource("abbotsford")
    logging.info("Scraped Abbotsford Web Page Source.")
    abbotsford_page_data = scraping.parse_awws_pagesource(abbotsford_page_source)
    logging.info("Parsed Abbotsford Web Page Source.")

    # Vancouver Data
    vancouver_page_source = scraping.scrape_awws_metar_pagesource("vancouver")
    logging.info("Scraped Vancouver Web Page Source.")
    vancouver_page_data = scraping.parse_awws_pagesource(vancouver_page_source)
    logging.info("Parsed Vancouver Web Page Source.")

    # Writing to DB
    with database.dynamodb_connection() as db:
        logging.info("Beginning to write data documents to DynamoDB.")
        database.write_data_documents_to_awws_database(db, abbotsford_page_data)
        database.write_data_documents_to_awws_database(db, vancouver_page_data)
        logging.info("Finished writing data documents to DynamoDB.")


if __name__ == "__main__":
    awws_metar_ingestion_pipeline()
