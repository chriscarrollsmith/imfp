# This script tries to download whole databases indicator by indicator

import imfp

# Examine database list
databases = imfp.imf_databases()

# Set a custom wait time and a database to query
_imf_wait_time = 10
database_to_download = "IFS"

# Try to download the database indicator by indicator (Note that some databases don't
# use the 'indicator' parameter, so this won't work with every database)
indicators = imfp.imf_parameters("IFS")["indicator"]
datasets = {"indicator_names": [], "dataframes": []}
for indicator in indicators["input_code"]:
    datasets["indicator_names"].append(indicator)
    try:
        datasets["dataframes"].append(
            imfp.imf_dataset(database_id=database_to_download, indicator=indicator)
        )
    except Exception as e:
        datasets["dataframes"].append(None)
        print("An error occurred when downloading", indicator, ": ", e)
