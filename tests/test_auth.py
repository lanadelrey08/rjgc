
def test_register_success(client):
    resp = client.post('/api/register', json={
        'username': 'charlie',
        'password': '123456'
    })
    assert resp.json['code'] == 0


def test_register_empty_username(client):
    resp = client.post('/api/register', json={
        'username': '',
        'password': '123456'
    })
    assert resp.json['code'] == -1


def test_register_short_password(client):
    resp = client.post('/api/register', json={
        'username': 'tom',
        'password': '123'
    })
    assert resp.json['message'] == '密码长度不能少于6位'


def test_register_duplicate_username(client):
    resp = client.post('/api/register', json={
        'username': 'alice',
        'password': '123456'
    })
    assert resp.json['message'] == '用户名已存在'


def test_login_success(client):
    resp = client.post('/api/login', json={
        'username': 'alice',
        'password': '123456'
    })
    assert resp.json['code'] == 0


def test_login_wrong_password(client):
    resp = client.post('/api/login', json={
        'username': 'alice',
        'password': '000000'
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post('/api/login', json={
        'username': 'nobody',
        'password': '123456'
    })
    assert resp.json['code'] == -1


def test_current_user_without_login(client):
    resp = client.get('/api/current_user')
    assert resp.status_code == 401


def test_logout(client):
    client.post('/api/login', json={
        'username': 'alice',
        'password': '123456'
    })
    resp = client.post('/api/logout')
    assert resp.json['message'] == '登出成功'


def test_login_required_after_logout(client):
    client.post('/api/login', json={
        'username': 'alice',
        'password': '123456'
    })
    client.post('/api/logout')
    resp = client.get('/api/my/events')
    assert resp.status_code == 401
