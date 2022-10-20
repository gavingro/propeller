import pytest
from bs4 import BeautifulSoup

import src.data.scraping as scraping


@pytest.fixture
def known_awws_van_source():
    with open("test/test_web_source.html") as f:
        known_page_source = f.read()
    return known_page_source


@pytest.fixture
def known_awws_van_soup(known_awws_van_source):
    known_page_soup = BeautifulSoup(known_awws_van_source, "lxml")
    return known_page_soup


class TestAWWSScraping:
    @pytest.mark.slow()
    @pytest.mark.online()
    def test_awws_page_scrape_vancouver_title(self, known_awws_van_soup):
        awws_vancouver_source = scraping.scrape_awws_metar_pagesource("vancouver")
        awws_vancouver_page = BeautifulSoup(awws_vancouver_source, "lxml")
        assert awws_vancouver_page.title.text == known_awws_van_soup.title.text
