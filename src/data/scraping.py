import logging

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import selenium.webdriver.chrome as chrome
from bs4 import BeautifulSoup

from src import config


def scrape_awws_metar_pagesource(location: str = "vancouver") -> str:
    """
    Connect to Aviation Weather Web Site to scrape the METAR - TAF forecasts
    for the given location.

    Parameters
    ----------
    location : str, optional
        The plain-language location for the airspace data you want to scrape,
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


# TODO Function to parse through AWWS response content with beautifulsoup and get bits.
KNOWN_METAR_TABLE_ITEMS = [
    "metar",
    "location",
    "date - time",
    "wind",
    "visibility",
    "runway visible range",
    "weather",
    "cloudiness",
    "temp / dewpoint",
    "altimeter",
    "recent weather",
    "wind shear",
]


def parse_awws_pagesource(
    source: str, known_fields: list = KNOWN_METAR_TABLE_ITEMS
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

    Returns
    -------
    dict
        Organized dictionary of weather data from web page.
    """
    page_data = {}
    page = BeautifulSoup(source, "lxml")

    # Report Timestamp
    timestamp = page.find_all("span", class_="corps")[0].find("b").text
    timestamp = timestamp.replace("at ", "").replace(" UTC", "")
    page_data["report_timestamp"] = timestamp

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
                table_data["encodedreport"] = field_item.upper()

            # Match known field items, and handle missing field values.
            if field_item in known_fields:
                logging.debug(f"Item Matched: {field_item}")
                if field_values:
                    logging.debug(f"Following Field Value: {field_values}")
                    table_data[field_item] = field_values
                else:
                    logging.debug(f"No field value for {field_item}.")
        page_data[table_number] = table_data
    return page_data


# TODO Function to connect to Database.
# TODO Function to write to database.
def write_data_dict_to_database(data: dict, database_id: str) -> None:
    """
    Takes the input data dictionary and writes it to the database
    at the provided database_id.

    Parameters
    ----------
    data : dict
        Dictionary of data values, ideally from the
        parse_awws_metar_pagesource() function.
    database_id : str
        Id to identify the database.
        Must also exist in the data.yml config file.
    """
    raise NotImplementedError
