import requests

BASE_URL = "http://127.0.0.1:5000"

# 创建一个 session 来保持登录状态
session = requests.Session()

# 1. 登录
print("=== 登录 ===")
response = session.post(f"{BASE_URL}/api/login", json={
    "username": "alice",
    "password": "123456"
})
print(response.json())

# 2. 获取活动列表
print("\n=== 获取活动列表 ===")
response = session.get(f"{BASE_URL}/api/events")
print(response.json())

# 3. 标记"想去"
print("\n=== 标记想去活动1 ===")
response = session.post(f"{BASE_URL}/api/events/1/interest")
print(response.json())

# 4. 查看我的活动
print("\n=== 我的活动 ===")
response = session.get(f"{BASE_URL}/api/my/events")
print(response.json())