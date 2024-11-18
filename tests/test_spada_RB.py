import mors
import pytest
from numpy.testing import assert_allclose

TEST_DATA = (
    ((0.128, 45.2, 8.5e1),(0.21264087, 1.68629162e+31, 1.74475018e+28)),
    ((1.113, 17.7, 3.2e3),(1.16581971, 6.81767904e+33, 7.94621466e+28)),
    ((0.995, 1.005, 1.0e4),(1.48910765e+00, 7.80659378e+33, 3.16581356e+28)),
    ((1.000, 1.00, 1.0e4),(1.52588718e+00, 8.13197065e+33, 3.29155751e+28)),
)

@pytest.mark.parametrize("inp,expected", TEST_DATA)
def test_spada(inp, expected):

    mors.DownloadEvolutionTracks('Spada')
    star = mors.Star(Mstar=inp[0], Omega=inp[1])
    ret = (
         star.Value(inp[2], 'Rstar'),
         star.Value(inp[2], 'Lbol'),
         star.Value(inp[2], 'Leuv'),
         )

    assert_allclose(ret, expected, rtol=1e-6, atol=0)
