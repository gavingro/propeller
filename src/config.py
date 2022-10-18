import yaml


def read_yaml_from(filepath: str) -> dict:
    """
    Reads the yaml file at the filepath and
    unpacks it into a returned dictionary.

    Parameters
    ----------
    filepath : str
        Path (from main level) to the yaml file.

    Returns
    -------
    dict
        Dictionary of YAML contents.
    """
    #Todo: Update to use Pathlib.
    with open(filepath, "r") as f:
        yaml_text = f.read()
    return yaml.full_load(yaml_text)
