import logging
import re
from typing import Literal

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import selenium.webdriver.chrome as chrome
from bs4 import BeautifulSoup

from src import config


def scrape_awws_metar_pagesource(
    location: Literal["vancouver", "abbotsford"] = "vancouver"
) -> str:
    """
    Connect to Aviation Weather Web Site to scrape the METAR - TAF forecasts
    for the given location.

    Parameters
    ----------
    location : str, optional
        The plain-language location for the airspace data you want to scrape.
        Currently 'vancouver' and 'abbotsford' are supported,
        by default 'vancouver'

    Returns
    -------
    str
        A string representing the entire HTML webpage containing the scraped data,
        to be parsed later using BeautifulSoup.
    """
    # Get URL from config.
    scraping_yaml_path = "config/scraping.yml"
    scraping_config = config.read_yaml_from(scraping_yaml_path)
    logging.debug(f"{scraping_config=}")
    awws_config = scraping_config["awws"]["metar-taf"]
    location_config = awws_config["locations"][location]
    location_code = location_config["code"]

    # Setup Selenium Chrome Driver
    chrome_options = chrome.options.Options()
    chrome_options.add_argument("--headless")
    chrome_service = chrome.service.Service(
        ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
    )
    driver = webdriver.Chrome(
        service=chrome_service,
        options=chrome_options,
    )

    # Navigate to report page.
    driver.get(awws_config["url"])
    manual_page_button = driver.find_element(
        By.LINK_TEXT, "Manual Entry / Change Region"
    )
    manual_page_button.click()
    logging.debug("Navigated to Code Manual Entry Page")
    plain_text_radio = driver.find_element(By.XPATH, "//input[@value='dcd']")
    plain_text_radio.click()
    id_lookup_entry = driver.find_element(By.NAME, "Stations")
    id_lookup_entry.clear()
    id_lookup_entry.send_keys(location_code)
    id_lookup_entry.send_keys(Keys.RETURN)
    logging.debug("Navigated to Plain-Text Weather Report")

    # Scrape Report Data Page Source
    return driver.page_source


def parse_awws_pagesource(
    source: str, awws_report: Literal["metar-taf"] = "metar-taf"
) -> dict:
    """
    Parses the page source of expected METAR web page for data.

    Data from page is organized into a dictionary and returned.

    Parameters
    ----------
    source : str
        HTML page source string of the AWWS METAR page,
        ideally generated with scrape_awws_metar_pagesource()
        function.

    awws_repot: Literal["metar-taf"]
        The type of AWWS report the page source is for.
        Currently only the METAR - TAF page is supported
        in the config files.
        "metar-taf" by default.

    Returns
    -------
    dict
        Organized dictionary of weather data from web page.
    """
    known_fields = config.read_yaml_from("config/scraping.yml")["awws"][awws_report][
        "known-fields"
    ]
    page_data = {}
    page_data["report"] = awws_report

    # Report Timestamp
    page = BeautifulSoup(source, "lxml")
    timestamp = page.find_all("span", class_="corps")[0].find("b").text
    clean_timestamp = timestamp.replace("at ", "").replace(" UTC", "").strip()
    page_data["report_timestamp"] = clean_timestamp

    # Process Each Table on the Page and add to dictionary.
    # For each, parse the table values and match them
    # against passed in known fields.
    tables = page.find_all("table", {"width": "665"})
    for table_number, table in enumerate(tables):
        table_data = {}
        print(table_number, "=" * 20, "\n")
        table_items = table.find_all("td")
        for item_number, table_item in enumerate(table_items):
            # Clean values slightly while removing the first of the
            # text rows as the field label.
            field_values = table_item.text.strip().replace("\xa0", " ").split("\n")
            field_item = field_values.pop(0).lower()

            # Handle full encoded report (always first item) as
            # proper encoded capital letters.
            if item_number == 0:
                logging.debug(f"Encoded Report Matched: {field_item.upper()}.")
                table_data["encodedreport"] = field_item.upper().strip()

            # Match known field items,
            # and handle missing/messy field values.
            if field_item in known_fields:
                logging.debug(f"Item Matched: {field_item}")
                if field_values:
                    logging.debug(f"Following Field Value: {field_values}")
                    cleaned_field_values = [
                        (re.sub(r"\s+", " ", value.strip()))
                        for value in field_values
                        if value
                    ]
                    table_data[field_item] = cleaned_field_values
                else:
                    logging.debug(f"No field value for {field_item}.")
        page_data[table_number] = table_data
    # Get Page Report Location from first 2 tables if possible.
    # Necessary for eventual partitioning on location in NoSQL.
    if page_data[0]["location"]:
        page_data["report_location"] = page_data[0]["location"][0]
    elif page_data[1] and page_data[1]["location"]:
        page_data["report_location"] = page_data[1]["location"][0]
    else:
        page_data["report_location"] = "unknown"
    return page_data
