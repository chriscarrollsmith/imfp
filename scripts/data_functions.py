import pandas as pd
from functools import partial
from utils import _download_parse, _imf_dimensions, _imf_metadata
from urllib.parse import urlencode
from typing import Union, List, Dict, Tuple


def imf_databases(times=3):
    """
    List IMF database IDs and descriptions
    
    Returns a DataFrame with database_id and text description for each
    database available through the IMF API endpoint.
    
    Parameters
    ----------
    times : int, optional, default 3
        Maximum number of API requests to attempt.
    
    Returns
    -------
    pandas.DataFrame
        DataFrame containing database_id and description columns.
    
    Examples
    --------
    # Return first 6 IMF database IDs and descriptions
    databases = imf_databases()
    """
    url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow'
    raw_dl = _download_parse(url, times)

    database_id = [dataflow['KeyFamilyRef']['KeyFamilyID'] for dataflow in raw_dl['Structure']['Dataflows']['Dataflow']]
    description = [dataflow['Name']['#text'] for dataflow in raw_dl['Structure']['Dataflows']['Dataflow']]
    database_list = pd.DataFrame({'database_id': database_id, 'description': description})
    return database_list


def imf_parameters(database_id, times=3):
    """
    List input parameters and available parameter values for use in
    making API requests from a given IMF database.

    Parameters
    ----------
    database_id : str
        A database_id from imf_databases().
    times : int, optional, default 3
        Maximum number of API requests to attempt.

    Returns
    -------
    dict
        A dictionary of DataFrames, where each key corresponds to an input
        parameter for API requests from the database. All values are DataFrames
        with an 'input_code' column and a 'description' column. The
        'input_code' column is a character list of all possible input codes for
        that parameter when making requests from the IMF API endpoint. The
        'descriptions' column is a character list of text descriptions of what
        each input code represents.

    Examples
    --------
    # Fetch the full list of indicator codes and descriptions for the Primary
    # Commodity Price System database
    params = imf_parameters(database_id='PCPS')
    """
    if not database_id:
        raise ValueError('Must supply database_id. Use imf_databases to find.')

    url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/CodeList/'
    try:
        codelist = _imf_dimensions(database_id, times)
    except Exception as e:
        if '<string xmlns=' in str(e):
            raise ValueError(f"{e}\n\nDid you supply a valid database_id? Use imf_databases to find.")
        else:
            raise ValueError(e)

    def fetch_parameter_data(k, url, times):
        if codelist.loc[k, 'parameter'] == 'freq':
            return pd.DataFrame({"input_code": ["A", "M", "Q"],
                                 "description": ["Annual", "Monthly", "Quarterly"]})
        else:
            raw = _download_parse(url + codelist.loc[k, 'code'], times)['Structure']['CodeLists']['CodeList']['Code']
            return pd.DataFrame({"input_code": [code['@value'] for code in raw],
                                 "description": [code['Description']['#text'] for code in raw]})

    parameter_list = {codelist.loc[k, 'parameter']: fetch_parameter_data(k, url, times)
                      for k in range(codelist.shape[0])}

    return parameter_list


import pandas as pd
from utils import _imf_dimensions

def imf_parameter_defs(database_id, times=3, inputs_only=False):
    """
    Get text descriptions of input parameters used in making API
    requests from a given IMF database

    Parameters
    ----------
    database_id : str
        A database_id from imf_databases().
    times : int, optional, default 3
        Maximum number of API requests to attempt.
    inputs_only : bool, optional, default False
        Whether to return only parameters used as inputs in API requests,
        or also output variables.

    Returns
    -------
    pandas.DataFrame
        A DataFrame of input parameters used in making API requests
        from a given IMF database, along with text descriptions or definitions
        of those parameters. Useful in cases when parameter names returned by
        imf_databases() are not self-explanatory. (Note that the usefulness
        of text descriptions can be uneven, depending on the database design.)

    Examples
    --------
    # Get names and text descriptions of parameters used in IMF API calls to the
    # Primary Commodity Price System database
    param_defs = imf_parameter_defs(database_id='PCPS')
    """
    if not database_id:
        raise ValueError('Must supply database_id. Use imf_databases to find.')

    url = 'http://dataservices.imf.org/REST/SDMX_JSON.svc/CodeList/'
    parameterlist = _imf_dimensions(database_id, times)[['parameter', 'description']]

    return parameterlist


