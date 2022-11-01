import contextlib

import boto3

from src import config


@contextlib.contextmanager
def dynamodb_connection(**boto_client_kwargs):
    """
    Creates a client connection to AWS DynamoDB with 
    the passed in keyword arguments.
    
    Notably, use endpoint_url = http://localhost:8000
    to connect to local DynamoDB instance.

    Yields
    ------
    boto_client_kwargs: dictionary
        Keyword arguments for Boto3's client connection.
    """
    db_client = boto3.client("dynamodb", **boto_client_kwargs)
    try:
        yield db_client
    finally:
        db_client.close()
    
    


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
