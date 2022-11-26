# propeller

![Badge Status for Src Test](https://github.com/gavingro/propeller/actions/workflows/lint-test.yml/badge.svg)
![Badge Status Code Coverage](https://github.com/gavingro/propeller/blob/main/reports/coverage.svg)

An in-progress project to predict how 'flyable' vancouver airbases will be.

*Todo: Add Value Statement.*

---

## Recent Changes

* Web Scraping Scripts
* DynamoDB Scripting

---

## App

*To come: Visual and description of App for end-user.*

## Predictions

*Todo: Description of ML models used.*

*Todo: Add performance tables and metrics.*

## Components

*Todo: Add large DAG visualization.*

### Web Scraping

Includes python script components using **Selenium** to visit and scrape web data from AWWS METAR-TAF data from AWS web pages, and parse them into data documents with **BeautifulSoup**.

* Relevent scripts found in `src/scraping.py`.
* Relevent config information found in `config/scraping.yml`.

### NoSQL (Document Based) Database

Includes the use of **AWS DynamoDB**, a document-based NoSQL database, to store our semi-structured meteorological data that we scrape from the AWWS web pages. **Boto3** is used within python scripts to access and write to database (as well as create local databases for testing).

* Relevent scripts found in `src/data.yml`.
* Relevent config information found in `config/data.yml`.

---

## Filetree

* `src/`
    * Contains relevent python scripts and components.
* `config/`
    * Contains relevent hyperparameters and constants for various aspects of the project, stored in YAML files.
* `reports/`
    * Contains documents displaying validation and performance information of the current project version.
