# imfp

[![Tests](https://github.com/chriscarrollsmith/imfp/actions/workflows/actions.yml/badge.svg)](https://github.com/chriscarrollsmith/imfp/actions/workflows/actions.yml)
[![PyPI Version](https://img.shields.io/pypi/v/imfp.svg)](https://pypi.python.org/pypi/imfp)

`imfp`, by Christopher C. Smith, is a Python package for downloading data from the [International Monetary
Fund's](http://data.imf.org/) [RESTful JSON
API](http://datahelp.imf.org/knowledgebase/articles/667681-using-json-restful-web-service).

## Installation

To install the stable version of imfp from PyPi, use pip.


```python
pip install -q --upgrade imfp
```

To load the library, use `import`:


```python
import imfp
```


## Usage

### Suggested packages

`imfp` outputs data in a `pandas` data frame, so you will want to use the `pandas` package for its functions for viewing and manipulating this object type. I also recommend `matplotlib` or `seaborn` for making plots, and `numpy` for computation. These packages can be installed using `pip` and loaded using `import`:


```python
import seaborn
```

### Setting a Unique Application Name with imf_app_name

`imfp.imf_app_name()` allows users to set a custom application name to be used when making API calls to the IMF API. The IMF API has an application-based rate limit of 50 requests per second, with the application identified by the "user_agent" variable in the request header.

This could prove problematic if the `imfp` library became too popular and too many users tried to make simultaneous API requests using the default app name. By setting a custom application name, users can avoid hitting rate limits and being blocked by the API. `imfp.imf_app_name()` sets the application name by changing the `IMF_APP_NAME` variable in the environment. If this variable doesn't exist, `imfp.imf_app_name()` will create it.

To set a custom application name, simply call the `imfp.imf_app_name()` function with your desired application name as an argument:


```python
# Set custom app name as an environment variable
imfp.imf_app_name("my_custom_app_name")
```



The function will throw an error if the provided name is missing, NULL, NA, not a string, or longer than 255 characters. If the provided name is "imfr" (the default) or an empty string, the function will issue a warning recommending the use of a unique app name to avoid hitting rate limits.

### Adjusting the rate limit with _imf_wait_time

During import of `imfp`, a variable called _imf_wait_time is set to a default value of 1.5. This is the mandatory enforced wait time between API calls, to prevent repeated or recursive calls from exceeding the limit. This wait time should be sufficient for most applications. However, if you are running parallel processes using `imfp` (e.g. during cross-platform testing), this wait time may be insufficient to prevent you from running up against the API's rate and bandwidth limits. You can increase this wait time by simply changing the variable value. For instance, to increase the between-call wait time by one second, use `_imf_wait_time += 1`.

Also note that by default, `imfp` functions will retry any API call rejected for bandwidth or rate limit reasons. The number of times `imfp` will attempt the call is set by the `times` argument, with a default value of 3. (With this value, requests will be retried twice after an initial failure.) Note that `imfp` enforces an exponentially increasing wait time between function calls, with a base wait time of 5 seconds on the first retry, so it is not recommended to set a high value for `times`.


### Fetching an Index of Databases with the imf_databases Function

The `imfp` package introduces four core functions: `imfp.imf_databases`, `imfp.imf_parameters`, `imfp.imf_parameter_defs`, and `imfp.imf_dataset`. The function for downloading datasets is `imfp.imf_dataset`, but you will need the other functions to determine what arguments to supply to `imfp.imf_dataset`. For instance, all calls to `imfp.imf_dataset` require a `database_id`. This is because the IMF serves many different databases through its API, and the API needs to know which of these many databases you're requesting data from. To obtain a list of databases, use `imfp.imf_databases`, like so:


```python
#Fetch the list of databases available through the IMF API
databases = imfp.imf_databases()
databases.head()
```




<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>database_id</th>
      <th>description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>BOP_2017M06</td>
      <td>Balance of Payments (BOP), 2017 M06</td>
    </tr>
    <tr>
      <th>1</th>
      <td>BOP_2020M3</td>
      <td>Balance of Payments (BOP), 2020 M03</td>
    </tr>
    <tr>
      <th>2</th>
      <td>BOP_2017M11</td>
      <td>Balance of Payments (BOP), 2017 M11</td>
    </tr>
    <tr>
      <th>3</th>
      <td>DOT_2020Q1</td>
      <td>Direction of Trade Statistics (DOTS), 2020 Q1</td>
    </tr>
    <tr>
      <th>4</th>
      <td>GFSMAB2016</td>
      <td>Government Finance Statistics Yearbook (GFSY 2...</td>
    </tr>
  </tbody>
</table>
</div>



This function returns the IMF’s listing of 259 databases available through the API. (In reality, 7 of the listed databases are defunct and not actually available: FAS_2015, GFS01, FM202010, APDREO202010, AFRREO202010, WHDREO202010, BOPAGG_2020.)

To view and explore the database list, it’s possible to explore subsets of the data frame by row number with `databases.loc`:



```python
# View a subset consisting of rows 5 through 9
databases.loc[5:9]
```




<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>database_id</th>
      <th>description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>5</th>
      <td>BOP_2019M12</td>
      <td>Balance of Payments (BOP), 2019 M12</td>
    </tr>
    <tr>
      <th>6</th>
      <td>GFSYFALCS2014</td>
      <td>Government Finance Statistics Yearbook (GFSY 2...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>GFSE2016</td>
      <td>Government Finance Statistics Yearbook (GFSY 2...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>FM201510</td>
      <td>Fiscal Monitor (FM) October 2015</td>
    </tr>
    <tr>
      <th>9</th>
      <td>GFSIBS2016</td>
      <td>Government Finance Statistics Yearbook (GFSY 2...</td>
    </tr>
  </tbody>
</table>
</div>




 Or, if you already know which database you want, you can fetch the corresponding code by searching for a string match using `str.contains` and subsetting the data frame for matching rows. For instance, here’s how to search for the Primary Commodity Price System:


```python
databases[databases['description'].str.contains("Commodity")]
```




<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>database_id</th>
      <th>description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>237</th>
      <td>PCTOT</td>
      <td>Commodity Terms of Trade</td>
    </tr>
    <tr>
      <th>239</th>
      <td>PCPS</td>
      <td>Primary Commodity Price System (PCPS)</td>
    </tr>
  </tbody>
</table>
</div>



### Fetching a List of Parameters and Input Codes with imf_parameters and imf_parameter_defs

Once you have a `database_id`, it’s possible to make a call to `imfp.imf_dataset` to fetch the entire database: `imfp.imf_dataset(database_id)`. However, while this will succeed for some small databases, it will fail for many of the larger ones. And even when it succeeds, fetching an entire database can take a long time. You’re much better off supplying additional filter parameters to reduce the size of your request.

Requests to databases available through the IMF API are complicated by the fact that each database uses a different set of parameters when making a request. (At last count, there were 43 unique parameters used in making API requests from the various databases!) You also have to have the list of valid input codes for each parameter. The `imfp.imf_parameters` function solves this problem. Use the function to obtain the full list of parameters and valid input codes for a given database:


```python
# Fetch list of valid parameters and input codes for commodity price database
params = imfp.imf_parameters("PCPS")
```

The `imfp.imf_parameters` function returns a dictionary of data frames. Each dictionary key name corresponds to a parameter used in making requests from the database:


```python
# Get key names from the params object
params.keys()
```




    dict_keys(['freq', 'ref_area', 'commodity', 'unit_measure'])



In the event that a parameter name is not self-explanatory, the `imfp.imf_parameter_defs` function can be used to fetch short text descriptions of each parameter:


```python
# Fetch and display parameter text descriptions for the commodity price database
imfp.imf_parameter_defs("PCPS")
```




<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>parameter</th>
      <th>description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>freq</td>
      <td>Frequency</td>
    </tr>
    <tr>
      <th>1</th>
      <td>ref_area</td>
      <td>Geographical Areas</td>
    </tr>
    <tr>
      <th>2</th>
      <td>commodity</td>
      <td>Indicator</td>
    </tr>
    <tr>
      <th>3</th>
      <td>unit_measure</td>
      <td>Unit</td>
    </tr>
  </tbody>
</table>
</div>



Each named list item is a data frame containing a vector of valid input codes that can be used with the named parameter, and a vector of text descriptions of what each code represents.

To access the data frame containing valid values for each parameter, subset the `params` dict by the parameter name:


```python
# View the data frame of valid input codes for the frequency parameter
params['freq']
```




<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>input_code</th>
      <th>description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>A</td>
      <td>Annual</td>
    </tr>
    <tr>
      <th>1</th>
      <td>M</td>
      <td>Monthly</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Q</td>
      <td>Quarterly</td>
    </tr>
  </tbody>
</table>
</div>



### Viewing Data Frames

Note that `pandas` data frames in Python can be a little difficult to work with, because Python doesn't have a built-in variable explorer. If you're doing data science, I recommend using an IDE like RStudio or Spyder that has a built-in variable explorer. However, if you don't have a variable explorer, you can prevent Python from truncating data frames using the `options` in `pandas`. For instance, to increase the maximum allowed column width to 100 characters, we can use `pandas.options.display.max_colwidth = 100`.

Alternatively, it's possible to open the data frame in a new window to view it in full:


```python
import imfp
import tempfile
import webbrowser

# Define a simple function to view data frame in a browser window
def View(df):
    html = df.to_html()
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html') as f:
        url = 'file://' + f.name
        f.write(html)
    webbrowser.open(url)

# Open data frame in a new browser window using the function
df = imfp.imf_databases()
View(df)
```

### Supplying Parameter Arguments to imf_dataset: A Tale of Two Workflows

There are two ways to supply parameters to `imfp.imf_dataset`: by supplying list arguments or by supplying a modified parameters dict. The list arguments workflow will be more intuitive for most users, but the dict argument workflow requires a little less code.

#### The List Arguments Workflow

To supply list arguments, just find the codes you want and supply them to `imfp.imf_dataset` using the parameter name as the argument name. The example below shows how to request 2000–2015 annual coal prices from the Primary Commodity Price System database:


```python
# Fetch the 'freq' input code for annual frequency
selected_freq = list(
    params['freq']['input_code'][params['freq']['description'].str.contains("Annual")]
)

# Fetch the 'commodity' input code for coal
selected_commodity = list(
    params['commodity']['input_code'][params['commodity']['description'].str.contains("Coal")]
)

# Fetch the 'unit_measure' input code for index
selected_unit_measure = list(
    params['unit_measure']['input_code'][params['unit_measure']['description'].str.contains("Index")]
)

# Request data from the API
df = imfp.imf_dataset(database_id = "PCPS",
         freq = selected_freq, commodity = selected_commodity,
         unit_measure = selected_unit_measure,
         start_year = 2000, end_year = 2015)

# Display the first few entries in the retrieved data frame
df.head()
```




<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>freq</th>
      <th>ref_area</th>
      <th>commodity</th>
      <th>unit_measure</th>
      <th>unit_mult</th>
      <th>time_format</th>
      <th>time_period</th>
      <th>obs_value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2000</td>
      <td>39.3510230293202</td>
    </tr>
    <tr>
      <th>1</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2001</td>
      <td>49.3378587284039</td>
    </tr>
    <tr>
      <th>2</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2002</td>
      <td>39.4949091648006</td>
    </tr>
    <tr>
      <th>3</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2003</td>
      <td>43.2878876950788</td>
    </tr>
    <tr>
      <th>4</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2004</td>
      <td>82.9185858052862</td>
    </tr>
  </tbody>
</table>
</div>



#### The Parameters Argument Workflow

To supply a list object, modify each data frame in the `params` list object to retain only the rows you want, and then supply the modified list object to `imfp.imf_dataset` as its parameters argument. Here is how to make the same request for annual coal price data using a parameters list:


```python
# Fetch the 'freq' input code for annual frequency
params['freq'] = params['freq'][params['freq']['description'].str.contains("Annual")]

# Fetch the 'commodity' input code(s) for coal
params['commodity'] = params['commodity'][params['commodity']['description'].str.contains("Coal")]

# Fetch the 'unit_measure' input code for index
params['unit_measure'] = params['unit_measure'][params['unit_measure']['description'].str.contains("Index")]

# Request data from the API
df = imfp.imf_dataset(database_id = "PCPS",
         parameters = params,
         start_year = 2000, end_year = 2015)

# Display the first few entries in the retrieved data frame
df.head()
```




<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>freq</th>
      <th>ref_area</th>
      <th>commodity</th>
      <th>unit_measure</th>
      <th>unit_mult</th>
      <th>time_format</th>
      <th>time_period</th>
      <th>obs_value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2000</td>
      <td>39.3510230293202</td>
    </tr>
    <tr>
      <th>1</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2001</td>
      <td>49.3378587284039</td>
    </tr>
    <tr>
      <th>2</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2002</td>
      <td>39.4949091648006</td>
    </tr>
    <tr>
      <th>3</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2003</td>
      <td>43.2878876950788</td>
    </tr>
    <tr>
      <th>4</th>
      <td>A</td>
      <td>W00</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2004</td>
      <td>82.9185858052862</td>
    </tr>
  </tbody>
</table>
</div>



### Working with the Returned Data Frame

Note that all columns in the returned data frame are character vectors, and that to plot the series we will need to convert to valid numeric or date formats. Using `seaborn` with `hue`, we can plot different indicators in different colors:


```python
# Convert obs_value to numeric and time_period to integer year
df = df.astype({"time_period" : int, "obs_value" : float})

# Plot prices of different commodities in different colors with seaborn
seaborn.lineplot(data=df, x='time_period', y='obs_value', hue='commodity');
```


    
![png](README_files/plot.png)
    



Also note that the returned data frame has mysterious-looking codes as values in some columns.

Codes in the `time_format` column are ISO 8601 duration codes. In this case, “P1Y” means “periods of 1 year.” The `unit_mult` column represents the number of zeroes you should add to the value column. For instance, if value is in millions, then the unit multiplier will be 6. If in billions, then the unit multiplier will be 9.

The meanings of the other codes are stored in our `params` object and can be fetched with a join. For instance to fetch the meaning of the `ref_area` code “W00”, we can perform a left join with the `params['ref_area']` data frame and use select to replace `ref_area` with the parameter description:


```python
# Join df with params['ref_area'] to fetch code description
df = df.merge(params['ref_area'], left_on='ref_area',right_on='input_code',how='left')

# Drop redundant columns and rename description column
df = df.drop(columns=['ref_area','input_code']).rename(columns={"description":"ref_area"})

# View first few columns in the modified data frame
df.head()
```




<div>

<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>freq</th>
      <th>commodity</th>
      <th>unit_measure</th>
      <th>unit_mult</th>
      <th>time_format</th>
      <th>time_period</th>
      <th>obs_value</th>
      <th>ref_area</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>A</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2000</td>
      <td>39.351023</td>
      <td>All Countries, excluding the IO</td>
    </tr>
    <tr>
      <th>1</th>
      <td>A</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2001</td>
      <td>49.337859</td>
      <td>All Countries, excluding the IO</td>
    </tr>
    <tr>
      <th>2</th>
      <td>A</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2002</td>
      <td>39.494909</td>
      <td>All Countries, excluding the IO</td>
    </tr>
    <tr>
      <th>3</th>
      <td>A</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2003</td>
      <td>43.287888</td>
      <td>All Countries, excluding the IO</td>
    </tr>
    <tr>
      <th>4</th>
      <td>A</td>
      <td>PCOAL</td>
      <td>IX</td>
      <td>0</td>
      <td>P1Y</td>
      <td>2004</td>
      <td>82.918586</td>
      <td>All Countries, excluding the IO</td>
    </tr>
  </tbody>
</table>
</div>


