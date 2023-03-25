import pytest
from scripts.data_functions import imf_databases, imf_parameters, imf_parameter_defs

class TestIMFDatabase:

    def test_imf_databases(self):
        assert len(imf_databases()) > 1

    def test_imf_parameters(self):
        params = imf_parameters("BOP")
        assert all(params['input_code'] == ['A', 'M', 'Q']) == True
        with pytest.raises(Exception):
            imf_parameters(times=1)
        with pytest.raises(Exception):
            imf_parameters(database_id="not_a_real_database", times=1)

    def test_imf_parameter_defs(self):
        assert len(imf_parameter_defs("BOP_2017M08")) > 1
        with pytest.raises(Exception):
            imf_parameter_defs(times=1)
        with pytest.raises(Exception):
            imf_parameters("not_a_real_database", times=1)

    def test_imf_dataset_error_handling(self):
        params = imf_parameters("FISCALDECENTRALIZATION")
        params['freq'] = params['freq'][0:1]
        params['ref_area'] = params['ref_area'][0:1]
        params['indicator'] = params['indicator'][params['indicator'] == "edu"]
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
            imf_dataset(database_id="WHDREO201910", freq="M", ref_area="US", indicator=["PPPSH", "NGDPD"], start_year=2010, end_year=2011, times=3)
        with pytest.warns(Warning):
            imf_dataset(database_id="FISCALDECENTRALIZATION", parameters=params, ref_sector=["1C_CG", "1C_LG"])

    def test_imf_dataset_params_list_request(self):
        params = {
            'freq': {'input_code': 'A', 'description': 'blah'},
            'ref_area': {'input_code': 'US', 'description': 'blah'},
            'ref_sector': {'input_code': 'S13', 'description': 'blah'},
            'classification': {'input_code': ['W0_S1_G1151', 'W0_S1_G1412'], 'description': ['blah']}
        }
        df = imf_dataset(database_id="GFSR2019", parameters=params, start_year=2001, end_year=2002, times=5)
        assert len(df) > 1
        assert all(int(date) >= 2001 and int(date) <= 2002 for date in df['date'])
        assert all(ref_sector == "S13" for ref_sector in df['ref_sector'])

    def test_imf_dataset_vector_parameters_request(self):
        df = imf_dataset(database_id="AFRREO", indicator=["TTT_IX", "GGX_G01_GDP_PT"], ref_area="7A", start_year=2021)
        assert len(df) > 1
        assert all(int(date) >= 2021 for date in df['date'])
        assert all(indicator in ["TTT_IX", "GGX_G01_GDP_PT"] for indicator in df['indicator'])

    def test_imf_dataset_data_frame_prep(self):
        if_condition = imf_dataset(database_id="WHDREO201910", freq="A", ref_area="US", indicator=["PPPSH", "NGDPD"], start_year=2010, end_year=2012)
        else_if_condition = imf_dataset(database_id="WHDREO201910", freq="A", ref_area="US", indicator=["PPPSH", "NGDPD"], start_year=2010, end_year=2011)
        else_condition = imf_dataset(database_id="WHDREO201910", freq="A", ref_area="US", indicator=["NGDPD"], start_year=2011, end_year=2012)

        desired_names = ["date", "value", "freq", "ref_area", "indicator", "unit_mult", "time_format"]

        assert len(if_condition) == 4 and len(else_if_condition) == 2 and len(else_condition) == 2
        assert len(if_condition.columns) == 7 and len(else_if_condition.columns) == 7 and len(else_condition.columns) == 7
        assert all(col in desired_names for col in if_condition.columns) and \
               all(col in desired_names for col in else_if_condition.columns) and \
               all(col in desired_names for col in else_condition.columns)

    def test_imf_dataset_include_metadata(self):
        output = imf_dataset(database_id="WHDREO201910", freq="A", ref_area="US", indicator=["PPPSH", "NGDPD"], start_year=2010, end_year=2012, include_metadata=True)
        assert isinstance(output, list)
        assert len(output) == 2
        assert isinstance(output[0], list)
        assert isinstance(output[1], list)
        assert all(not any(pd.isna(data)) for data in output[0])

if __name__ == '__main__':
    pytest.main()