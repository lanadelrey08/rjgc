def test_user_auth_integration(client):
    # 注册
    resp = client.post('/api/register', json={
        'username': 'int_user',
        'password': '123456'
    })
    assert resp.status_code == 200
    assert resp.json['code'] == 0

    # 登录
    resp = client.post('/api/login', json={
        'username': 'int_user',
        'password': '123456'
    })
    assert resp.status_code == 200
    assert resp.json['data']['username'] == 'int_user'

    # 登录后访问受限接口
    resp = client.get('/api/current_user')
    assert resp.status_code == 200
    assert resp.json['data']['username'] == 'int_user'

    # 登出
    resp = client.post('/api/logout')
    assert resp.status_code == 200

    # 登出后访问受限接口
    resp = client.get('/api/current_user')
    assert resp.status_code == 401

def test_interest_integration(client):
    # 使用样例用户登录（后端已初始化）
    resp = client.post('/api/login', json={
        'username': 'alice',
        'password': '123456'
    })
    assert resp.status_code == 200

    # 标记“想去”
    resp = client.post('/api/events/1/interest')
    assert resp.status_code == 200
    assert resp.json['code'] == 0

    # 再次调用，取消“想去”
    resp = client.post('/api/events/1/interest')
    assert resp.status_code == 200
    assert resp.json['code'] == 0

    # 查询我的活动
    resp = client.get('/api/my/events')
    assert resp.status_code == 200
    assert 'created' in resp.json['data']
    assert 'interested' in resp.json['data']