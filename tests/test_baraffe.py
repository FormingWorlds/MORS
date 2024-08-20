import mors
import pytest
from numpy.testing import assert_allclose

TEST_DATA = (
    ((0.047, 8.5e7, 0.75),(0.74306071e-3, 0.14300000, 1.79809587  )),
    ((1.113, 3.2e9, 1.05),(1.65441005   , 1.18216231, 2.04256380e3)),
)

@pytest.mark.parametrize("inp,expected", TEST_DATA)
def test_baraffe(inp, expected):

    mors.DownloadEvolutionTracks('Baraffe')
    baraffe = mors.BaraffeTrack(inp[0])
    ret = (
         baraffe.BaraffeLuminosity(inp[1]),
         baraffe.BaraffeStellarRadius(inp[1]),
         baraffe.BaraffeSolarConstant(inp[1], inp[2]),
         )

    assert_allclose(ret, expected, rtol=1e-5, atol=0)
