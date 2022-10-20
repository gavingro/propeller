import logging

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import selenium.webdriver.chrome as chrome

from src import config


# TODO: WRITE QUICK TESTS.
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
    # Get URL
    scraping_yaml_path = "config/scraping.yml"
    scraping_config = config.read_yaml_from(scraping_yaml_path)
    logging.debug(f"{scraping_config=}")
    awws_config = scraping_config["awws"]["metar-taf"]
    location_config = awws_config["locations"][location]
    location_code = location_config["code"]

    # Setup Selenium Chrome Driver
    chrome_options = chrome.options.Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=chrome.service.Service(
            ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        ),
        options=chrome_options,
    )

    # Navigate to report
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


# with open("test/test_web_source.html", "r") as f:
#     source = f.read()
# page = BeautifulSoup(source, features="lxml")
# print(f"{page.title=}, {page.title.string=}")

# TODO Function to parse through AWWS response content with beautifulsoup and get bits.
def parse_awws_metar_pagesource(page_source: str) -> dict:
    """
    Parses the page source of expected METAR web page for data.

    Data from page is organized into a dictionary and returned.

    Parameters
    ----------
    page_source : str
        HTML page source string of the AWWS METAR page,
        ideally generated with scrape_awws_metar_pagesource()
        function.

    Returns
    -------
    dict
        Organized dictionary of weather data from web page.
    """
    raise NotImplementedError


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
