# 喜马拉雅音频集成指南

## 📋 概述

本文档说明如何将喜马拉雅音频内容集成到 `python-learning-site` 项目中，实现以下核心功能：

1. **音频下载**：下载专辑前三集音频或单集下载（不提供播放链接）
2. **在线播放**：页面提供前三集音频播放器（本地播放）
3. **文本提取**：优先提取专辑配套文本，若无则通过语音识别生成文字
4. **思维导图生成**：将文本内容提交到"文档分析 + 思维导图"功能生成思维导图
5. **历史记录**：用户可在搜索页查看之前预览的专辑和相关思维导图

---

## 🔑 第一步：入驻喜马拉雅开放平台

### 1.1 访问开放平台
- 平台地址：https://open.ximalaya.com/
- 商务合作热线：(021)50179077-8806 / 8803

### 1.2 选择开发者类型

**企业开发者**（推荐）
- 支持 API / H5 接入方式
- 可进行音频深度合作、付费内容分销
- 适合商业项目

**个人开发者**
- 仅支持 H5 接入方式
- 可接入免费音频内容、开发个人电台

### 1.3 入驻流程
1. 注册账号
2. 创建应用（选择"移动应用"或"网页/小程序"）
3. 选择技术接入方式：**API**
4. 提交审核

---

## 🔧 第二步：获取 API 凭证

### 2.1 应用信息
创建应用后，在【管理中心】→【应用中心】获取：
- `app_key` (client_id)
- `client_secret`
- `serverAuthStaticKey`

### 2.2 配置 IP 白名单
在【提交应用审核】→【其他服务】中配置服务器 IP 白名单

### 2.3 申请测试账号
联系商务对接人申请测试账号（如需测试付费内容）

---

## 🌐 第三步：API 域名配置

### 3.1 请求域名
```python
# 主域名
API_BASE_URL = "https://api.ximalaya.com"
# 备用域名（故障切换）
API_BACKUP_URL = "https://apihera.ximalaya.com"

# 付费内容域名
MPAY_BASE_URL = "https://mpay.ximalaya.com"
MPAY_BACKUP_URL = "https://mpayhera.ximalaya.com"
```

### 3.2 返回域名（白名单配置）
```python
# 图片域名
IMG_DOMAIN = "imgopen.xmcdn.com"

# 音频下载域名
DOWNLOAD_DOMAINS = [
    "download.ali.xmcdn.com",
    "download.xmcdn.com",
    "audio.ali.xmcdn.com",
    "aod.cos.tx.xmcdn.com",
    "audio.xmcdn.com"
]

# 付费音频域名
PAID_AUDIO_DOMAINS = [
    "audiopay.ali.xmcdn.com",
    "audiopay.cos.tx.xmcdn.com",
    "audio.pay.xmcdn.com"
]
```

---

## 🔐 第四步：签名算法

### 4.1 公共参数
所有 API 请求需要以下公共参数：

| 参数 | 说明 | 必填 |
|------|------|------|
| `app_key` | 应用 Key | 是 |
| `device_id` | 设备 ID（安卓 OAID，iOS IDFA） | 是 |
| `client_os_type` | 客户端系统类型 | 是 |
| `timestamp` | 时间戳（毫秒） | 是 |
| `nonce` | 随机字符串 | 是 |
| `sig` | 签名 | 是 |

### 4.2 签名生成算法
```python
import hashlib
import time
import uuid

def generate_signature(params, client_secret):
    """
    生成喜马拉雅 API 签名
    """
    # 1. 按参数名 ASCII 码排序
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    
    # 2. 拼接参数
    param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
    
    # 3. 拼接 client_secret
    sign_string = f"{param_string}{client_secret}"
    
    # 4. MD5 加密
    sig = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    
    return sig

def get_common_params(app_key, client_secret):
    """获取公共参数"""
    timestamp = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    
    params = {
        'app_key': app_key,
        'device_id': generate_device_id(),
        'client_os_type': '4',  # 4=Linux/Server
        'timestamp': timestamp,
        'nonce': nonce
    }
    
    # 生成签名
    params['sig'] = generate_signature(params, client_secret)
    
    return params

def generate_device_id():
    """生成设备 ID（服务器场景可用 UUID）"""
    return uuid.uuid4().hex
```

---

## 📚 第五步：常用 API 接口

