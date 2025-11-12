const API_BASE = 'http://127.0.0.1:5000/api';

// 加载活动列表
async function loadEvents(category = 'all') {
    try {
        let url = `${API_BASE}/events`;
        if (category !== 'all') {
            url += `?category=${encodeURIComponent(category)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        const eventList = document.getElementById('eventList');
        if (!eventList) return;
        
        if (data.events && data.events.length > 0) {
            eventList.innerHTML = data.events.map(event => `
                <div class="event-card" onclick="viewEvent(${event.id})">
                    <div class="event-image"></div>
                    <div class="event-info">
                        <div class="event-title">${event.title}</div>
                        <div class="event-time">${event.start_time}</div>
                        <div class="event-location">${event.location}</div>
                        <span class="event-tag ${getTagClass(event.category)}">${event.category}</span>
                    </div>
                </div>
            `).join('');
        } else {
            eventList.innerHTML = '<p style="text-align:center;color:#999;padding:40px;">暂无活动</p>';
        }
    } catch (error) {
        console.error('加载活动失败:', error);
    }
}

// 获取标签颜色类
function getTagClass(category) {
    const colorMap = {
        '学术讲座': '',
        '社团招新': 'tag-green',
        '文体娱乐': 'tag-red',
    };
    return colorMap[category] || '';
}

// 分类切换
document.addEventListener('DOMContentLoaded', () => {
    // 首页分类切换
    const tabs = document.querySelectorAll('.category-tabs .tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            loadEvents(tab.dataset.category);
        });
    });
    
    // 个人中心标签切换
    const profileTabs = document.querySelectorAll('.profile-tabs .tab');
    profileTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            profileTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            if (tab.dataset.tab === 'interested') {
                document.getElementById('interestedEvents').classList.add('active');
                loadMyEvents('interested');
            } else {
                document.getElementById('publishedEvents').classList.add('active');
                loadMyEvents('published');
            }
        });
    });
    
    // 初始加载
    if (document.getElementById('eventList')) {
        loadEvents();
    }
    if (document.getElementById('username')) {
        loadUserProfile();
    }
});

// 查看活动详情
function viewEvent(id) {
    alert(`查看活动详情 ID: ${id}\n（详情页面待实现）`);
}

// 显示搜索框
function showSearch() {
    const searchBox = document.getElementById('searchBox');
    searchBox.style.display = searchBox.style.display === 'none' ? 'block' : 'none';
}

// 提交活动
async function submitEvent() {
    const form = document.getElementById('publishForm');
    const formData = new FormData(form);
    
    const data = {
        title: formData.get('title'),
        start_time: formData.get('start_time').replace('T', ' '),
        end_time: formData.get('end_time').replace('T', ' '),
        location: formData.get('location'),
        category: formData.get('category'),
        description: formData.get('description'),
        capacity: formData.get('capacity') || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('发布成功！');
            window.location.href = 'index.html';
        } else {
            alert(result.error || '发布失败');
        }
    } catch (error) {
        alert('网络错误');
        console.error(error);
    }
}

// 加载用户信息
async function loadUserProfile() {
    try {
        const response = await fetch(`${API_BASE}/current_user`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.username) {
            document.getElementById('username').textContent = data.username;
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
    }
}

// 加载我的活动
async function loadMyEvents(type) {
    try {
        const response = await fetch(`${API_BASE}/my/events`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        const events = type === 'interested' ? data.interested_events : data.published_events;
        const container = document.getElementById(type === 'interested' ? 'interestedEvents' : 'publishedEvents');
        
        if (events && events.length > 0) {
            container.innerHTML = events.map(event => `
                <div class="event-card">
                    <div class="event-image"></div>
                    <div class="event-info">
                        <div class="event-title">${event.title}</div>
                        <div class="event-time">${event.start_time}</div>
                        <div class="event-location">${event.location}</div>
                        <button class="btn-primary" style="margin-top:10px;">操作</button>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="text-align:center;color:#999;padding:40px;">暂无活动</p>';
        }
    } catch (error) {
        console.error('加载我的活动失败:', error);
    }
}

function editProfile() {
    alert('编辑个人信息功能待实现');
}
