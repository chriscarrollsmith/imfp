import pytest
from imfp import set_imf_app_name, set_imf_wait_time
import os


def test_set_imf_app_name():
    with pytest.warns(UserWarning):
        set_imf_app_name("")
    with pytest.warns(UserWarning):
        set_imf_app_name("imfp")

    with pytest.raises(ValueError):
        set_imf_app_name(None)
    with pytest.raises(ValueError):
        set_imf_app_name(float("nan"))
    with pytest.raises(ValueError):
        set_imf_app_name("z" * 256)
    with pytest.raises(ValueError):
        set_imf_app_name(["z", "z"])

    set_imf_app_name("imfr_admin_functions_tester")
    assert os.getenv("IMF_APP_NAME") == "imfr_admin_functions_tester"


@pytest.fixture
def env_setup_teardown():
    # Store the original value of the environment variable
    original_value = os.environ.get("IMF_WAIT_TIME", None)

    # Perform the test
    yield

    # Restore the original value of the environment variable after the test
    if original_value is not None:
        os.environ["IMF_WAIT_TIME"] = original_value
    else:
        os.environ.pop("IMF_WAIT_TIME", None)


def test_set_imf_wait_time(env_setup_teardown):
    # Test with valid input (int)
    set_imf_wait_time(5)
    assert os.environ["IMF_WAIT_TIME"] == "5"

    # Test with valid input (float)
    set_imf_wait_time(2.5)
    assert os.environ["IMF_WAIT_TIME"] == "2.5"

    # Test with invalid input (string)
    with pytest.raises(TypeError):
        set_imf_wait_time("some_string")

    # Test with invalid input (negative value)
    with pytest.raises(ValueError):
        set_imf_wait_time(-1)


if __name__ == "__main__":
    pytest.main()