### 5.1 获取访问令牌（OAuth2）
```python
import requests

def get_access_token(app_key, client_secret):
    """获取 OAuth2 访问令牌"""
    url = "https://api.ximalaya.com/oauth2/v2/access_token"
    
    params = get_common_params(app_key, client_secret)
    params.update({
        'client_id': app_key,
        'grant_type': 'client_credentials'
    })
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    
    response = requests.post(url, data=params, headers=headers)
    return response.json()
```

### 5.2 搜索专辑
```python
def search_albums(query, page=1, count=20):
    """搜索专辑"""
    url = "https://api.ximalaya.com/search/albums"
    
    params = get_common_params(APP_KEY, CLIENT_SECRET)
    params.update({
        'q': query,
        'category_id': 0,
        'calc_dimension': 1,
        'page': page,
        'count': count
    })
    
    response = requests.get(url, params=params)
    return response.json()
```

### 5.3 获取专辑详情
```python
def get_album_detail(album_id):
    """获取专辑详情"""
    url = f"https://api.ximalaya.com/album/{album_id}"
    
    params = get_common_params(APP_KEY, CLIENT_SECRET)
    
    response = requests.get(url, params=params)
    return response.json()
```

### 5.4 获取声音列表
```python
def get_tracks(album_id, page=1, count=20):
    """获取专辑声音列表"""
    url = f"https://api.ximalaya.com/album/{album_id}/tracks"
    
    params = get_common_params(APP_KEY, CLIENT_SECRET)
    params.update({
        'page': page,
        'count': count
    })
    
    response = requests.get(url, params=params)
    return response.json()
```

### 5.5 获取声音播放地址（用于下载）
```python
def get_track_playurl(track_id):
    """获取声音播放地址（用于下载音频文件）"""
    url = f"https://api.ximalaya.com/tracks/{track_id}/playurl"
    
    params = get_common_params(APP_KEY, CLIENT_SECRET)
    
    response = requests.get(url, params=params)
    return response.json()
```

---

## 💻 第六步：集成到 python-learning-site

### 6.1 创建喜马拉雅客户端模块

