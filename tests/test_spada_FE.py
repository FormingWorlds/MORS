import mors
import pytest
from numpy.testing import assert_allclose

TEST_DATA = (
    ((0.128, 45.2, 8.5e1),(0.21263373, 1.68612614e+31, 1.73275380e+28)),
    ((1.113, 17.7, 3.2e3),(1.16581827, 6.81769926e+33, 7.94292986e+28)),
    ((0.995, 1.005, 1.0e4),(1.48904952e+00, 7.80667546e+33, 3.22933432e+28)),
    ((1.000, 1.00, 1.0e4),(1.52583342e+00, 8.13191736e+33, 3.38245392e+28)),
)

@pytest.mark.parametrize("inp,expected", TEST_DATA)
def test_spada(inp, expected):

    mors.DownloadEvolutionTracks('Spada')
    params = mors.NewParams()
    params['TimeIntegrationMethod'] = 'ForwardEuler'
    star = mors.Star(Mstar=inp[0], Omega=inp[1], params = params)
    ret = (
         star.Value(inp[2], 'Rstar'),
         star.Value(inp[2], 'Lbol'),
         star.Value(inp[2], 'Leuv'),
         )

    assert_allclose(ret, expected, rtol=1e-5, atol=0)
