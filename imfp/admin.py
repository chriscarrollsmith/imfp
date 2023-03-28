from os import environ
from warnings import warn


def imf_app_name(name="imfp"):
    """
    Set the IMF Application Name.

    Set a unique application name to be used in requests to the IMF API as an
    environment variable.

    Args:
        name (str, optional): A string representing the application name.
        Default is "imfp".

    Returns:
        None

    Raises:
        ValueError: If the provided name is not a valid string or contains
        forbidden characters.

    Examples:
        imf_app_name("my_custom_app_name")
    """

    if not isinstance(name, str) or len(name) > 255:
        raise ValueError("Please provide a valid string as the application "
                         "name (max length: 255 characters).")

    if name == "imfp" or name == "":
        warn("Best practice is to choose a unique app name. Use of a default "
             "or empty app name may result in hitting API rate limits and "
             "being blocked by the API.", UserWarning)

    forbidden_chars = set(range(32)) | {127}
    if any(ord(c) in forbidden_chars for c in name):
        raise ValueError("The application name contains forbidden characters. "
                         "Please remove control characters and non-printable "
                         "ASCII characters.")

    environ["IMF_APP_NAME"] = name

    return None
