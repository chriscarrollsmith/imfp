import pytest
from imfp import imf_app_name
import os

def test_imf_app_name():
    with pytest.warns(UserWarning):
        imf_app_name("")
    with pytest.warns(UserWarning):
        imf_app_name("imfr")
    
    with pytest.raises(ValueError):
        imf_app_name(None)
    with pytest.raises(ValueError):
        imf_app_name(float('nan'))
    with pytest.raises(ValueError):
        imf_app_name("z" * 256)
    with pytest.raises(ValueError):
        imf_app_name(["z","z"])
    
    imf_app_name("imfr_admin_functions_tester")
    assert os.getenv("IMF_APP_NAME") == "imfr_admin_functions_tester"


if __name__ == '__main__':
    pytest.main()