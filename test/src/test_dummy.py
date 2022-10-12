from src.tempfile import temp_func


def test_dummy():
    assert True


def test_temp_src():
    temp_func()
    assert True
