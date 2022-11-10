import contextlib
from typing import Literal

import boto3

from src import config


# Using the boto3 client interface instead of the
# boto3 resource interface allows us to access
# the local DynamoDB database by URL for testing.
@contextlib.contextmanager
def dynamodb_connection(**boto_client_kwargs):
    """
    Creates a resource connection to AWS DynamoDB with
    the passed in keyword arguments.

    Notably, use endpoint_url = http://localhost:8000
    to connect to local DynamoDB instance.

    Parameters
    ------
    boto_client_kwargs: dictionary
        Keyword arguments for Boto3's client connection.

    Yields
    ------
    botocore.ServiceResource
        A boto3 resource connection to a DynamoDB instance.
    """
    db_client = boto3.resource("dynamodb", **boto_client_kwargs)
    yield db_client


# @contextlib.contextmanager
# def dynamodb_connection(**boto_client_kwargs):
#     """
#     Creates a client connection to AWS DynamoDB with
#     the passed in keyword arguments.

#     Notably, use endpoint_url = http://localhost:8000
#     to connect to local DynamoDB instance.

#     Parameters
#     ------
#     boto_client_kwargs: dictionary
#         Keyword arguments for Boto3's client connection.

#     Yields
#     ------
#     botocore.client.DynamoDb
#         A boto3 client connection to a DynamoDB instance.
#     """
#     db_client = boto3.client("dynamodb", **boto_client_kwargs)
#     try:
#         yield db_client
#     finally:
#         db_client.close()


# TODO Function to write to database.
def write_data_document_to_awws_database(
    db: boto3.resources.factory,
    data: dict,
    database_id: Literal["metar-taf"] = "metar-taf",
) -> None:
    """
    Takes the input data dictionary and writes it to the database
    at the provided database_id.

    Parameters
    ----------
    client: botocore.client.DynamoDB
        A boto3 client connection connecting to a DynamoDB
        database, ideally created with dynamodb_connection().
    data : dict
        Dictionary of data values, ideally from the
        parse_awws_metar_pagesource() function.
    database_id : str
        Id to identify the database config information.
        Currently only ["metar-taf"] is supported.
        Must also exist in the data.yml config file.
    """
    raise NotImplementedError
    # Get Config.
    data_config = config.read_yaml_from("config/data.yml")
    table_config = data_config["dynamodb"]["awws"][database_id]
    table_name = table_config["table-name"]
    # partition_key = table_config["partition-key"]
    # sort_key = table_config["sort-key"]

    # Write to Table
    table = db.Table(table_name)
    table.put_item(Item=data)
    # WRITE TEST AND ENSURE IT WORKS
