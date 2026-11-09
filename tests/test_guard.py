import pytest

from attacks.guard import OutOfLabError, assert_in_lab


@pytest.mark.parametrize("ok", ["10.20.0.10", "10.21.0.30", "10.20.0.0/27"])
def test_allows_lab(ok):
    assert assert_in_lab(ok) == ok


@pytest.mark.parametrize(
    "bad",
    ["8.8.8.8", "192.168.0.1", "10.20.0.0/16", "10.19.0.2", "example.com", ""],
)
def test_refuses_outside(bad):
    with pytest.raises(OutOfLabError):
        assert_in_lab(bad)
