import logging
import re
from typing import Literal
from datetime import datetime
import pytz

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
        by default 'vancouver'.

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
        ChromeDriverManager(
            version="85.0.4183.83-0ubuntu2", chrome_type=ChromeType.CHROMIUM
        ).install()
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


def format_utc_datetime(
    utc_string: str,
    target_timezone: str = None,
    format_string: str = "%d %B %Y - %H%M %Z",
) -> str:
    """
    Transforms the string representation of a UTC datetime
    scraped into a uniform datetime string, optionally in
    a passed-in timezone.

    Parameters
    ----------
    utc_string : str
        A string representation of a UTC datetime,
        similar to those scraped from the AWWS pagesource.

    target_timezone : str
        A string representing a timezone from the pytz package.
        If included, the datetime will be converted to the
        timezone specified, otherwise it will be in UTC time.
        By default None.

    format_string : str
        The format of the expected UTC string to read, by
        default matching the format found in the AWWS weather
        reports: "d MMM YYYY - HHMM UTC".

    Returns
    -------
    str
        The datetime string in the format "YYYY-MM-DD HH:MM Z"

    Examples
    --------
    >> format_scraped_utc_string_to_local_datetime("28 OCTOBER 2022 - 0300 UTC")
    2022-10-27 20:00 UTC

    >> format_scraped_utc_string_to_local_datetime(
        "28 OCTOBER 2022 - 0300 UTC",
        timezone = "America/Vancouver")
    2022-10-27 20:00 PDT

    """
    new_datetime = datetime.strptime(utc_string, format_string)
    aware_datetime = pytz.utc.localize(new_datetime)
    if target_timezone:
        local_tz = pytz.timezone(target_timezone)
        aware_datetime = local_tz.normalize(
            aware_datetime.replace(tzinfo=pytz.utc).astimezone(tz=local_tz)
        )
    new_datetime_string = aware_datetime.strftime("%Y-%m-%d %H:%M %Z")
    return new_datetime_string


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

    awws_report: Literal["metar-taf"]
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

    # Get Timestamp to add to each table.
    page = BeautifulSoup(source, "lxml")
    timestamp = page.find_all("span", class_="corps")[0].find("b").text
    clean_timestamp = timestamp.replace("at ", "").replace(" UTC", "").strip()

    # Process each table on the Page and add to dictionary.
    # For each, parse the table values and match them
    # against passed in known fields.
    tables = page.find_all("table", {"width": "665"})
    for table_number, table in enumerate(tables):
        table_data = {}
        table_data["report_timestamp"] = clean_timestamp
        table_data["report"] = awws_report

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
                        re.sub(r"\s+", " ", value.strip())
                        for value in field_values
                        if value
                    ]
                    # Leaving as list, even for single elements.
                    table_data[field_item] = cleaned_field_values
                else:
                    logging.debug(f"No field value for {field_item}.")

        # Clean up the location for reports to use as Partition Key
        # in Dynamo DB.
        if "location" in table_data.keys():
            table_data["location"] = table_data["location"][0]

        # Clean up the datetime for reports and convert to Vancouver
        # time to use as Sort Key for Dynamo DB.
        if "date - time" in table_data.keys():
            table_data["datetime"] = format_utc_datetime(
                table_data["date - time"][0], target_timezone="America/Vancouver"
            )
            table_data["date - time"].pop
        page_data[table_number] = table_data
    return page_data
