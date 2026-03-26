#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""喜马拉雅 API 客户端

用于集成喜马拉雅音频内容到 Python 学习网站
支持搜索专辑、获取详情、播放地址等功能
"""

import hashlib
import time
import uuid
import requests
from typing import Dict, List, Optional
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XimalayaClient:
    """喜马拉雅 API 客户端"""
    
    def __init__(self, app_key: str = None, client_secret: str = None):
        """
        初始化客户端
        
        Args:
            app_key: 应用 Key（从喜马拉雅开放平台获取）
            client_secret: 客户端密钥
        """
        self.app_key = app_key or os.environ.get('XIMALAYA_APP_KEY', '')
        self.client_secret = client_secret or os.environ.get('XIMALAYA_CLIENT_SECRET', '')
        
        if not self.app_key:
            logger.warning("XIMALAYA_APP_KEY 未配置，部分功能将不可用")
        
        self.base_url = "https://api.ximalaya.com"
        self.backup_url = "https://apihera.ximalaya.com"  # 备用域名
        self.access_token = None
        self.token_expires_at = 0
    
    def _generate_signature(self, params: Dict) -> str:
        """
        生成 API 签名
        
        签名算法：
        1. 将所有参数按参数名 ASCII 码排序
        2. 拼接参数：key1=value1&key2=value2&...
        3. 拼接 client_secret
        4. MD5 加密
        
        Args:
            params: 参数字典
            
        Returns:
            签名值（32 位十六进制字符串）
        """
        # 1. 按参数名 ASCII 码排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 2. 拼接参数
        param_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # 3. 拼接 client_secret
        sign_string = f"{param_string}{self.client_secret}"
        
        # 4. MD5 加密
        sig = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        
        return sig
    
    def _get_common_params(self) -> Dict:
        """
        获取公共参数
        
        Returns:
            包含公共参数的字典
        """
        timestamp = str(int(time.time() * 1000))
        nonce = uuid.uuid4().hex
        
        params = {
            'app_key': self.app_key,
            'device_id': self._generate_device_id(),
            'client_os_type': '4',  # 4=Linux/Server
            'timestamp': timestamp,
            'nonce': nonce
        }
        
        # 生成签名
        params['sig'] = self._generate_signature(params)
        
        return params
    
    def _generate_device_id(self) -> str:
        """
        生成设备 ID
        
        服务器场景使用 UUID，移动端需按规范回传 OAID/IDFA
        
        Returns:
            设备 ID 字符串
        """
        return uuid.uuid4().hex
    
    def _request(self, method: str, url: str, params: Dict = None, data: Dict = None, 
                 use_backup: bool = False) -> Optional[Dict]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法（GET/POST）
            url: 请求 URL
            params: URL 参数
            data: POST 数据
            use_backup: 是否使用备用域名
            
        Returns:
            响应数据字典，失败返回 None
        """
        base = self.backup_url if use_backup else self.base_url
        full_url = f"{base}{url}" if not url.startswith('http') else url
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(full_url, params=params, headers=headers, timeout=10)
            else:
                response = requests.post(full_url, data=data or params, headers=headers, timeout=10)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败：{e}")
            # 尝试备用域名
            if not use_backup:
                logger.info("尝试使用备用域名...")
                return self._request(method, url, params, data, use_backup=True)
            return None
        except Exception as e:
            logger.error(f"解析响应失败：{e}")
            return None
    
    def search_albums(self, query: str, page: int = 1, count: int = 20, 
                      category_id: int = 0) -> Dict:
        """
        搜索专辑
        
        Args:
            query: 搜索关键词
            page: 页码（从 1 开始）
            count: 每页数量（最大 20）
            category_id: 分类 ID（0=全部分类）
            
        Returns:
            搜索结果字典，包含 albums 列表
        """
        url = "/search/albums"
        params = self._get_common_params()
        params.update({
            'q': query,
            'category_id': category_id,
            'calc_dimension': 1,  # 1=综合排序
            'page': page,
            'count': min(count, 20)  # 最多 20 条
        })
        
        result = self._request('GET', url, params=params)
        return result or {'error': '请求失败', 'albums': []}
    
    def get_album_detail(self, album_id: str) -> Dict:
        """
        获取专辑详情
        
        Args:
            album_id: 专辑 ID
            
        Returns:
            专辑详情字典
        """
        url = f"/album/{album_id}"
        params = self._get_common_params()
        
        result = self._request('GET', url, params=params)
        return result or {'error': '请求失败'}
    
    def get_tracks(self, album_id: str, page: int = 1, count: int = 20) -> Dict:
        """
        获取专辑声音列表
        
        Args:
            album_id: 专辑 ID
            page: 页码（从 1 开始）
            count: 每页数量（最大 20）
            
        Returns:
            声音列表字典，包含 tracks 列表
        """
        url = f"/album/{album_id}/tracks"
        params = self._get_common_params()
        params.update({
            'page': page,
            'count': min(count, 20)
        })
        
        result = self._request('GET', url, params=params)
        return result or {'error': '请求失败', 'tracks': []}
    
    def get_track_playurl(self, track_id: str) -> Dict:
        """
        获取声音播放地址
        
        Args:
            track_id: 声音 ID
            
        Returns:
            包含 play_url 的字典
        """
        url = f"/tracks/{track_id}/playurl"
        params = self._get_common_params()
        
        result = self._request('GET', url, params=params)
        return result or {'error': '请求失败'}
    
    def get_recommend_albums(self, category_id: int = 0, count: int = 20) -> Dict:
        """
        获取推荐专辑
        
        Args:
            category_id: 分类 ID（0=全部）
            count: 数量（最大 20）
            
        Returns:
            推荐专辑列表字典
        """
        url = "/recommend/albums"
        params = self._get_common_params()
        params.update({
            'category_id': category_id,
            'count': min(count, 20)
        })
        
        result = self._request('GET', url, params=params)
        return result or {'error': '请求失败', 'albums': []}
    
    def search_tracks(self, query: str, page: int = 1, count: int = 20) -> Dict:
        """
        搜索声音
        
        Args:
            query: 搜索关键词
            page: 页码
            count: 每页数量
            
        Returns:
            搜索结果字典
        """
        url = "/search/tracks"
        params = self._get_common_params()
        params.update({
            'q': query,
            'page': page,
            'count': min(count, 20)
        })
        
        result = self._request('GET', url, params=params)
        return result or {'error': '请求失败', 'tracks': []}
    
    def get_categories(self) -> Dict:
        """
        获取分类列表
        
        Returns:
            分类列表字典
        """
        url = "/categories"
        params = self._get_common_params()
        
        result = self._request('GET', url, params=params)
        return result or {'error': '请求失败', 'categories': []}
    
    # ============ 数据回传接口（必须接入才能上线）============
    
    def report_play(self, track_id: str, play_duration: int, 
                    device_id: str = None) -> bool:
        """
        回传播放数据
        
        Args:
            track_id: 声音 ID
            play_duration: 播放时长（秒）
            device_id: 设备 ID（可选，默认自动生成）
            
        Returns:
            是否成功
        """
        url = "/data/report/play"
        params = self._get_common_params()
        if device_id:
            params['device_id'] = device_id
        params.update({
            'track_id': track_id,
            'play_duration': play_duration
        })
        
        result = self._request('POST', url, data=params)
        return result is not None and result.get('ret') == 0
    
    def report_view(self, album_id: str, device_id: str = None) -> bool:
        """
        回传浏览数据
        
        Args:
            album_id: 专辑 ID
            device_id: 设备 ID（可选）
            
        Returns:
            是否成功
        """
        url = "/data/report/view"
        params = self._get_common_params()
        if device_id:
            params['device_id'] = device_id
        params['album_id'] = album_id
        
        result = self._request('POST', url, data=params)
        return result is not None and result.get('ret') == 0
    
    def report_exposure(self, album_id: str, position: int = 0,
                        device_id: str = None) -> bool:
        """
        回传曝光数据
        
        Args:
            album_id: 专辑 ID
            position: 曝光位置（列表中的索引）
            device_id: 设备 ID（可选）
            
        Returns:
            是否成功
        """
        url = "/data/report/exposure"
        params = self._get_common_params()
        if device_id:
            params['device_id'] = device_id
        params.update({
            'album_id': album_id,
            'position': position
        })
        
        result = self._request('POST', url, data=params)
        return result is not None and result.get('ret') == 0


