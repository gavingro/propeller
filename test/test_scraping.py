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
    def test_awws_metar_vancouver_page_scrape_connects_to_correct_page(
        self, known_awws_van_soup
    ):
        awws_vancouver_source = scraping.scrape_awws_metar_pagesource("vancouver")
        awws_vancouver_page = BeautifulSoup(awws_vancouver_source, "lxml")
        assert awws_vancouver_page.title.text == known_awws_van_soup.title.text

    def test_awws_metar_vancouver_source_parses_to_expected_dict(
        self, known_awws_van_source
    ):
        known_awws_van_dict = scraping.parse_awws_pagesource(known_awws_van_source)
        # Report Data
        assert known_awws_van_dict["report_timestamp"] == "10/20/2022 05:03:30"
        # Box 1 Data
        assert known_awws_van_dict[0]["location"] == "CYVR - VANCOUVER INTL/BC"
        assert known_awws_van_dict[0]["date-time"] == "20 OCTOBER 2022 - 0400 UTC"
        assert known_awws_van_dict[0]["wind"] == "VRB @ 2  KNOTS"
        assert known_awws_van_dict[0]["visibility"] == "15 STAT.  MILES"
        assert (
            known_awws_van_dict[0]["cloudiness"]
            == "BROKEN CLOUDS (5/8 - 7/8) 22000  FT"
        )
        assert known_awws_van_dict[0]["temperature / dewpoint"] == "11 C / 11 C"
        assert known_awws_van_dict[0]["altimeter"] == "30.22 IN HG"
        # Box 2 Data
        assert known_awws_van_dict[1]["location"] == "CYVR - VANCOUVER INTL/BC"
        assert known_awws_van_dict[1]["date-time"] == "20 OCTOBER 2022 - 0300 UTC"
        assert known_awws_van_dict[1]["wind"] == "CALM"
        assert known_awws_van_dict[1]["visibility"] == "15 STAT.  MILES"
        assert known_awws_van_dict[1]["weather"] == [
            "PARTIAL COVERAGE OF FOG",
            "SHALLOW FOG",
        ]
        assert known_awws_van_dict[1]["cloudiness"] == [
            "FEW CLOUDS (1/8 - 2/8) 12000  FT",
            "SCATTERED CLOUDS (3/8 - 4/8) 22000  FT",
        ]
        assert known_awws_van_dict[1]["temperature / dewpoint"] == "11 C / 11 C"
        assert known_awws_van_dict[1]["altimeter"] == "30.22 IN HG"
