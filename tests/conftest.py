import sys
import os
import pytest

# 把项目根目录加入 Python 模块搜索路径
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from backend import app, init_sample_data


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-key'

    with app.test_client() as client:
        with app.app_context():
            init_sample_data()
        yield client
