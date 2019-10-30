import pytest
import os

import pandas as pd
from pandas.util.testing import assert_frame_equal

from aneris import cli


# TODO: utilize this for regression or take it out completely
# # decorator for slow-running tests
# slow = pytest.mark.skipif(
#     not pytest.config.getoption("--runslow"),
#     reason="need --runslow option to run"
# )


# This is a class that runs all tests through the harmonize CLI Note that it
# uses the actual harmonize API rather than subprocessing the CLI because
# coveralls does not pick up the lines covered in CLI calls when in a docker
# container.
#
# I don't know why. I spent 4+ hours digging. I am done. I hope I never have to
# worry about this again.
class TestHarmonizeRegression():

    def _run(self, prefix, inf, checkf, hist='history.csv', reg='message.csv'):
        # path setup
        here = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        prefix = os.path.join(here, prefix)
        add_prefix = lambda f: os.path.join(prefix, f)

        # get all arguments
        hist = add_prefix(hist)
        reg = add_prefix(reg)
        rc = add_prefix('aneris.yaml')
        inf = add_prefix(inf)
        outf = add_prefix('test_harmonized.xlsx')
        if os.path.exists(outf):
            os.remove(outf)

        # run
        print(inf, hist, reg, rc, prefix, 'test')
        cli.harmonize(inf, hist, reg, rc, prefix, 'test')

        # test
        xfile = os.path.join(prefix, checkf)
        x = pd.read_excel(xfile, sheet_name='data')
        y = pd.read_excel(outf, sheet_name='data')
        assert_frame_equal(x, y)

        clean = [
            outf,
            add_prefix('test_metadata.xlsx'),
            add_prefix('test_diagnostics.xlsx'),
        ]
        for f in clean:
            if os.path.exists(f):
                os.remove(f)

    def test_basic_run(self):
        prefix = 'test_data'
        inf = 'model.xls'
        checkf = 'test_basic_run.xlsx'
        self._run(prefix, inf, checkf, hist='history.xls', reg='regions.csv')

    # TODO: utilize this for regression or take it out completely
    # there were a number of these tests. I now no longer know where the regression files exist.
    # the best option here is to use a token on CI to test this by downloading an existing file.
    #
    # @slow
    # def test_message_ref(self):
    #     prefix = 'regression_data'
    #     inf = 'MESSAGE-GLOBIOM_SSP2-Ref-SPA0-V25_unharmonized.xlsx'
    #     checkf = 'test_regress_ssp2_ref.xlsx'
    #     self._run(prefix, inf, checkf)
