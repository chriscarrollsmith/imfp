import pytest
import responses
import time
import pandas as pd
import os
from imfp import (
    _imf_get,
    _download_parse,
    _imf_metadata,
    _imf_dimensions,
    set_imf_wait_time,
)
from imfp.utils import _imf_save_response, _imf_use_cache


# Set test configuration options
create_cache = False
use_cache = True
wait_time = 0


@pytest.fixture
def set_options(monkeypatch):
    # Create the responses directory if it doesn't exist
    os.makedirs("tests/responses", exist_ok=True)

    # Store the original values of the options
    original_save_response = _imf_save_response
    original_use_cache = _imf_use_cache
    original_wait_time = os.environ.get("IMF_WAIT_TIME", None)

    # Set caching options for response mocking
    monkeypatch.setattr("imfp.utils._imf_save_response", create_cache)
    monkeypatch.setattr("imfp.utils._imf_use_cache", use_cache)
    set_imf_wait_time(wait_time)

    # Perform the test
    yield float(os.environ.get("IMF_WAIT_TIME"))

    # Restore the original values of the options during teardown
    monkeypatch.setattr("imfp.utils._imf_save_response", original_save_response)
    monkeypatch.setattr("imfp.utils._imf_use_cache", original_use_cache)
    if original_wait_time is not None:
        os.environ["IMF_WAIT_TIME"] = original_wait_time
    else:
        os.environ.pop("IMF_WAIT_TIME", None)


@pytest.fixture
def env_setup_teardown():
    # Store the original value of the environment variable
    original_value = os.environ.get("IMF_WAIT_TIME", None)

    # Set the environment variable for the test
    os.environ["IMF_WAIT_TIME"] = "2.5"

    # Perform the test
    yield original_value

    # Restore the original value of the environment variable after the test
    if original_value is not None:
        os.environ["IMF_WAIT_TIME"] = original_value
    else:
        os.environ.pop("IMF_WAIT_TIME", None)


@responses.activate
def test_imf_get(env_setup_teardown):
    # Check if the new value is larger than the default value (1.5) or the original value if it exists
    original_value = env_setup_teardown
    if original_value:
        assert float(original_value) <= float(os.environ["IMF_WAIT_TIME"])
    else:
        assert 1.5 <= float(os.environ["IMF_WAIT_TIME"])

    # Define a mock URL and response
    mock_url = "https://example.com/"
    mock_response_text = "Example Domain"
    mock_header = {"Accept": "application/json", "User-Agent": "imfp"}

    # Add the mock response to the responses library
    responses.add(responses.GET, mock_url, body=mock_response_text, status=200)

    # Call the _imf_get function and assert that the response text
    # matches the mock response
    response = _imf_get(mock_url, mock_header)
    assert response.text == mock_response_text

    # Test the rate-limiting functionality by checking the elapsed time
    # between two requests
    start_time = time.perf_counter()
    _imf_get(mock_url, mock_header)
    _imf_get(mock_url, mock_header)
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    # The elapsed time should be at least the minimum set in the environ variable
    assert elapsed_time >= float(os.environ["IMF_WAIT_TIME"])