在 `python-learning-site/` 目录下创建 `ximalaya_client.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""喜马拉雅 API 客户端（支持下载、文本提取、思维导图生成）"""

import hashlib
import time
import uuid
import requests
import os
from typing import Dict, List, Optional
from pathlib import Path

class XimalayaClient:
    """喜马拉雅 API 客户端"""
    
    def __init__(self, app_key: str, client_secret: str):
        self.app_key = app_key
        self.client_secret = client_secret
        self.base_url = "https://api.ximalaya.com"
        self.access_token = None
        self.token_expires_at = 0
        self.download_dir = Path("downloads/ximalaya")
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_signature(self, params: Dict) -> str:
        """生成签名"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        sign_string = f"{param_string}{self.client_secret}"
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    
    def _get_common_params(self) -> Dict:
        """获取公共参数"""
        timestamp = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        
        params = {
            'app_key': self.app_key,
            'device_id': uuid.uuid4().hex,
            'client_os_type': '4',
            'timestamp': timestamp,
            'nonce': nonce
        }
        params['sig'] = self._generate_signature(params)
        return params
    
    def search_albums(self, query: str, page: int = 1, count: int = 20) -> Dict:
        """搜索专辑"""
        url = f"{self.base_url}/search/albums"
        params = self._get_common_params()
        params.update({
            'q': query,
            'category_id': 0,
            'calc_dimension': 1,
            'page': page,
            'count': count
        })
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_album_detail(self, album_id: str) -> Dict:
        """获取专辑详情"""
        url = f"{self.base_url}/album/{album_id}"
        params = self._get_common_params()
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_tracks(self, album_id: str, page: int = 1, count: int = 20) -> Dict:
        """获取专辑声音列表"""
        url = f"{self.base_url}/album/{album_id}/tracks"
        params = self._get_common_params()
        params.update({
            'page': page,
            'count': count
        })
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_track_playurl(self, track_id: str) -> Dict:
        """获取声音播放地址"""
        url = f"{self.base_url}/tracks/{track_id}/playurl"
        params = self._get_common_params()
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def download_track(self, track_id: str, track_title: str) -> Optional[str]:
        """下载音频文件到本地"""
        playurl_data = self.get_track_playurl(track_id)
        
        if 'error' in playurl_data or not playurl_data.get('play_url'):
            return None
        
        audio_url = playurl_data['play_url']
        file_path = self.download_dir / f"{track_id}_{track_title}.mp3"
        
        try:
            response = requests.get(audio_url, stream=True, timeout=30)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return str(file_path)
        except Exception as e:
            print(f"下载失败：{e}")
            return None
    
    def download_first_three_tracks(self, album_id: str) -> List[Dict]:
        """下载专辑前三集音频"""
        tracks_data = self.get_tracks(album_id, page=1, count=3)
        
        if 'error' in tracks_data or not tracks_data.get('tracks'):
            return []
        
        downloaded = []
        for track in tracks_data['tracks'][:3]:
            file_path = self.download_track(track['id'], track['title'])
            if file_path:
                downloaded.append({
                    'track_id': track['id'],
                    'title': track['title'],
                    'file_path': file_path,
                    'duration': track.get('duration', 0)
                })
        
        return downloaded
    
    def extract_album_text(self, album_id: str) -> Optional[str]:
        """尝试提取专辑配套文本（如果有）"""
        # 获取专辑详情，检查是否有文本内容
        album_data = self.get_album_detail(album_id)
        
        if 'error' in album_data:
            return None
        
        # 优先检查专辑介绍/简介
        text_content = album_data.get('description', '')
        
        # 检查是否有配套文本资源（根据实际 API 返回调整）
        if album_data.get('rich_content'):
            text_content += "\n\n" + album_data.get('rich_content', '')
        
        return text_content if text_content else None
    
    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """使用语音识别将音频转为文字（使用 DashScope）"""
        try:
            from dashscope import AudioTranscription
            
            result = AudioTranscription.call(
                model='paraformer-realtime-v2',
                file_path=audio_file_path
            )
            
            if result.status_code == 200:
                return result.output.get('text', '')
            else:
                print(f"语音识别失败：{result}")
                return None
        except Exception as e:
            print(f"语音识别异常：{e}")
            return None
    
    def process_album_for_mindmap(self, album_id: str, album_title: str) -> Dict:
        """处理专辑：下载前三集 + 提取文本 + 准备思维导图生成"""
        result = {
            'album_id': album_id,
            'album_title': album_title,
            'downloaded_tracks': [],
            'text_content': '',
            'mindmap_generated': False,
            'mindmap_url': None
        }
        
        # 1. 下载前三集音频
        downloaded = self.download_first_three_tracks(album_id)
        result['downloaded_tracks'] = downloaded
        
        # 2. 尝试提取专辑文本
        album_text = self.extract_album_text(album_id)
        
        if album_text:
            result['text_content'] = album_text
        else:
            # 3. 如果没有文本，对音频进行语音识别
            if downloaded:
                transcribed_texts = []
                for track in downloaded:
                    text = self.transcribe_audio(track['file_path'])
                    if text:
                        transcribed_texts.append(f"## {track['title']}\n\n{text}")
                
                result['text_content'] = "\n\n".join(transcribed_texts)
        
        return result
```

### 6.2 更新 requirements.txt

```txt
# 现有依赖...
requests>=2.28.0
dashscope>=1.14.0  # 用于语音识别
```

### 6.3 在 app.py 中添加路由

