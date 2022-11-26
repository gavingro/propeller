import pytest
import os
import subprocess
import logging
import json

import botocore
import boto3

from src.data import database
from src import config


@pytest.fixture
def known_awws_metar_van_data():
    with open("test/known_awws_metar_van_data.json") as f:
        data = json.load(f)
    # Update JSON (string) keys to the integers we create during scraping.
    updated_key_data = {int(table_num) : table_data for table_num, table_data in data.items()}
    return updated_key_data


@pytest.fixture
def known_awws_metar_abbotsford_data():
    with open("test/known_awws_metar_abbotsford_data.json") as f:
        data = json.load(f)
    # Update JSON (string) keys to the integers we create during scraping.
    updated_key_data = {int(table_num) : table_data for table_num, table_data in data.items()}
    return updated_key_data


@pytest.fixture
def data_config():
    data_config = config.read_yaml_from("config/data.yml")
    return data_config


@pytest.mark.local_db
@pytest.fixture
def local_dynamo_db(data_config):
    # If on home computer, spin up local database server in subprocess.
    if os.popen("hostname").read() == "gavs-lil-mac.local\n":
        logging.debug("Starting Local DyanamoDB server subprocess.")
        local_db_server = subprocess.Popen(
            "exec java "
            "-Djava.library.path=dynamodb_local_latest/DynamoDBLocal_lib "
            "-jar dynamodb_local_latest/DynamoDBLocal.jar -sharedDb",
            shell=True,
        )
    else:
        logging.debug("Not running on local laptop, no need to start DB.")
        local_db_server = None

    # Setup Local DynamoDB Connection Client
    test_url_endpoint = data_config["dynamodb"]["test"]["endpoint-url"]
    db_client = boto3.resource("dynamodb", endpoint_url=test_url_endpoint)
    yield db_client
    # Cleanup DB Client and Local DynamoDB Server, if necessary.
    if local_db_server:
        try:
            local_db_server.terminate()
            local_db_server.wait(1)
            logging.debug("Local DyanamoDB server terminated successfully.")
        except subprocess.TimeoutExpired:
            local_db_server.kill()
            logging.warning(
                "Local DyanamoDB server unable to terminate. Process killed."
            )


@pytest.mark.local_db
@pytest.fixture
def local_awws_metar_table_in_db(local_dynamo_db, data_config):
    # Get Table Info
    metar_taf_config = data_config["dynamodb"]["awws"]["metar-taf"]
    table_name = metar_taf_config["table-name"]
    partition_key = metar_taf_config["partition-key"]
    sort_key = metar_taf_config["sort-key"]

    # Clear table if exists already.
    existing_tables = [table.table_name for table in local_dynamo_db.tables.all()]
    if table_name in existing_tables:
        table = local_dynamo_db.Table(table_name)
        table.delete()
        table.wait_until_not_exists()

    # Create Table.
    local_dynamo_db.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": partition_key, "KeyType": "HASH"},
            {"AttributeName": sort_key, "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": partition_key, "AttributeType": "S"},
            {"AttributeName": sort_key, "AttributeType": "S"},
        ],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )
    # Wait for the Async Table Creation Task to finish.
    # Ideally, we should wait for the table status to be READY, not CREATING.
    table = local_dynamo_db.Table(table_name)
    table.wait_until_exists()
    logging.debug("AWWS METAR table created in Local DB for testing.")
    yield local_dynamo_db

    # Cleanup Table.
    table.delete()


@pytest.mark.expensive
@pytest.mark.online
def test_dynamodb_context_manager_connects_to_aws(data_config):
    table_name = data_config["dynamodb"]["awws"]["metar-taf"]["table-name"]
    with database.dynamodb_connection() as db:
        table = db.Table(table_name)
        assert table.table_status == "ACTIVE"


@pytest.mark.local_db
def test_dynamodb_context_manager_connects_to_local_db(
    local_awws_metar_table_in_db, data_config
):
    table_name = data_config["dynamodb"]["awws"]["metar-taf"]["table-name"]
    table = local_awws_metar_table_in_db.Table(table_name)
    assert table.table_status == "ACTIVE"


@pytest.mark.slow
def test_dynamodb_context_manager_errors_on_bad_endpoint():
    with pytest.raises(botocore.exceptions.EndpointConnectionError):
        with database.dynamodb_connection(endpoint_url="http://iamabadaddress") as db:
            table = db.Table("bad-table-name-doesnt-exist")
            # Call some attribute to force table db connection.
            assert table.billing_mode_summary is None


@pytest.mark.local_db
@pytest.mark.parametrize(
    "data, expected_count",
    [("known_awws_metar_van_data", 4), ("known_awws_metar_abbotsford_data", 4)],
)
def test_write_data_document_writes_expected_amount_of_documents(
    local_awws_metar_table_in_db, data_config, request, data, expected_count
):
    data = request.getfixturevalue(data)
    database.write_data_documents_to_awws_database(
        db=local_awws_metar_table_in_db,
        data_documents=data,
    )

    table_name = data_config["dynamodb"]["awws"]["metar-taf"]["table-name"]
    table = local_awws_metar_table_in_db.Table(table_name)
    item_count = table.item_count
    assert item_count == expected_count
