from flask import Flask, request, jsonify, session
from datetime import datetime, timedelta
from functools import wraps
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['JSON_AS_ASCII'] = False  # 支持中文

# ===========================
# 内存数据存储
# ===========================

# 用户数据 {user_id: {username, password, ...}}
users_db = {}
user_id_counter = 1

# 活动数据 {event_id: {title, start_time, end_time, location, ...}}
events_db = {}
event_id_counter = 1

# "想去"关系 {event_id: [user_id1, user_id2, ...]}
interests_db = {}

# 活动分类
CATEGORIES = ['学术讲座', '社团招新', '文体娱乐', '其他']


# ===========================
# 工具函数
# ===========================

def success_response(data=None, message='success'):
    """统一成功响应格式"""
    return jsonify({'code': 0, 'message': message, 'data': data})


def error_response(message='error', code=400):
    """统一错误响应格式"""
    return jsonify({'code': -1, 'message': message}), code


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id or user_id not in users_db:
            return error_response('请先登录', 401)
        return f(*args, **kwargs)
    return decorated_function


def parse_datetime(dt_str):
    """解析时间字符串，支持多种格式"""
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError('时间格式错误，支持格式如: 2025-11-15 14:30')


def format_event(event_id):
    """格式化活动信息，添加统计数据"""
    event = events_db[event_id].copy()
    event['id'] = event_id
    
    # 添加"想去"人数
    interested_users = interests_db.get(event_id, [])
    event['interested_count'] = len(interested_users)
    
    # 判断是否已满
    capacity = event.get('capacity')
    event['is_full'] = capacity is not None and len(interested_users) >= capacity
    
    # 判断当前用户是否已标记"想去"
    current_user_id = session.get('user_id')
    event['is_interested'] = current_user_id in interested_users if current_user_id else False
    
    # 时间格式化为字符串
    event['start_time'] = event['start_time'].strftime('%Y-%m-%d %H:%M')
    event['end_time'] = event['end_time'].strftime('%Y-%m-%d %H:%M')
    
    return event


# ===========================
# 用户相关API
# ===========================