# ============ 使用示例 ============

if __name__ == "__main__":
    # 从环境变量读取配置
    client = XimalayaClient()
    
    if not client.app_key:
        print("❌ 请先配置环境变量：")
        print("  export XIMALAYA_APP_KEY=your_app_key")
        print("  export XIMALAYA_CLIENT_SECRET=your_secret")
        exit(1)
    
    print("✅ 喜马拉雅客户端初始化成功")
    print(f"   App Key: {client.app_key[:8]}...")
    
    # 示例 1: 搜索专辑
    print("\n🔍 搜索 '英语听力'...")
    result = client.search_albums("英语听力", page=1, count=5)
    
    if 'albums' in result and result['albums']:
        print(f"   找到 {len(result['albums'])} 个专辑:")
        for i, album in enumerate(result['albums'][:3], 1):
            print(f"   {i}. {album.get('title', 'N/A')}")
            print(f"      声音数：{album.get('track_count', 0)}")
            print(f"      封面：{album.get('cover_url', 'N/A')[:50]}...")
    
    # 示例 2: 获取专辑详情
    if 'albums' in result and result['albums']:
        album_id = result['albums'][0]['id']
        print(f"\n📚 获取专辑详情 (ID: {album_id})...")
        detail = client.get_album_detail(album_id)
        if detail and 'error' not in detail:
            print(f"   标题：{detail.get('title', 'N/A')}")
            print(f"   主播：{detail.get('nickname', 'N/A')}")
            print(f"   简介：{detail.get('description', 'N/A')[:100]}...")
    
    # 示例 3: 获取声音列表
    if 'albums' in result and result['albums']:
        album_id = result['albums'][0]['id']
        print(f"\n🎵 获取声音列表...")
        tracks = client.get_tracks(album_id, page=1, count=5)
        
        if 'tracks' in tracks and tracks['tracks']:
            print(f"   找到 {len(tracks['tracks'])} 个声音:")
            for i, track in enumerate(tracks['tracks'][:3], 1):
                print(f"   {i}. {track.get('title', 'N/A')}")
                print(f"      时长：{track.get('duration', 0)}秒")
    
    print("\n✅ 测试完成!")
