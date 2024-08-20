import mors
import pytest
from numpy.testing import assert_allclose

TEST_DATA = (
    ((0.047, 8.5e7, 0.75),(0.0007430607161602045, 0.143, 1.7980958798328914)),
    ((1.113, 3.2e9, 1.05),(1.6544100501920276, 1.1821623140636999, 2042.5638079262828))
)

@pytest.mark.parametrize("inp,expected", TEST_DATA)
def test_baraffe(inp, expected):

    baraffe = mors.BaraffeTrack(inp[0])
    ret = (
         baraffe.BaraffeLuminosity(inp[1]),
         baraffe.BaraffeStellarRadius(inp[1]),
         baraffe.BaraffeSolarConstant(inp[1], inp[2]),
         )

    assert_allclose(ret, expected, rtol=1e-5, atol=0)
