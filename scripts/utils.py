import os
import time
import requests
import json
import functools
from ratelimiter import RateLimiter
from pkg_resources import get_distribution

def rate_limited(rate_limit):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with rate_limit:
                return func(*args, **kwargs)
        return wrapper
    return decorator

rate_limit = RateLimiter(max_calls=5, period=5)


@rate_limited(rate_limit)
def download_parse(URL, times=3):
    app_name = os.environ.get("IMF_APP_NAME")
    if app_name:
        app_name = app_name[:255]
    else:
        app_name = f'imfr/{get_distribution("imfr").version}'

    headers = {'Accept': 'application/json', 'User-Agent': app_name}
    for _ in range(times):
        response = requests.get(URL, headers=headers)
        content = response.text
        status = response.status_code

        if ('<!DOCTYPE HTML PUBLIC' in content or
            '<!DOCTYPE html in content or
            '<string xmlns="http://schemas.m' in content or
            '<html xmlns=' in content):
            err_message = (f"API request failed. URL: '{URL}', Status: '{status}', "
                           f"Content: '{content[:30]}'")
            raise ValueError(err_message)

        try:
            json_parsed = json.loads(content)
            return json_parsed
        except json.JSONDecodeError:
            if _ < times - 1:
                time.sleep(2 ** (_ + 1))
            else:
                raise