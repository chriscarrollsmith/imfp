import sys
import os
import pandas as pd
import warnings

sys.path.insert(0, os.pardir)

from scripts.utils import _download_parse, _imf_dimensions, _imf_metadata
from urllib.parse import urlencode
from typing import Union, Dict, Tuple


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
            if isinstance(raw,list):
                return pd.DataFrame({"input_code": [code['@value'] for code in raw],
                                    "description": [code['Description']['#text'] for code in raw]})
            else:
                return pd.DataFrame({"input_code": [raw['@value']],
                                    "description": [raw['Description']['#text']]})

    parameter_list = {codelist.loc[k, 'parameter']: fetch_parameter_data(k, url, times)
                      for k in range(codelist.shape[0])}

    return parameter_list


def imf_parameter_defs(database_id, times=3, inputs_only=True):
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
    try:
        parameterlist = _imf_dimensions(database_id, times, inputs_only)[['parameter', 'description']]
    except Exception as e:
        if 'There is an issue' in str(e):
            raise ValueError(f"{e}\n\nDid you supply a valid database_id? Use imf_databases to find.")
        else:
            raise ValueError(e)

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
        try:
            start_year = str(start_year)
            if start_year.isdigit() and len(start_year) == 4:
                years['startPeriod'] = start_year
            else:
                raise ValueError("start_year must be a four-digit number, either integer or string")
        except:
            raise ValueError("start_year must be a four-digit number, either integer or string")
    if end_year is not None:
        try:
            end_year = str(end_year)
            if end_year.isdigit() and len(end_year) == 4:
                years['endPeriod'] = end_year
            else:
                raise ValueError("end_year must be a four-digit number, either integer or string")
        except:
            raise ValueError("end_year must be a four-digit number, either integer or string")

    data_dimensions = imf_parameters(database_id, times)

    if parameters is not None:
        for key in parameters:
            if key not in data_dimensions:
                raise ValueError(f"{key} not valid parameter(s) for the {database_id} database. "
                                 f"Use imf_parameters('{database_id}') to get valid parameters.")
            invalid_keys = []
            for x in list(parameters[key]['input_code']):
                if x not in list(data_dimensions[key]['input_code']):
                    invalid_keys.append(x)
            if len(invalid_keys) > 0:
                warnings.warn(f"{invalid_keys} not valid value(s) for {key} and will be ignored. "
                              f"Use imf_parameters('{database_id}') to get valid parameters.")
            data_dimensions[key] = data_dimensions[key].iloc[[index for index, x in enumerate(data_dimensions[key]['input_code']) if x in list(parameters[key]['input_code'])]]

    elif kwargs:
        for key in kwargs:
            if key not in data_dimensions:
                raise ValueError(f"{key} not valid parameter(s) for the {database_id} database. "
                                 f"Use imf_parameters('{database_id}') to get valid parameters.")
            invalid_vals = []
            if not isinstance(kwargs[key],list):
                kwargs[key] = [kwargs[key]]
            for x in kwargs[key]:
                if x not in data_dimensions[key]['input_code'].tolist():
                    invalid_vals.append(x)
            if len(invalid_vals) > 0:
                warnings.warn(f"{invalid_vals} not valid value(s) for {key} and will be ignored. "
                              f"Use imf_parameters('{database_id}') to get valid parameters.")
            data_dimensions[key] = data_dimensions[key].iloc[[index for index, x in enumerate(data_dimensions[key]['input_code']) if x in kwargs[key]]]

    else:
        print("User supplied no filter parameters for the API request. "
              "imf_dataset will attempt to request the entire database.")
        for key in data_dimensions:
            data_dimensions[key] = data_dimensions[key].iloc[0:0]

    parameter_string = '.'.join(['+'.join(data_dimensions[key]['input_code']) for key in data_dimensions])

    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/{database_id}/{parameter_string}"
    if years:
        url += f"?{urlencode(years)}"

    if print_url:
        print(url)

    raw_dl = _download_parse(url, times)['CompactData']['DataSet']
    try:
        raw_dl = raw_dl['Series']
    except:
        raise ValueError("No data found for that combination of parameters. Try making your request less restrictive.")
    if raw_dl is None:
        raise ValueError("No data found for that combination of parameters. Try making your request less restrictive.")

    if return_raw:
        if include_metadata:
            metadata = _imf_metadata(url)
            return metadata, raw_dl
        else:
            return raw_dl

    # Function to check if a value is a scalar
    def is_scalar(value):
        return not isinstance(value, (list, tuple, set, pd.Series))
    
    # Function to return dictionary without 'Obs'
    def without_obs(d, keys={"Obs"}):
        return {x: d[x] for x in d if x not in keys}
    
    # Check if raw_dl is a list, and if not, convert it to one
    if not isinstance(raw_dl,list):
        raw_dl = [raw_dl]

    def process_data(item):
       
        # Make a data frame of dict items excluding 'Obs'
        if all(is_scalar(value) for value in without_obs(item).values()):
            param_vals = pd.DataFrame.from_dict([without_obs(item)])
        else:
            raise ValueError("Expected item to be scalar, but it's not.")
        
        # Make a data frame from the dicts in 'Obs'
        if not isinstance(item['Obs'], list):
            item['Obs'] = [item['Obs']]
        series = pd.DataFrame.from_dict(item['Obs'])
            
        # Create a copy of param_vals for every row in series
        param_vals = pd.concat([param_vals]*len(series)).reset_index(drop=True)

        #Column bind param_vals to series
        output = pd.concat([param_vals, series],axis=1)
        return output
    
    result = pd.concat(list(map(process_data,raw_dl)))
    result.columns = result.columns.str.replace("@","")
    result.columns = result.columns.str.lower()

    if not include_metadata:
        return result
    else:
        metadata = _imf_metadata(url)
        return metadata, result