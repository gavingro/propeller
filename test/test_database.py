import pytest
import botocore

from src.data import database


@pytest.mark.expensive
@pytest.mark.online
def test_dynamodb_context_manager_connects_to_aws():
    with database.dynamodb_connection() as db:
        response = db.list_tables()
    assert type(response) == dict


@pytest.mark.local_db
def test_dynamodb_context_manager_connects_to_local_db():
    with database.dynamodb_connection(endpoint_url="http://localhost:8000") as db:
        response = db.list_tables()
    assert type(response) == dict


@pytest.mark.slow
def test_dynamodb_context_manager_errors_on_bad_endpoint():
    with pytest.raises(botocore.exceptions.EndpointConnectionError):
        with database.dynamodb_connection(endpoint_url="http://localhost:8080") as db:
            db.list_tables()