```python
from ximalaya_client import XimalayaClient
import json
from datetime import datetime

# 初始化喜马拉雅客户端（从环境变量读取配置）
ximalaya_app_key = os.environ.get('XIMALAYA_APP_KEY', '')
ximalaya_client_secret = os.environ.get('XIMALAYA_CLIENT_SECRET', '')
ximalaya_client = XimalayaClient(ximalaya_app_key, ximalaya_client_secret) if ximalaya_app_key else None

# 历史记录存储（可替换为数据库）
HISTORY_FILE = Path("data/ximalaya_history.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_history():
    """加载历史记录"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(history):
    """保存历史记录"""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route('/api/ximalaya/search')
def ximalaya_search():
    """搜索喜马拉雅专辑"""
    if not ximalaya_client:
        return jsonify({'error': '喜马拉雅 API 未配置'}), 500
    
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 20))
    
    if not query:
        return jsonify({'error': '缺少搜索关键词'}), 400
    
    result = ximalaya_client.search_albums(query, page, count)
    return jsonify(result)

@app.route('/api/ximalaya/album/<album_id>')
def ximalaya_album_detail(album_id):
    """获取专辑详情"""
    if not ximalaya_client:
        return jsonify({'error': '喜马拉雅 API 未配置'}), 500
    
    result = ximalaya_client.get_album_detail(album_id)
    return jsonify(result)

@app.route('/api/ximalaya/album/<album_id>/tracks')
def ximalaya_album_tracks(album_id):
    """获取专辑声音列表"""
    if not ximalaya_client:
        return jsonify({'error': '喜马拉雅 API 未配置'}), 500
    
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 20))
    
    result = ximalaya_client.get_tracks(album_id, page, count)
    return jsonify(result)

@app.route('/api/ximalaya/album/<album_id>/preview', methods=['POST'])
def ximalaya_album_preview(album_id):
    """预览专辑：下载前三集 + 提取文本 + 生成思维导图"""
    if not ximalaya_client:
        return jsonify({'error': '喜马拉雅 API 未配置'}), 500
    
    data = request.json or {}
    album_title = data.get('album_title', '未知专辑')
    
    # 处理专辑
    result = ximalaya_client.process_album_for_mindmap(album_id, album_title)
    
    # 保存到历史记录
    history = load_history()
    history_entry = {
        'album_id': album_id,
        'album_title': album_title,
        'preview_time': datetime.now().isoformat(),
        'downloaded_tracks': result['downloaded_tracks'],
        'text_content': result['text_content'],
        'mindmap_generated': result['mindmap_generated'],
        'mindmap_url': result['mindmap_url']
    }
    
    # 如果已有文本内容，可以调用思维导图生成
    if result['text_content']:
        # TODO: 调用文档分析 + 思维导图生成 API
        # mindmap_result = generate_mindmap(result['text_content'])
        # history_entry['mindmap_generated'] = True
        # history_entry['mindmap_url'] = mindmap_result.get('url')
        pass
    
    history.insert(0, history_entry)  # 新记录放在最前面
    save_history(history)
    
    return jsonify(history_entry)

@app.route('/api/ximalaya/track/<track_id>/download', methods=['POST'])
def ximalaya_track_download(track_id):
    """下载单集音频"""
    if not ximalaya_client:
        return jsonify({'error': '喜马拉雅 API 未配置'}), 500
    
    data = request.json or {}
    track_title = data.get('track_title', '未知音频')
    
    file_path = ximalaya_client.download_track(track_id, track_title)
    
    if file_path:
        return jsonify({'success': True, 'file_path': file_path})
    else:
        return jsonify({'error': '下载失败'}), 500

@app.route('/api/ximalaya/history')
def ximalaya_history():
    """获取历史记录"""
    history = load_history()
    return jsonify(history)

@app.route('/api/ximalaya/mindmap/<album_id>')
def ximalaya_mindmap(album_id):
    """获取专辑的思维导图"""
    history = load_history()
    
    for entry in history:
        if entry['album_id'] == album_id:
            return jsonify({
                'album_id': album_id,
                'mindmap_generated': entry.get('mindmap_generated', False),
                'mindmap_url': entry.get('mindmap_url')
            })
    
    return jsonify({'error': '未找到该专辑的预览记录'}), 404
```

### 6.4 添加前端页面

