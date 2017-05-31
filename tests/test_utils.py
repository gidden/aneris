import pandas as pd

from numpy.testing import assert_almost_equal
import nose.tools as nt
import pandas.util.testing as pdt

from aneris import utils


def test_remove_emissions_prefix():
    nt.assert_equal('foo', utils.remove_emissions_prefix('foo'))
    nt.assert_equal('foo', utils.remove_emissions_prefix('Emissions|XXX|foo'))
    nt.assert_equal('Emissions|bar|foo',
                    utils.remove_emissions_prefix('Emissions|bar|foo'))
    nt.assert_equal('foo', utils.remove_emissions_prefix(
        'Emissions|bar|foo', gas='bar'))


def test_region_agg_funky_name():
    df = pd.DataFrame({
        'sector': ['foo', 'foo'],
        'region': ['a', 'b'],
        '2010': [1.0, 4.0],
        'units': ['Mt'] * 2,
        'gas': ['BC'] * 2,
    }).set_index(utils.df_idx).sort_index()
    mapping = pd.DataFrame(
        [['fOO_Bar', 'a'], ['fOO_Bar', 'b']], columns=['x', 'y'])
    exp = pd.DataFrame({
        'sector': ['foo'],
        'region': ['fOO_Bar'],
        '2010': [5.0],
        'units': ['Mt'],
        'gas': ['BC'],
    }).set_index(utils.df_idx).sort_index()
    obs = utils.agg_regions(df, rfrom='y', rto='x', mapping=mapping)
    print(obs)
    pdt.assert_frame_equal(obs, exp)


def test_no_repeat_gases():
    gases = utils.all_gases
    pdt.assert_equal(len(gases), len(set(gases)))


def test_gases():
    var_col = pd.Series(['foo|Emissions|CH4|bar', 'Emissions|N2O|baz|zing'])
    exp = pd.Series(['CH4', 'N2O'])
    obs = utils.gases(var_col)
    pdt.assert_series_equal(obs, exp)


def test_units():
    var_col = pd.Series(['foo|Emissions|CH4|bar', 'Emissions|N2O|baz|zing'])
    exp = pd.Series(['Mt CH4/yr', 'kt N2O/yr'])
    obs = utils.units(var_col)
    pdt.assert_series_equal(obs, exp)


def test_formatter_to_std():
    df = pd.DataFrame({
        'Variable': [
            'CEDS+|9+ Sectors|Emissions|BC|foo|Unharmonized',
            'Emissions|BC|bar|baz',
        ],
        'Region': ['a', 'b'],
        '2010': [5.0, 2.0],
        '2020': [-1.0, 3.0],
        'Unit': ['Mt foo/yr'] * 2,
        'Model': ['foo'] * 2,
        'Scenario': ['foo'] * 2,
    })

    fmt = utils.FormatTranslator(df.copy())
    obs = fmt.to_std()
    exp = pd.DataFrame({
        'sector': [
            'CEDS+|9+ Sectors|foo|Unharmonized',
            'bar|baz',
        ],
        'region': ['a', 'b'],
        '2010': [5000.0, 2000.0],
        '2020': [-1000.0, 3000.0],
        'units': ['kt'] * 2,
        'gas': ['BC'] * 2,
    })
    pdt.assert_frame_equal(obs.set_index(utils.df_idx),
                           exp.set_index(utils.df_idx))


def test_formatter_to_template():
    df = pd.DataFrame({
        'Variable': [
            'CEDS+|9+ Sectors|Emissions|BC|foo|Unharmonized',
            'Emissions|BC|bar|baz',
        ],
        'Region': ['a', 'b'],
        '2010': [5.0, 2.0],
        '2020': [-1.0, 3.0],
        'Unit': ['Mt BC/yr'] * 2,
        'Model': ['foo'] * 2,
        'Scenario': ['foo'] * 2,
    }).set_index(utils.iamc_idx)
    fmt = utils.FormatTranslator(df)
    std = fmt.to_std()
    obs = fmt.to_template()
    exp = df.reindex_axis(obs.columns, axis=1)
    pdt.assert_frame_equal(obs, exp)


def combine_rows_df():
    df = pd.DataFrame({
        'sector': [
            '1A1a_Electricity-autoproducer',
            '1A1a_Electricity-public',
            '1A1a_Electricity-autoproducer',
            'extra_b',
            '1A1a_Electricity-autoproducer',
        ],
        'region': ['a', 'a', 'b', 'b', 'c'],
        '2010': [1.0, 4.0, 2.0, 21, 42],
        'foo': [-1.0, -4.0, 2.0, 21, 42],
        'units': ['Mt'] * 5,
        'gas': ['BC'] * 5,
    }).set_index(utils.df_idx)
    return df


def test_combine_rows_default():
    df = combine_rows_df()
    exp = pd.DataFrame({
        'sector': [
            '1A1a_Electricity-autoproducer',
            '1A1a_Electricity-public',
            'extra_b',
            '1A1a_Electricity-autoproducer',
        ],
        'region': ['a', 'a', 'a', 'c'],
        '2010': [3.0, 4.0, 21, 42],
        'foo': [1.0, -4.0, 21, 42],
        'units': ['Mt'] * 4,
        'gas': ['BC'] * 4,
    }).set_index(utils.df_idx)
    obs = utils.combine_rows(df, 'region', 'a', ['b'])
    pdt.assert_frame_equal(obs, exp.reindex_axis(obs.columns, axis=1))


def test_combine_rows_dropothers():
    df = combine_rows_df()
    exp = pd.DataFrame({
        'sector': [
            '1A1a_Electricity-autoproducer',
            '1A1a_Electricity-public',
            'extra_b',
            '1A1a_Electricity-autoproducer',
            'extra_b',
            '1A1a_Electricity-autoproducer',
        ],
        'region': ['a', 'a', 'a', 'b', 'b', 'c'],
        '2010': [3.0, 4.0, 21, 2.0, 21, 42],
        'foo': [1.0, -4.0, 21, 2.0, 21, 42],
        'units': ['Mt'] * 6,
        'gas': ['BC'] * 6,
    }).set_index(utils.df_idx)
    obs = utils.combine_rows(df, 'region', 'a', ['b'], dropothers=False)
    pdt.assert_frame_equal(obs, exp.reindex_axis(obs.columns, axis=1))


def test_combine_rows_sumall():
    df = combine_rows_df()
    exp = pd.DataFrame({
        'sector': [
            '1A1a_Electricity-autoproducer',
            'extra_b',
            '1A1a_Electricity-autoproducer',
        ],
        'region': ['a', 'a', 'c'],
        '2010': [2.0, 21, 42],
        'foo': [2.0, 21, 42],
        'units': ['Mt'] * 3,
        'gas': ['BC'] * 3,
    }).set_index(utils.df_idx)
    obs = utils.combine_rows(df, 'region', 'a', ['b'], sumall=False)
    pdt.assert_frame_equal(obs, exp.reindex_axis(obs.columns, axis=1))