import datetime

import pytest
from bs4 import BeautifulSoup

import src.data.scraping as scraping


@pytest.fixture
def known_awws_metar_van_source():
    with open("test/known_awws_metar_van_source.html") as f:
        known_page_source = f.read()
    return known_page_source


@pytest.fixture
def known_awws_metar_abbotsford_source():
    with open("test/known_awws_metar_abbotsford_source.html") as f:
        known_page_source = f.read()
    return known_page_source


@pytest.fixture
def known_awws_metar_van_soup(known_awws_metar_van_source):
    known_page_soup = BeautifulSoup(known_awws_metar_van_source, "lxml")
    return known_page_soup


@pytest.fixture
def known_awws_metar_abbotsford_soup(known_awws_metar_abbotsford_source):
    known_page_soup = BeautifulSoup(known_awws_metar_abbotsford_source, "lxml")
    return known_page_soup


class TestAWWSScraping:
    @pytest.mark.slow()
    @pytest.mark.online()
    def test_awws_metar_vancouver_page_scrape_connects_to_correct_page(
        self, known_awws_metar_van_soup
    ):
        awws_vancouver_source = scraping.scrape_awws_metar_pagesource("vancouver")
        awws_vancouver_page = BeautifulSoup(awws_vancouver_source, "lxml")
        assert awws_vancouver_page.title.text == known_awws_metar_van_soup.title.text

    @pytest.mark.slow()
    @pytest.mark.online()
    def test_awws_metar_abbotsford_page_scrape_connects_to_correct_page(
        self, known_awws_metar_abbotsford_soup
    ):
        awws_abbotsford_source = scraping.scrape_awws_metar_pagesource("abbotsford")
        awws_abbotsford_page = BeautifulSoup(awws_abbotsford_source, "lxml")
        assert (
            awws_abbotsford_page.title.text
            == known_awws_metar_abbotsford_soup.title.text
        )

    def test_awws_metar_vancouver_source_parses_to_expected_dict(
        self, known_awws_metar_van_source
    ):
        known_awws_metar_van_dict = scraping.parse_awws_pagesource(
            known_awws_metar_van_source
        )
        # Report Data (pushed to each Box)
        assert known_awws_metar_van_dict[0]["report"] == "metar-taf"
        assert known_awws_metar_van_dict[1]["report"] == "metar-taf"
        assert known_awws_metar_van_dict[0]["report_timestamp"] == "10/20/2022 05:03:30"
        assert known_awws_metar_van_dict[1]["report_timestamp"] == "10/20/2022 05:03:30"
        # Box 1 Data
        assert (
            known_awws_metar_van_dict[0]["encodedreport"]
            == "METAR CYVR 200400Z VRB02KT 15SM BKN220 11/11 A3022 RMK CI5 VIS N LWR SLP235="
        )
        assert known_awws_metar_van_dict[0]["location"] == "CYVR - VANCOUVER INTL/BC"
        assert known_awws_metar_van_dict[0]["datetime"] == "2022-10-19 21:00 PDT"
        assert known_awws_metar_van_dict[0]["wind"] == ["VRB @ 2 KNOTS"]
        assert known_awws_metar_van_dict[0]["visibility"] == ["15 STAT. MILES"]
        assert known_awws_metar_van_dict[0]["cloudiness"] == [
            "BROKEN CLOUDS (5/8 - 7/8) 22000 FT"
        ]
        assert known_awws_metar_van_dict[0]["temp / dewpoint"] == ["11 C /", "11 C"]
        assert known_awws_metar_van_dict[0]["altimeter"] == ["30.22 IN HG"]
        # Box 2 Data
        assert (
            known_awws_metar_van_dict[1]["encodedreport"]
            == "METAR CYVR 200300Z 00000KT 15SM PRFG MIFG FEW120 SCT220 11/11 A3022 RMK AC1CI3"
        )
        assert known_awws_metar_van_dict[1]["location"] == "CYVR - VANCOUVER INTL/BC"
        assert known_awws_metar_van_dict[1]["datetime"] == "2022-10-19 20:00 PDT"
        assert known_awws_metar_van_dict[1]["wind"] == ["CALM"]
        assert known_awws_metar_van_dict[1]["visibility"] == ["15 STAT. MILES"]
        assert known_awws_metar_van_dict[1]["weather"] == [
            "PARTIAL COVERAGE OF FOG",
            "SHALLOW FOG",
        ]
        assert known_awws_metar_van_dict[1]["cloudiness"] == [
            "FEW CLOUDS (1/8 - 2/8) 12000 FT",
            "SCATTERED CLOUDS (3/8 - 4/8) 22000 FT",
        ]
        assert known_awws_metar_van_dict[1]["temp / dewpoint"] == ["11 C /", "11 C"]
        assert known_awws_metar_van_dict[1]["altimeter"] == ["30.22 IN HG"]

    def test_awws_metar_vancouver_source_excludes_empty_fields(
        self, known_awws_metar_van_source
    ):
        known_awws_metar_van_dict = scraping.parse_awws_pagesource(
            known_awws_metar_van_source
        )
        with pytest.raises(KeyError):
            known_awws_metar_van_dict[0]["weather"]

    @pytest.mark.xfail(strict=False)
    @pytest.mark.slow()
    @pytest.mark.online()
    def test_integration_for_awws_metar_web_scrape_components_provides_keys(self):
        page_source = scraping.scrape_awws_metar_pagesource()
        page_dict = scraping.parse_awws_pagesource(page_source)
        for table in page_dict.values():
            # Location and datetime are our DynamoDB keys.
            report_location = table["location"]
            assert type(report_location) is str

            report_datetime = datetime.datetime.strptime(
                table["datetime"], "%Y-%m-%d %H:%M %Z"
            )
            assert type(report_datetime) is datetime.datetime


def test_known_utc_string_parses_correctly_to_utc():
    awws_utc_datetime_string = "28 OCTOBER 2022 - 0300 UTC"
    expected_awws_utc_datetime_string = "2022-10-28 03:00 UTC"
    assert (
        scraping.format_utc_datetime(awws_utc_datetime_string)
        == expected_awws_utc_datetime_string
    )


def test_known_utc_string_parses_correctly_to_pst():
    awws_utc_datetime_string = "28 OCTOBER 2022 - 0300 UTC"
    expected_awws_pst_datetime_string = "2022-10-27 20:00 PDT"
    assert (
        scraping.format_utc_datetime(
            awws_utc_datetime_string, target_timezone="America/Vancouver"
        )
        == expected_awws_pst_datetime_string
    )