在 `templates/` 目录下创建 `ximalaya.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>喜马拉雅音频学习</title>
    <style>
        .album-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .album-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .album-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .album-cover {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 4px;
        }
        .track-list {
            list-style: none;
            padding: 0;
        }
        .track-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .btn {
            padding: 5px 15px;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            margin: 2px;
        }
        .btn-primary {
            background: #f86442;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .search-box {
            display: flex;
            gap: 10px;
            padding: 20px;
        }
        .search-box input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            overflow-y: auto;
        }
        .modal-content {
            background: white;
            margin: 50px auto;
            padding: 20px;
            max-width: 800px;
            border-radius: 8px;
        }
        .audio-player {
            width: 100%;
            margin: 10px 0;
        }
        .text-content {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        .mindmap-section {
            margin-top: 20px;
            padding: 15px;
            background: #e3f2fd;
            border-radius: 4px;
        }
        .history-section {
            margin-top: 30px;
            padding: 20px;
        }
        .history-item {
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            cursor: pointer;
        }
        .history-item:hover {
            background: #f8f9fa;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>
<body>
    <h1>🎧 喜马拉雅音频学习</h1>
    
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="搜索专辑，如：英语听力、数学讲解...">
        <button class="btn btn-primary" onclick="searchAlbums()">搜索</button>
    </div>
    
    <div id="albumGrid" class="album-grid"></div>
    
    <!-- 历史记录区域 -->
    <div class="history-section">
        <h2>📚 预览历史</h2>
        <div id="historyList"></div>
    </div>
    
    <!-- 专辑详情弹窗 -->
    <div id="albumModal" class="modal">
        <div class="modal-content">
            <h2 id="albumTitle"></h2>
            <div id="albumInfo"></div>
            
            <h3>🎵 前三集预览</h3>
            <div id="trackList"></div>
            
            <div id="textContent" class="text-content" style="display:none;"></div>
            
            <div id="mindmapSection" class="mindmap-section" style="display:none;">
                <h3>🧠 思维导图</h3>
                <div id="mindmapContent"></div>
            </div>
            
            <div style="margin-top:20px;">
                <button class="btn btn-primary" onclick="previewAlbum()">预览专辑（下载 + 生成思维导图）</button>
                <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
            </div>
        </div>
    </div>

    <script>
        let currentAlbumId = null;
        
        async function searchAlbums() {
            const query = document.getElementById('searchInput').value;
            if (!query) return;
            
            const response = await fetch(`/api/ximalaya/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            const grid = document.getElementById('albumGrid');
            grid.innerHTML = '';
            
            if (data.albums) {
                data.albums.forEach(album => {
                    const card = document.createElement('div');
                    card.className = 'album-card';
                    card.innerHTML = `
                        <img src="${album.cover_url || 'https://via.placeholder.com/250x200'}" class="album-cover">
                        <h3>${album.title}</h3>
                        <p>${album.description || ''}</p>
                        <p>声音数：${album.track_count}</p>
                    `;
                    card.onclick = () => showAlbumTracks(album.id, album.title);
                    grid.appendChild(card);
                });
            }
        }
        
        async function showAlbumTracks(albumId, albumTitle) {
            currentAlbumId = albumId;
            document.getElementById('albumTitle').textContent = albumTitle;
            
            const response = await fetch(`/api/ximalaya/album/${albumId}/tracks`);
            const data = await response.json();
            
            const trackList = document.getElementById('trackList');
            trackList.innerHTML = '';
            
            if (data.tracks) {
                data.tracks.slice(0, 3).forEach((track, index) => {
                    const div = document.createElement('div');
                    div.className = 'track-item';
                    div.innerHTML = `
                        <div>
                            <strong>第${index + 1}集:</strong> ${track.title}
                            <audio class="audio-player" controls>
                                <source src="/api/ximalaya/track/${track.id}/playurl" type="audio/mpeg">
                                您的浏览器不支持音频播放
                            </audio>
                        </div>
                        <div>
                            <button class="btn btn-primary" onclick="downloadTrack('${track.id}', '${track.title}')">下载</button>
                        </div>
                    `;
                    trackList.appendChild(div);
                });
            }
            
            // 隐藏文本和思维导图区域
            document.getElementById('textContent').style.display = 'none';
            document.getElementById('mindmapSection').style.display = 'none';
            
            document.getElementById('albumModal').style.display = 'block';
        }
        
        async function previewAlbum() {
            if (!currentAlbumId) return;
            
            const albumTitle = document.getElementById('albumTitle').textContent;
            
            // 显示加载状态
            document.getElementById('albumInfo').innerHTML = '<div class="loading">正在下载音频并生成思维导图，请稍候...</div>';
            
            const response = await fetch(`/api/ximalaya/album/${currentAlbumId}/preview`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({album_title: albumTitle})
            });
            
            const result = await response.json();
            
            // 显示文本内容
            if (result.text_content) {
                const textDiv = document.getElementById('textContent');
                textDiv.innerHTML = '<h3>📄 提取文本</h3><pre style="white-space: pre-wrap;">' + result.text_content + '</pre>';
                textDiv.style.display = 'block';
            }
            
            // 显示思维导图
            if (result.mindmap_generated && result.mindmap_url) {
                const mindmapDiv = document.getElementById('mindmapSection');
                mindmapDiv.innerHTML = '<h3>🧠 思维导图</h3><a href="' + result.mindmap_url + '" target="_blank">查看思维导图</a>';
                mindmapDiv.style.display = 'block';
            }
            
            document.getElementById('albumInfo').innerHTML = '<p style="color: green;">✓ 预览完成！</p>';
            
            // 刷新历史记录
            loadHistory();
        }
        
        async function downloadTrack(trackId, trackTitle) {
            const response = await fetch(`/api/ximalaya/track/${trackId}/download`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({track_title: trackTitle})
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('下载成功！文件已保存到：' + result.file_path);
            } else {
                alert('下载失败：' + (result.error || '未知错误'));
            }
        }
        
        async function loadHistory() {
            const response = await fetch('/api/ximalaya/history');
            const history = await response.json();
            
            const historyList = document.getElementById('historyList');
            historyList.innerHTML = '';
            
            if (history.length === 0) {
                historyList.innerHTML = '<p>暂无预览历史记录</p>';
                return;
            }
            
            history.forEach(entry => {
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerHTML = `
                    <h4>${entry.album_title}</h4>
                    <p>预览时间：${new Date(entry.preview_time).toLocaleString()}</p>
                    <p>已下载集数：${entry.downloaded_tracks ? entry.downloaded_tracks.length : 0}</p>
                    ${entry.mindmap_generated ? '<p style="color: green;">✓ 已生成思维导图</p>' : ''}
                `;
                div.onclick = () => showAlbumTracks(entry.album_id, entry.album_title);
                historyList.appendChild(div);
            });
        }
        
        function closeModal() {
            document.getElementById('albumModal').style.display = 'none';
        }
        
        // 页面加载时加载历史记录
        loadHistory();
    </script>
