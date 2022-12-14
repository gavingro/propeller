import contextlib
import logging

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
        Keyword arguments for Boto3's resource connection.

    Yields
    ------
    botocore.ServiceResource
        A boto3 resource connection to a DynamoDB instance.
    """
    db_client = boto3.resource("dynamodb", **boto_client_kwargs)
    yield db_client


def write_data_documents_to_awws_database(
    db: boto3.resources.factory, data_documents: dict
) -> None:
    """
    Takes the input data dictionary and writes it to the database
    at the respective report_type.

    Parameters
    ----------
    db: boto3.resources.factory
        A boto3 resource connection connecting to a DynamoDB
        database, ideally created with dynamodb_connection().
    data : dict
        Dictionary of data values, ideally the
        collectino of documents from the
        parse_awws_metar_pagesource() function.
    """
    # Handle empty case.
    if not data_documents:
        return

    # Get Config.
    data_config = config.read_yaml_from("config/data.yml")
    report_type = data_documents[0]["report"]
    table_config = data_config["dynamodb"]["awws"][report_type]
    table_name = table_config["table-name"]
    partition_key = table_config["partition-key"]
    sort_key = table_config["sort-key"]

    # Write to Table if it has the necessary keys.
    # If not, log warnings.
    table = db.Table(table_name)
    document_skip_count = 0
    for data_document in data_documents.values():
        if data_document.get(partition_key, None) and data_document.get(sort_key, None):
            table.put_item(Item=data_document)
        else:
            document_skip_count += 1
            if data_document.get(partition_key, None):
                logging.warning(
                    "AWS Report skipped because Sort Key (Date) is missing from data."
                )
            elif data_document.get(sort_key, None):
                logging.warning(
                    "AWS Report skipped because Partition Key (Location) is missing from data."
                )
            else:
                logging.warning(
                    "AWS report skipped because both Sort Key (Date) "
                    "and Partition Key (Location) are missing from data."
                )
    if document_skip_count:
        logging.warning(
            f"{document_skip_count} / {len(data_documents.values())} documents skipped."
        )