def test_download_parse(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    # Test with a valid URL
    valid_url = (
        "http://dataservices.imf.org/REST/SDMX_JSON.svc/"
        "CompactData/BOP/A.US.BXSTVPO_BP6_USD?startPeriod=2020"
    )
    valid_result = _download_parse(valid_url)
    assert isinstance(valid_result, dict)
    assert len(valid_result) == 1
    assert "CompactData" in valid_result
    assert len(valid_result["CompactData"]) == 6

    # Test with an invalid URL
    invalid_url = (
        "http://dataservices.imf.org/REST/SDMX_JSON.svc/"
        "CompactData/not_a_real_database/"
    )
    with pytest.raises(ValueError):
        _download_parse(invalid_url)


def test_imf_metadata_valid_url(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    URL = (
        "http://dataservices.imf.org/REST/SDMX_JSON.svc/"
        "CompactData/BOP/A.US.BXSTVPO_BP6_USD?startPeriod=2020"
    )
    metadata = _imf_metadata(URL)

    assert isinstance(metadata, dict)
    assert len(metadata) == 7
    assert all(value != "NA" for value in metadata.values())


def test_imf_metadata_invalid_url(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    URL = (
        "http://dataservices.imf.org/REST/"
        "SDMX_JSON.svc/CompactData/not_a_real_database/"
    )

    with pytest.raises(Exception):
        _imf_metadata(URL)


def test_imf_metadata_empty_url(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    URL = ""

    with pytest.raises(ValueError):
        _imf_metadata(URL)


def test_imf_dimensions_valid_database_id(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    database_id = "PCPS"
    dimensions = _imf_dimensions(database_id)

    assert isinstance(dimensions, pd.DataFrame)
    assert dimensions.shape == (4, 3)
    assert dimensions.isna().sum().sum() == 0


def test_imf_dimensions_invalid_database_id(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    database_id = "not_a_real_database_id"

    with pytest.raises(Exception):
        _imf_dimensions(database_id)


def test_imf_dimensions_times_param(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    database_id = "PCPS"
    dimensions = _imf_dimensions(database_id, times=2)

    assert isinstance(dimensions, pd.DataFrame)
    assert dimensions.shape == (4, 3)
    assert dimensions.isna().sum().sum() == 0


def test_imf_dimensions_inputs_only_param(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    database_id = "PCPS"
    dimensions_1 = _imf_dimensions(database_id, inputs_only=True)
    dimensions_2 = _imf_dimensions(database_id, inputs_only=False)

    assert isinstance(dimensions_1, pd.DataFrame)
    assert isinstance(dimensions_2, pd.DataFrame)
    assert dimensions_1.shape == (4, 3)
    assert dimensions_2.shape == (6, 3)
    assert dimensions_1.isna().sum().sum() == 0
    assert dimensions_2.isna().sum().sum() == 2


def test_bad_request(set_options):
    assert (wait_time - 0.1) < set_options < (wait_time + 0.1)

    URL = "http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/BOP_2017M06/A+M+Q.AF+AL+DZ+AO+AI+AG+AR+AM+AW+AU+AT+AZ+BS+BH+BD+BB+BY+BE+R1+BZ+BJ+BM+BT+BO+BA+BW+BR+BN+BG+BF+BI+KH+CM+CA+CV+CF+TD+CL+HK+MO+CN+CO+KM+CD+CG+CR+CI+HR+CW+1C_355+CY+CZ+CSH+DK+DJ+DM+DO+5Y+EC+EG+SV+GQ+ER+EE+ET+U2+FO+FJ+FI+FR+PF+NC+GA+GM+GE+DE+GH+GR+GD+GT+GN+GW+GY+HT+HN+HU+IS+IN+ID+IR+IQ+IE+IL+IT+JM+JP+JO+KZ+KE+KI+KR+XK+KW+KG+LA+LV+LB+LS+LR+LY+LT+LU+MK+MG+MW+MY+MV+ML+MT+MH+MR+MU+MX+FM+MD+MN+ME+MS+MA+MZ+MM+NA+NP+NL+AN+NZ+NI+NE+NG+NO+OM+PK+PW+PA+PG+PY+PE+PH+PL+PT+QA+RO+RU+RW+WS+ST+SA+SN+RS+SC+SL+SG+SX+SK+SI+SB+SO+ZA+SS+ES+LK+KN+LC+VC+SD+SR+SZ+SE+CH+SY+TW+TJ+TZ+TH+TL+TG+TO+TT+TN+TR+TM+TV+UG+UA+GB+US+UY+VU+VE+VN+PS+1C_473+1C_459+YE+YUC+ZM+ZW+BOP_Reporters+All_Countries+IIP_Reporters.IADDF_BP6_EUR"

    with pytest.raises(ValueError) as excinfo:
        _download_parse(URL)

    assert "Too many parameters supplied" in str(excinfo.value)

    URL = "http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/BOP_2017M06/.."

    with pytest.raises(ValueError) as excinfo:
        _download_parse(URL)

    assert "too large" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main()
