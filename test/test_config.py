import os
import pytest
import yaml

import src.config as config


@pytest.fixture
def good_yaml_at_path():
    # Save YAML to file
    good_document = {"a": 1, "b": {"c": {"d": 3}, "e": {"f": 4}}}
    document_path = "good_document.yml"
    with open(document_path, "w") as file:
        yaml.dump(good_document, file)
    # Pass filepath to tests.
    yield document_path
    # Cleanup temporary YAML file.
    os.remove(document_path)


def test_read_good_yaml(good_yaml_at_path):
    document = config.read_yaml_from(good_yaml_at_path)
    assert type(document) == dict
    assert document["a"] == 1
    assert type(document["b"]) == dict
    assert type(document["b"]["c"]) == dict
    assert document["b"]["e"]["f"] == 4
