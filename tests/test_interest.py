
def login(client):
    client.post('/api/login', json={
        'username': 'alice',
        'password': '123456'
    })


def test_interest_add(client):
    login(client)
    resp = client.post('/api/events/2/interest')
    assert resp.json['data']['is_interested'] is True


def test_interest_cancel(client):
    login(client)
    client.post('/api/events/2/interest')
    resp = client.post('/api/events/2/interest')
    assert resp.json['data']['is_interested'] is False


def test_interest_event_not_exist(client):
    login(client)
    resp = client.post('/api/events/999/interest')
    assert resp.status_code == 404


def test_interest_event_toggle(client):
    login(client)
    resp1 = client.post('/api/events/1/interest')
    assert resp1.json['message'] == '已标记"想去"'

    resp2 = client.post('/api/events/1/interest')
    assert resp2.json['message'] == '已取消"想去"'


def test_interest_without_login(client):
    resp = client.post('/api/events/1/interest')
    assert resp.status_code == 401


def test_my_events(client):
    login(client)
    resp = client.get('/api/my/events')
    assert 'created' in resp.json['data']
    assert 'interested' in resp.json['data']
