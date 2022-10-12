from src.orchestration.tempfile import temp_func


def test_temp_src():
    temp_func()
    assert True


def test_dummy():
    assert True == True