</body>
</html>
```

### 6.5 添加导航链接

在 `app.py` 中添加路由：

```python
@app.route('/ximalaya')
def ximalaya_page():
    """喜马拉雅音频学习页面"""
    return render_template('ximalaya.html')
```

---

## 🔑 第七步：配置环境变量

在 `.env` 文件中添加：

```bash
# 喜马拉雅 API 配置
XIMALAYA_APP_KEY=your_app_key_here
XIMALAYA_CLIENT_SECRET=your_client_secret_here

# DashScope API Key（用于语音识别）
DASHSCOPE_API_KEY=your_dashscope_api_key
```

---

## 📊 第八步：数据回传（必须）

根据喜马拉雅要求，必须接入以下数据回传接口才能上线：

### 8.1 播放数据回传
```python
def report_play(track_id: str, play_duration: int):
    """回传播放数据"""
    url = "https://api.ximalaya.com/data/report/play"
    params = _get_common_params()
    params.update({
        'track_id': track_id,
        'play_duration': play_duration  # 秒
    })
    requests.post(url, data=params)
```

### 8.2 浏览数据回传
```python
def report_view(album_id: str):
    """回传浏览数据"""
    url = "https://api.ximalaya.com/data/report/view"
    params = _get_common_params()
    params.update({
        'album_id': album_id
    })
    requests.post(url, data=params)
```

---

## ✅ 第九步：测试与上线

### 9.1 测试清单
- [ ] API 签名验证通过
- [ ] 搜索接口正常返回
- [ ] 音频下载功能正常
- [ ] 语音识别功能正常（如有文本提取需求）
- [ ] 思维导图生成功能正常
- [ ] 历史记录功能正常
- [ ] 数据回传接口调用成功
- [ ] IP 白名单配置正确

### 9.2 提交审核
1. 在【应用中心】完善应用信息
2. 确保数据回传接口已接入
3. 提交应用审核
4. 等待审核通过（通常 1-3 个工作日）

---

## 📞 技术支持

- 商务合作热线：(021)50179077-8806 / 8803
- 开放平台：https://open.ximalaya.com/
- 技术文档：https://open.ximalaya.com/doc/

---

## ⚠️ 注意事项

1. **签名安全**：`client_secret` 仅在服务器端使用，不要暴露给前端
2. **请求频率**：注意 API 调用频率限制，避免被封禁
3. **版权合规**：仅使用已授权的内容，遵守喜马拉雅版权规范
4. **域名白名单**：如有 CDN 域名限制，需将 `*.xmcdn.com` 加入白名单
5. **设备 ID**：服务器场景可使用 UUID，移动端需按规范回传 OAID/IDFA
6. **存储空间**：音频文件会占用服务器存储空间，定期清理旧文件
7. **语音识别成本**：DashScope 语音识别会产生费用，注意控制调用量

---

_文档创建时间：2026-03-26_  
_更新时间：2026-03-29 - 根据新需求重构（下载替代播放、文本提取、思维导图生成、历史记录）_
