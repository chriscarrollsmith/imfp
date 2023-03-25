import pytest
from scripts.admin_functions import imf_app_name
import os

def test_imf_app_name():
    with pytest.warns(UserWarning):
        imf_app_name("")
    with pytest.warns(UserWarning):
        imf_app_name("imfr")
    with pytest.warns(UserWarning):
        imf_app_name("z" * 2)
    
    with pytest.raises(ValueError):
        imf_app_name(None)
    with pytest.raises(ValueError):
        imf_app_name(float('nan'))
    with pytest.raises(ValueError):
        imf_app_name("z" * 256)
    
    imf_app_name("imfr_admin_functions_tester")
    assert os.getenv("IMF_APP_NAME") == "imfr_admin_functions_tester"