@app.route('/api/register', methods=['POST'])
def register():
    """
    用户注册
    POST /api/register
    {
        "username": "alice",
        "password": "123456"
    }
    """
    global user_id_counter
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # 校验
    if not username or not password:
        return error_response('用户名和密码不能为空')
    
    if len(password) < 6:
        return error_response('密码长度不能少于6位')
    
    # 检查用户名是否已存在
    for user in users_db.values():
        if user['username'] == username:
            return error_response('用户名已存在')
    
    # 创建新用户
    user_id = user_id_counter
    user_id_counter += 1
    
    users_db[user_id] = {
        'username': username,
        'password': password,  # 实际项目应该加密，这里简化
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return success_response({'user_id': user_id, 'username': username}, '注册成功')


@app.route('/api/login', methods=['POST'])
def login():
    """
    用户登录
    POST /api/login
    {
        "username": "alice",
        "password": "123456"
    }
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # 查找用户
    for user_id, user in users_db.items():
        if user['username'] == username and user['password'] == password:
            # 设置会话
            session['user_id'] = user_id
            return success_response({
                'user_id': user_id,
                'username': username
            }, '登录成功')
    
    return error_response('用户名或密码错误', 401)


@app.route('/api/logout', methods=['POST'])
def logout():
    """
    用户登出
    POST /api/logout
    """
    session.clear()
    return success_response(message='登出成功')


@app.route('/api/current_user', methods=['GET'])
@login_required
def get_current_user():
    """
    获取当前登录用户信息
    GET /api/current_user
    """
    user_id = session.get('user_id')
    user = users_db[user_id]
    return success_response({
        'user_id': user_id,
        'username': user['username']
    })


# ===========================
# 活动相关API
# ===========================

@app.route('/api/events', methods=['GET'])
def get_events():
    """
    获取活动列表
    GET /api/events?category=学术讲座&status=upcoming
    
    参数:
    - category: 分类筛选（可选）
    - status: upcoming(即将发生) / past(已结束) / all(全部)，默认upcoming
    """
    category = request.args.get('category', '').strip()
    status = request.args.get('status', 'upcoming')
    
    now = datetime.now()
    result = []
    
    for event_id in events_db:
        event = events_db[event_id]
        
        # 状态筛选
        if status == 'upcoming' and event['end_time'] < now:
            continue
        elif status == 'past' and event['end_time'] >= now:
            continue
        
        # 分类筛选
        if category and event.get('category') != category:
            continue
        
        result.append(format_event(event_id))
    
    # 按开始时间排序
    result.sort(key=lambda x: x['start_time'], reverse=(status == 'past'))
    
    return success_response({
        'events': result,
        'total': len(result)
    })


@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event_detail(event_id):
    """
    获取活动详情
    GET /api/events/1
    """
    if event_id not in events_db:
        return error_response('活动不存在', 404)
    
    event = format_event(event_id)
    
    # 添加创建者信息
    creator_id = event.get('creator_id')
    if creator_id and creator_id in users_db:
        event['creator'] = {
            'user_id': creator_id,
            'username': users_db[creator_id]['username']
        }
    
    # 添加想去的用户列表（前10个）
    interested_user_ids = interests_db.get(event_id, [])[:10]
    event['interested_users'] = [
        {'user_id': uid, 'username': users_db[uid]['username']}
        for uid in interested_user_ids if uid in users_db
    ]
    
    return success_response(event)


@app.route('/api/events', methods=['POST'])
@login_required
def create_event():
    """
    创建活动
    POST /api/events
    {
        "title": "人工智能讲座",
        "start_time": "2025-11-20 14:00",
        "end_time": "2025-11-20 16:00",
        "location": "教学楼A201",
        "category": "学术讲座",
        "description": "详细介绍...",
        "cover_image_url": "https://...",
        "capacity": 50
    }
    """
    global event_id_counter
    
    data = request.get_json()
    user_id = session.get('user_id')
    
    # 必填字段验证
    required_fields = ['title', 'start_time', 'end_time', 'location']
    for field in required_fields:
        if not data.get(field):
            return error_response(f'缺少必填字段: {field}')
    
    # 时间解析
    try:
        start_time = parse_datetime(data['start_time'])
        end_time = parse_datetime(data['end_time'])
    except ValueError as e:
        return error_response(str(e))
    
    # 时间逻辑校验
    if end_time <= start_time:
        return error_response('结束时间必须晚于开始时间')
    
    if start_time < datetime.now():
        return error_response('开始时间不能早于当前时间')
    
    # 分类校验
    category = data.get('category', '').strip()
    if category and category not in CATEGORIES:
        category = '其他'
    
    # 人数上限
    capacity = data.get('capacity')
    if capacity is not None:
        try:
            capacity = int(capacity)
            if capacity < 1:
                return error_response('人数上限必须大于0')
        except ValueError:
            return error_response('人数上限必须为整数')
    
    # 创建活动
    event_id = event_id_counter
    event_id_counter += 1
    
    events_db[event_id] = {
        'title': data['title'].strip(),
        'start_time': start_time,
        'end_time': end_time,
        'location': data['location'].strip(),
        'category': category,
        'description': data.get('description', '').strip(),
        'cover_image_url': data.get('cover_image_url', '').strip(),
        'capacity': capacity,
        'creator_id': user_id,
        'created_at': datetime.now()
    }
    
    # 初始化"想去"列表
    interests_db[event_id] = []
    
    return success_response(format_event(event_id), '活动创建成功')


# ===========================
# 互动相关API
# ===========================

@app.route('/api/events/<int:event_id>/interest', methods=['POST'])
@login_required
def toggle_interest(event_id):
    """
    标记/取消"想去"
    POST /api/events/1/interest
    """
    if event_id not in events_db:
        return error_response('活动不存在', 404)
    
    user_id = session.get('user_id')
    event = events_db[event_id]
    
    # 检查活动是否已结束
    if event['end_time'] < datetime.now():
        return error_response('活动已结束，无法操作')
    
    # 获取想去列表
    if event_id not in interests_db:
        interests_db[event_id] = []
    
    interested_users = interests_db[event_id]
    
    # 已经想去 -> 取消
    if user_id in interested_users:
        interested_users.remove(user_id)
        return success_response({
            'is_interested': False,
            'interested_count': len(interested_users)
        }, '已取消"想去"')
    
    # 检查是否已满
    capacity = event.get('capacity')
    if capacity is not None and len(interested_users) >= capacity:
        return error_response('活动名额已满')
    
    # 添加想去
    interested_users.append(user_id)
    return success_response({
        'is_interested': True,
        'interested_count': len(interested_users)
    }, '已标记"想去"')


@app.route('/api/my/events', methods=['GET'])
@login_required
def get_my_events():
    """
    获取我的活动
    GET /api/my/events
    
    返回:
    - created: 我创建的活动列表
    - interested: 我想去的活动列表
    """
    user_id = session.get('user_id')
    
    # 我创建的活动
    created = []
    for event_id, event in events_db.items():
        if event.get('creator_id') == user_id:
            created.append(format_event(event_id))
    
    # 我想去的活动
    interested = []
    for event_id, interested_users in interests_db.items():
        if user_id in interested_users:
            interested.append(format_event(event_id))
    
    # 排序
    created.sort(key=lambda x: x['start_time'], reverse=True)
    interested.sort(key=lambda x: x['start_time'])
    
    return success_response({
        'created': created,
        'interested': interested
    })


# ===========================
# 其他API
# ===========================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """
    获取所有分类
    GET /api/categories
    """
    return success_response({'categories': CATEGORIES})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    获取统计信息
    GET /api/stats
    """
    now = datetime.now()
    upcoming_count = sum(1 for e in events_db.values() if e['end_time'] >= now)
    
    return success_response({
        'total_users': len(users_db),
        'total_events': len(events_db),
        'upcoming_events': upcoming_count,
        'total_interests': sum(len(v) for v in interests_db.values())
    })


# ===========================
# 初始化样例数据
# ===========================

def init_sample_data():
    """初始化一些样例数据用于测试"""
    global user_id_counter, event_id_counter
    
    # 创建样例用户
    users_db[1] = {
        'username': 'alice',
        'password': '123456',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    users_db[2] = {
        'username': 'bob',
        'password': '123456',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    user_id_counter = 3
    
    # 创建样例活动
    now = datetime.now()
    
    events_db[1] = {
        'title': '人工智能前沿讲座',
        'start_time': now + timedelta(days=1, hours=2),
        'end_time': now + timedelta(days=1, hours=4),
        'location': '教学楼A201',
        'category': '学术讲座',
        'description': '邀请知名校友分享AI趋势与职业发展机会',
        'cover_image_url': 'https://picsum.photos/seed/ai/600/300',
        'capacity': 50,
        'creator_id': 1,
        'created_at': now
    }
    
    events_db[2] = {
        'title': '话剧社秋季招新说明会',
        'start_time': now + timedelta(days=2),
        'end_time': now + timedelta(days=2, hours=2),
        'location': '活动中心103',
        'category': '社团招新',
        'description': '欢迎热爱表演与舞台的同学加入话剧社！',
        'cover_image_url': 'https://picsum.photos/seed/drama/600/300',
        'capacity': 30,
        'creator_id': 2,
        'created_at': now
    }
    
    events_db[3] = {
        'title': '校园篮球友谊赛',
        'start_time': now + timedelta(days=3, hours=1),
        'end_time': now + timedelta(days=3, hours=3),
        'location': '西区篮球场',
        'category': '文体娱乐',
        'description': '以球会友，切磋技艺，重在参与！',
        'cover_image_url': 'https://picsum.photos/seed/basketball/600/300',
        'capacity': None,
        'creator_id': 1,
        'created_at': now
    }
    
    event_id_counter = 4
    
    # 初始化想去关系
    interests_db[1] = [2]  # bob想去活动1
    interests_db[2] = []
    interests_db[3] = [1, 2]  # alice和bob都想去活动3
    
    print('样例数据初始化完成')
    print(f'- 用户数: {len(users_db)}')
    print(f'- 活动数: {len(events_db)}')


# ===========================
# 启动服务
# ===========================

@app.route('/')
def index():
    """API文档首页"""
    return jsonify({
        'name': '校园活动社交App API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/register': '用户注册',
            'POST /api/login': '用户登录',
            'POST /api/logout': '用户登出',
            'GET /api/current_user': '获取当前用户',
            'GET /api/events': '获取活动列表',
            'GET /api/events/<id>': '获取活动详情',
            'POST /api/events': '创建活动',
            'POST /api/events/<id>/interest': '标记/取消想去',
            'GET /api/my/events': '获取我的活动',
            'GET /api/categories': '获取分类列表',
            'GET /api/stats': '获取统计信息'
        }
    })


if __name__ == '__main__':
    # 初始化样例数据
    init_sample_data()
    
    print('=' * 50)
    print('校园活动社交App后端服务启动')
    print('访问 http://127.0.0.1:5000 查看API文档')
    print('样例用户: alice/123456, bob/123456')
    print('=' * 50)
    
    app.run(debug=True, port=5000)