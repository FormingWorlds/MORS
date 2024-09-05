import mors
import pytest
from numpy.testing import assert_allclose

TEST_DATA = (
    ((0.128, 45.2, 8.5e1),(0.21263373, 1.68612613e+31, 1.74497354e+28)),
    ((1.113, 17.7, 3.2e3),(1.16581856, 6.81769993e+33, 7.95296357e+28)),
    ((0.9999, 1.0001, 1.0e4),(1.52531295e+00, 8.12513828e+33, 3.18153902e+28)),
    ((1.000, 1.00, 1.0e4),(1.526565e+00, 8.13136992e+33, 3.19921075e+28)),
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

    assert_allclose(ret, expected, rtol=1e-5, atol=0)
