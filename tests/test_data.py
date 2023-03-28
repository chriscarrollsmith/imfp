import pytest
import pandas as pd
from imfp import imf_databases, imf_parameters, imf_parameter_defs, imf_dataset


def test_imf_databases():
    result = imf_databases()
    assert isinstance(result, pd.DataFrame), 'Result should be a pandas DataFrame'
    expected_column_names = ['database_id', 'description']
    assert list(result.columns) == expected_column_names, 'Result should have the expected column names'
    assert result.isna().sum().sum() == 0, 'Result should not contain any NAs'
    assert len(result['database_id']) == len(result['description']), 'Both columns should have the same length'

def test_imf_parameter_defs():
    result = imf_parameter_defs("BOP_2017M08")
    assert isinstance(result, pd.DataFrame), 'Result should be a pandas DataFrame'
    assert result.shape[0] == 3, 'Result should have 3 rows'
    assert result.shape[1] == 2, 'Result should have 2 columns'
    expected_column_names = ['parameter', 'description']
    assert list(result.columns) == expected_column_names, 'Result should have the expected column names'

    result = imf_parameter_defs("BOP_2017M08",inputs_only=False)
    assert isinstance(result, pd.DataFrame), 'Result should be a pandas DataFrame'
    assert result.shape[0] == 5, 'Result should have 5 rows'
    assert result.shape[1] == 2, 'Result should have 2 columns'
    expected_column_names = ['parameter', 'description']
    assert list(result.columns) == expected_column_names, 'Result should have the expected column names'
    
    with pytest.raises(Exception):
        imf_parameter_defs(times=1)
    with pytest.raises(Exception):
        imf_parameters("not_a_real_database", times=1)

def test_imf_parameters():
    params = imf_parameters("BOP")
    assert all(params['freq']['input_code'] == ['A', 'M', 'Q']) == True
    with pytest.raises(Exception):
        imf_parameters(times=1)
    with pytest.raises(Exception):
        imf_parameters(database_id="not_a_real_database", times=1)

def test_imf_dataset_error_handling():
    params = imf_parameters("FISCALDECENTRALIZATION")
    params['freq'] = params['freq'][0:1]
    params['ref_area'] = params['ref_area'][5:10]
    params['indicator'] = params['indicator'].iloc[[index for index, x in enumerate(params['indicator']['input_code']) if "edu" in x]]
    params['ref_sector'] = params['ref_sector'][0:1]
    with pytest.raises(Exception):
        imf_dataset(database_id="APDREO201904", counterpart_area="X", counterpart_sector="X", times=1)
    with pytest.warns(Warning):
        imf_dataset(database_id="APDREO201904", ref_area="AU", indicator=["BCA_BP6_USD", "XYZ"])
    with pytest.raises(Exception):
        imf_dataset(times=1)
    with pytest.raises(Exception):
        imf_dataset(database_id=2, times=1)
    with pytest.raises(Exception):
        imf_dataset(database_id=[], times=1)
    with pytest.raises(Exception):
        imf_dataset(database_id=["a", "b"], times=1)
    with pytest.raises(Exception):
        imf_dataset(database_id="not_a_real_database", times=1)
    with pytest.raises(Exception):
        imf_dataset(database_id="PCPS", start_year=1, times=1)
    with pytest.raises(Exception):
        imf_dataset(database_id="PCPS", end_year="a", times=1)
    with pytest.raises(Exception):
        imf_dataset(database_id="PCPS", end_year=[1999, 2004], times=1)
    with pytest.raises(Exception):
        imf_dataset(database_id="WHDREO201910", freq="M", ref_area="US", indicator=["PPPSH", "NGDPD"], start_year=2010, end_year=2011)
    with pytest.warns(Warning):
        imf_dataset(database_id="FISCALDECENTRALIZATION", parameters=params, ref_sector=["1C_CG", "1C_LG"])

def test_imf_dataset_params_list_request():
    params = imf_parameters("GFSR2019")
    params['freq'] = params['freq'].iloc[[index for index, x in enumerate(params['freq']['input_code']) if "A" in x]]
    params['ref_area'] = params['ref_area'].iloc[[index for index, x in enumerate(params['ref_area']['input_code']) if "US" in x]]
    params['classification'] = params['classification'].iloc[[index for index, x in enumerate(params['classification']['input_code']) if x in ['W0_S1_G1151', 'W0_S1_G1412']]]
    params['ref_sector'] = params['ref_sector'].iloc[[index for index, x in enumerate(params['ref_sector']['input_code']) if x in "S13"]]
    df = imf_dataset(database_id="GFSR2019", parameters=params, start_year=2001, end_year=2002)
    assert len(df) > 1
    assert all(int(date) >= 2001 and int(date) <= 2002 for date in df['time_period'])
    assert all(ref_sector == "S13" for ref_sector in df['ref_sector'])

def test_imf_dataset_vector_parameters_request():
    df = imf_dataset(database_id="AFRREO", indicator=["TTT_IX", "GGX_G01_GDP_PT"], ref_area="7A", start_year=2021)
    assert len(df) > 1
    assert all(int(date) >= 2021 for date in df['time_period'])
    assert all(indicator in ["TTT_IX", "GGX_G01_GDP_PT"] for indicator in df['indicator'])

def test_imf_dataset_data_frame_prep():
    case_1 = imf_dataset(database_id="WHDREO201910", freq="A", ref_area="US", indicator=["PPPSH", "NGDPD"], start_year=2010, end_year=2012)
    case_2 = imf_dataset(database_id="WHDREO201910", freq="A", ref_area="US", indicator=["PPPSH", "NGDPD"], start_year=2010, end_year=2011)
    case_3 = imf_dataset(database_id="WHDREO201910", freq="A", ref_area="US", indicator=["NGDPD"], start_year=2011, end_year=2012)

    desired_names = ["time_period", "obs_value", "freq", "ref_area", "indicator", "unit_mult", "time_format"]

    assert len(case_1) == 4 and len(case_2) == 2 and len(case_3) == 2
    assert len(case_1.columns) == 7 and len(case_2.columns) == 7 and len(case_3.columns) == 7
    assert all(col in desired_names for col in case_1.columns) and \
            all(col in desired_names for col in case_2.columns) and \
            all(col in desired_names for col in case_3.columns)

def test_imf_dataset_include_metadata():
    output = imf_dataset(database_id="WHDREO201910", freq="A", ref_area="US", indicator=["PPPSH", "NGDPD"], start_year=2010, end_year=2012, include_metadata=True)
    assert isinstance(output, tuple)
    assert len(output) == 2
    assert isinstance(output[0], dict)
    assert isinstance(output[1], pd.core.frame.DataFrame)
    assert all([not pd.isna(value) for value in output[0].values()])

if __name__ == '__main__':
    pytest.main()