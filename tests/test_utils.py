import sys
import os
import pytest

sys.path.insert(0, os.pardir)

from scripts.utils import _download_parse

def test_download_parse():
    # Test with a valid URL
    valid_url = "http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/BOP/A.US.BXSTVPO_BP6_USD?startPeriod=2020"
    valid_result = _download_parse(valid_url)
    assert isinstance(valid_result, dict)
    assert len(valid_result) == 1
    assert 'CompactData' in valid_result
    assert len(valid_result['CompactData']) == 6

    # Test with an invalid URL
    invalid_url = "http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/not_a_real_database/"
    with pytest.raises(ValueError):
        _download_parse(invalid_url)