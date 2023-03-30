from os import environ
from time import sleep, perf_counter
from requests import get
from json import loads, JSONDecodeError
from pandas import DataFrame
from pkg_resources import get_distribution, DistributionNotFound
import re


def _min_wait_time_limited(min_wait_time):
    def decorator(func):
        last_called = [0.0]

        def wrapper(*args, **kwargs):
            elapsed = perf_counter() - last_called[0]
            left_to_wait = min_wait_time - elapsed
            if left_to_wait > 0:
                sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = perf_counter()
            return ret

        return wrapper

    return decorator


@_min_wait_time_limited(1.5)  # 1.5 seconds wait time between calls
def _imf_get(url, headers):
    """
    A rate-limited wrapper around the requests.get method.
    
    Args:
        url (str): The URL to send a GET request to.
        headers (dict): The headers to use in the API request.
    
    Returns:
        requests.Response: The response object returned by requests.get.
        
    Usage:
        response = _imf_get(
                'http://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow'
            )
        print(response.text)
    """
    return get(url, headers)


def _download_parse(URL, times=2):
    """
    (Internal) Download and parse JSON content from a URL with rate limiting
    and retries.

    This function is rate-limited and will perform a specified number of
    retries in case of failure.

    Args:
        URL (str): The URL to download and parse the JSON content from.
        times (int, optional): The number of times to retry the request in case
        of failure. Defaults to 3.

    Returns:
        dict: The parsed JSON content as a Python dictionary.

    Raises:
        ValueError: If the content cannot be parsed as JSON after the specified
        number of retries.
    """

    app_name = environ.get("IMF_APP_NAME")
    if app_name:
        app_name = app_name[:255]
    else:
        try:
            app_name = f'imfp/{get_distribution("imfp").version}'
        except DistributionNotFound:
            app_name = 'imfp'

    headers = {'Accept': 'application/json', 'User-Agent': app_name}
    for _ in range(times):
        try:
            response = _imf_get(URL, headers=headers)
            content = response.text
            status = response.status_code
            json_parsed = loads(content)
            return json_parsed
        except JSONDecodeError:
            if ('Rejected' in content):
                if _ < times - 1:
                    sleep(5 ** (_ + 1))
                else:
                    matches = re.search("<[^>]+>(.*?)<\\/[^>]+>", content)
                    inner_text = matches.group(1)
                    output_string = re.sub(
                        " GKey\\s*=\\s*[a-f0-9-]+", "", inner_text
                    )
                    err_message = (f"API request failed. URL: '{URL}' "
                                   f"Status: '{status}', "
                                   f"Content: '{output_string}'\n\n"
                                   "API may be overwhelmed by too many "
                                   "requests. Take a break and try again.")
                    raise ValueError(err_message)
            else:
                matches = re.search("<[^>]+>(.*?)<\\/[^>]+>", content)
                inner_text = matches.group(1)
                output_string = re.sub(
                    " GKey\\s*=\\s*[a-f0-9-]+", "", inner_text
                )
                err_message = (f"API request failed. URL: '{URL}' "
                               f"Status: '{status}', "
                               f"Content: '{output_string}'")
                raise ValueError(err_message)


def _imf_dimensions(database_id, times=3, inputs_only=True):
    """
    (Internal) Retrieve the list of codes for dimensions of an individual IMF
    database.

    Args:
        database_id (str): The ID of the IMF database.
        times (int, optional): The number of times to retry the request in case
        of failure. Defaults to 3.
        inputs_only (bool, optional): If True, only include input parameters.
        Defaults to True.

    Returns:
        pandas.DataFrame: A DataFrame containing the parameter names and their
        corresponding codes and descriptions.
    """
    URL = (f'http://dataservices.imf.org/REST/SDMX_JSON.svc/DataStructure/'
           f'{database_id}')
    raw_dl = _download_parse(URL, times)

    code = []
    for item in raw_dl['Structure']['CodeLists']['CodeList']:
        code.append(item['@id'])
    description = []
    for item in raw_dl['Structure']['CodeLists']['CodeList']:
        description.append(item['Name']['#text'])
    codelist_df = DataFrame({'code': code, 'description': description})

    params = [
        dim['@conceptRef'].lower()
        for dim in (
            raw_dl['Structure']['KeyFamilies']['KeyFamily']['Components']
            ['Dimension']
        )
        ]
    codes = [
        dim['@codelist']
        for dim in (
            raw_dl['Structure']['KeyFamilies']['KeyFamily']['Components']
            ['Dimension']
        )
        ]
    param_code_df = DataFrame({'parameter': params, 'code': codes})

    if inputs_only:
        result_df = param_code_df.merge(codelist_df, on='code', how='left')
    else:
        result_df = param_code_df.merge(codelist_df, on='code', how='outer')

    return result_df


def _imf_metadata(URL, times=3):
    """
    (Internal) Access metadata for a dataset.

    Args:
        URL (str): The URL used to request metadata.
        times (int, optional): Maximum number of requests to attempt. Defaults
        to 3.

    Returns:
        dict: A dictionary containing the metadata information.

    Raises:
        ValueError: If the URL is not provided.

    Examples:
        # Find Primary Commodity Price System database metadata
        metadata = (
            imf_metadata("http://dataservices.imf.org/REST/SDMX_JSON.svc/"
            "GenericMetadata/PCPS/A..?start_year=2020")
        )
    """

    if not URL:
        raise ValueError("Must supply URL.")

    URL = URL.replace("CompactData", "GenericMetadata")
    raw_dl = _download_parse(URL, times=times)

    output = {
        "XMLschema": raw_dl["GenericMetadata"]["@xmlns:xsd"],
        "message": raw_dl["GenericMetadata"]["@xsi:schemaLocation"],
        "language": (
            raw_dl["GenericMetadata"]["Header"]["Sender"]["Name"]["@xml:lang"]
        ),
        "timestamp": raw_dl["GenericMetadata"]["Header"]["Prepared"],
        "custodian": (
            raw_dl["GenericMetadata"]["Header"]["Sender"]["Name"]["#text"]
        ),
        "custodian_url": (
            raw_dl["GenericMetadata"]["Header"]["Sender"]["Contact"]["URI"]
        ),
        "custodian_telephone": (
            raw_dl["GenericMetadata"]["Header"]["Sender"]["Contact"]
            ["Telephone"]
        )
    }
    return output
