# TODO Function to connect to Database.
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