def imf_dataset(database_id: str, parameters: Dict = None, start_year: int = None, end_year: int = None,
                return_raw: bool = False, print_url: bool = False, times: int = 3,
                include_metadata: bool = False, **kwargs) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Download a data series from the IMF.

    Args:
        database_id (str): Database ID for the database from which you would like to request data.
                           Can be found using imf_databases().
        parameters (dict): Dictionary of data frames providing input parameters for your
                           API request. Retrieve dictionary of all possible input parameters using
                           imf_parameters() and filter each data frame in the dictionary to
                           reduce it to the inputs you want.
        start_year (int, optional): Four-digit year. Earliest year for which you would like
                                     to request data.
        end_year (int, optional): Four-digit year. Latest year for which you would like to
                                   request data.
        return_raw (bool, optional): Whether to return the raw list returned by the API
                                     instead of a cleaned-up data frame.
        print_url (bool, optional): Whether to print the URL used in the API call.
        times (int, optional): Maximum number of requests to attempt.
        include_metadata (bool, optional): Whether to return the database metadata
                                           header along with the data series.
        **kwargs: Additional keyword arguments for specifying parameters as separate arguments.
                  Use imf_parameters() to identify which parameters to use for requests from a
                  given database and to see all valid input codes for each parameter.

    Returns:
        If return_raw == False and include_metadata == False, returns a tidy
        DataFrame with the data series. If return_raw == False but
        include_metadata == True, returns a tuple whose first item is the database
        header, and whose second item is the tidy DataFrame. If return_raw == True,
        returns the raw JSON fetched from the API endpoint.
    """

    if database_id is None:
        raise ValueError("Missing required database_id argument.")

    if not isinstance(database_id, str):
        raise ValueError("database_id must be a string.")

    years = {}
    if start_year is not None:
        years['startPeriod'] = start_year
    if end_year is not None:
        years['endPeriod'] = end_year

    data_dimensions = _imf_parameters(database_id, times)

    if parameters is not None:
        for key in parameters:
            if key not in data_dimensions:
                raise ValueError(f"{key} not valid parameter(s) for the {database_id} database."
                                 f"Use _imf_parameters('{database_id}') to get valid parameters.")
            data_dimensions[key] = data_dimensions[key][data_dimensions[key]['input_code'].isin(parameters[key]['input_code'])]

    elif kwargs:
        for key in kwargs:
            if key not in data_dimensions:
                raise ValueError(f"{key} not valid parameter(s) for the {database_id} database."
                                 f"Use _imf_parameters('{database_id}') to get valid parameters.")
            data_dimensions[key] = data_dimensions[key][data_dimensions[key]['input_code'].isin(kwargs[key])]

    else:
        print("User supplied no filter parameters for the API request."
              "imf_dataset will attempt to request the entire database.")
        for key in data_dimensions:
            data_dimensions[key] = data_dimensions[key].iloc[0:0]

    parameter_string = '.'.join(['+'.join(data_dimensions[key]['input_code']) for key in data_dimensions])

    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/{database_id}/{parameter_string}"
    if years:
        url += f"?{urlencode(years)}"

    if print_url:
        print(url)

    raw_dl = _download_parse(url, times)['CompactData']['DataSet']['Series']
    if raw_dl is None:
        raise ValueError("No data found for that combination of parameters. Try making your request less restrictive.")

    if return_raw:
        if include_metadata:
            metadata = _imf_metadata(url=url)
            return metadata, raw_dl
        else:
            return raw_dl

    if isinstance(raw_dl['Obs'], list):
        data = []
        for i, obs in enumerate(raw_dl['Obs']):
            if isinstance(obs, list):
                df = pd.DataFrame(obs)
                df.columns = ['date', 'value']
            else:
                df = obs
                df.columns = ['date', 'value']

            tmp = pd.DataFrame({key.lower(): [raw_dl[key][i]] * len(df) for key in raw_dl if key != 'Obs'})
            data.append(pd.concat([df, tmp], axis=1))

        df = pd.concat(data)

    else:
        df = raw_dl['Obs']
        df.columns = ['date', 'value']
        tmp = pd.DataFrame({key.lower(): [raw_dl[key]] * len(df) for key in raw_dl if key != 'Obs'})
        df = pd.concat([df, tmp], axis=1)

    if not include_metadata:
        return df
    else:
        metadata = _imf_metadata(url=url)
        return metadata, df