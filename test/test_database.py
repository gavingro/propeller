import pytest
import os
import subprocess
import logging

import botocore
import boto3

from src.data import database
from src import config


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
    db_client = boto3.client("dynamodb", endpoint_url=test_url_endpoint)
    yield db_client
    # Cleanup DB Client and Local DynamoDB Server, if necessary.
    db_client.close()
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
    table_exists_waiter = local_dynamo_db.get_waiter("table_exists")
    table_exists_waiter.wait(
        TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 10}
    )
    logging.debug("AWWS METAR table created in Local DB for testing.")
    yield local_dynamo_db
    # Cleanup Table.
    local_dynamo_db.delete_table(TableName=table_name)
    table_not_exists_waiter = local_dynamo_db.get_waiter("table_not_exists")
    table_not_exists_waiter.wait(
        TableName=table_name, WaiterConfig={"Delay": 1, "MaxAttempts": 10}
    )
    logging.debug("AWWS METAR table in Local DB for testing sucessfully deleted.")


@pytest.mark.expensive
@pytest.mark.online
def test_dynamodb_context_manager_connects_to_aws():
    with database.dynamodb_connection() as db:
        response = db.list_tables()
    assert type(response) == dict


@pytest.mark.local_db
def test_dynamodb_context_manager_connects_to_local_db(local_dynamo_db):
    with database.dynamodb_connection(endpoint_url="http://localhost:8000") as db:
        response = db.list_tables()
    assert type(response) == dict


@pytest.mark.slow
def test_dynamodb_context_manager_errors_on_bad_endpoint():
    with pytest.raises(botocore.exceptions.EndpointConnectionError):
        with database.dynamodb_connection(endpoint_url="http://localhost:8080") as db:
            db.list_tables()


def test_local_db_connection(local_awws_metar_table_in_db, data_config):
    table_name = data_config["dynamodb"]["awws"]["metar-taf"]["table-name"]
    response = local_awws_metar_table_in_db.describe_table(TableName=table_name)
