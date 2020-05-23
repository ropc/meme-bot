import pytest

def run():
    pytest.main()

def run_debug():
    import ptvsd
    ptvsd.attach()

    run()
