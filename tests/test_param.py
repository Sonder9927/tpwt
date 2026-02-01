from pathlib import Path

import pytest

import tpwt


@pytest.fixture
def config_toml():
    return "tests/config-test.toml"


def test_param(config_toml: str):
    cfg = tpwt.TPWTConfig(config_toml)
    assert Path(cfg.outpath).exists()
