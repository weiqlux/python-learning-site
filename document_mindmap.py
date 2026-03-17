#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档分析 + 思维导图生成器
支持：财务报表、流程图、架构图、思维导图等文档的智能分析和可视化
"""

import os
import sys
import json
import base64
import hashlib
import shutil
import http.client
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sqlite3
from PIL import Image
import io


class DocumentMindMapGenerator:
    """文档分析与思维导图生成器"""
    
    # 预设的分析场景
    SCENARIOS = {
        "financial_report": {
            "name": "财务报表分析",
            "description": "分析财务报表中的表格数据、增长趋势、关键指标",
            "system_prompt": """你是一位专业的财务分析师。请分析用户上传的财务报表图片。

请完成以下任务：
1. 提取表格中的所有数据
2. 计算关键财务指标（同比增长率、环比增长率等）
3. 识别异常数据和趋势
4. 生成结构化的分析结果

输出格式必须是严格的 JSON：
{
    "document_type": "financial_report",
    "title": "报表标题",
    "tables": [
        {
            "table_name": "表格名称",
            "headers": ["列1", "列2", "列3"],
            "rows": [["数据1", "数据2", "数据3"], ...]
        }
    ],
    "key_metrics": [
        {"name": "指标名称", "value": "数值", "change": "变化率", "trend": "up/down/stable"}
    ],
    "insights": ["洞察1", "洞察2"],
    "mindmap_structure": {
        "root": "报表主题",
        "children": [
            {
                "name": "一级节点",
                "children": [
                    {"name": "二级节点"},
                    {"name": "二级节点"}
                ]
            }
        ]
    }
}"""
        },
        "flowchart": {
            "name": "流程图解读",
            "description": "解读流程图逻辑、分支条件、执行路径",
            "system_prompt": """你是一位系统架构师。请分析用户上传的流程图。

请完成以下任务：
1. 识别流程图的所有节点和步骤
2. 分析流程的分支逻辑和判断条件
3. 识别关键路径和异常处理
4. 解释特定场景下的执行流程

输出格式必须是严格的 JSON：
{
    "document_type": "flowchart",
    "title": "流程图标题",
    "nodes": [
        {"id": "1", "type": "start/action/decision/end", "label": "节点描述"}
    ],
    "edges": [
        {"from": "1", "to": "2", "label": "条件/动作"}
    ],
    "paths": [
        {"name": "主流程", "steps": ["步骤1", "步骤2"]}
    ],
    "key_decisions": [
        {"condition": "判断条件", "true_path": "是分支", "false_path": "否分支"}
    ],
    "mindmap_structure": {
        "root": "流程主题",
        "children": [
            {
                "name": "开始/输入",
                "children": [{"name": "输入项1"}, {"name": "输入项2"}]
            },
            {
                "name": "处理逻辑",
                "children": [{"name": "判断条件"}, {"name": "处理步骤"}]
            },
            {
                "name": "输出/结果",
                "children": [{"name": "成功"}, {"name": "失败/异常"}]
            }
        ]
    }
}"""
        },
        "architecture": {
            "name": "架构图分析",
            "description": "分析系统架构图、组件关系、数据流向",
            "system_prompt": """你是一位资深系统架构师。请分析用户上传的系统架构图。

请完成以下任务：
1. 识别所有系统组件和模块
2. 分析组件之间的关系和依赖
3. 识别数据流向和接口
4. 评估架构特点

输出格式必须是严格的 JSON：
{
    "document_type": "architecture",
    "title": "架构图标题",
    "components": [
        {"name": "组件名", "type": "service/db/cache/gateway", "description": "功能描述"}
    ],
    "relationships": [
        {"from": "组件A", "to": "组件B", "type": "sync/async", "protocol": "HTTP/GRPC/..."}
    ],
    "data_flow": ["数据源", "处理", "存储", "展示"],
    "architecture_patterns": ["微服务", "分层架构", "事件驱动"],
    "mindmap_structure": {
        "root": "系统架构",
        "children": [
            {
                "name": "接入层",
                "children": [{"name": "API Gateway"}, {"name": "负载均衡"}]
            },
            {
                "name": "服务层",
                "children": [{"name": "业务服务A"}, {"name": "业务服务B"}]
            },
            {
                "name": "数据层",
                "children": [{"name": "数据库"}, {"name": "缓存"}]
            }
        ]
    }
}"""
        },
        "mindmap": {
            "name": "思维导图归纳",
            "description": "归纳思维导图要点、层级结构、核心主题",
            "system_prompt": """你是一位知识管理专家。请分析用户上传的思维导图。

请完成以下任务：
1. 提取思维导图的核心主题
2. 识别所有层级和分支结构
3. 归纳每个分支的要点
4. 发现知识点之间的关联

输出格式必须是严格的 JSON：
{
    "document_type": "mindmap",
    "title": "导图主题",
    "central_theme": "中心主题",
    "main_branches": [
        {
            "name": "主分支1",
            "key_points": ["要点1", "要点2"],
            "sub_branches": [
                {"name": "子分支1", "points": ["子要点"]},
                {"name": "子分支2", "points": ["子要点"]}
            ]
        }
    ],
    "summary": "整体总结",
    "mindmap_structure": {
        "root": "中心主题",
        "children": [
            {
                "name": "主分支1",
                "children": [
                    {"name": "子分支1"},
                    {"name": "子分支2"}
                ]
            }
        ]
    }
}"""
        },
        "general": {
            "name": "通用文档分析",
            "description": "分析任意文档，提取关键信息",
            "system_prompt": """你是一位文档分析专家。请分析用户上传的文档图片。

请完成以下任务：
1. 识别文档类型和内容结构
2. 提取关键信息和数据
3. 总结核心观点
4. 生成思维导图结构

输出格式必须是严格的 JSON：
{
    "document_type": "general",
    "title": "文档标题",
    "document_category": "文档类别",
    "key_content": ["要点1", "要点2", "要点3"],
    "data_extracted": [
        {"type": "table/text/chart", "content": "具体内容"}
    ],
    "summary": "文档总结",
    "mindmap_structure": {
        "root": "文档主题",
        "children": [
            {"name": "要点1", "children": [{"name": "细节1"}]},
            {"name": "要点2", "children": [{"name": "细节2"}]}
        ]
    }
}"""
        }
    }
    
    def __init__(self, config: Dict = None):
        """初始化生成器"""
        self.config = config or {}
        self.api_key = self.config.get('api_key') or os.environ.get('DASHSCOPE_API_KEY', '')
        self.model = self.config.get('model', 'qwen-vl-max')
        
        # 目录设置
        self.base_dir = Path(__file__).parent
        self.upload_dir = self.base_dir / 'static' / 'uploads' / 'documents'
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(str(self.base_dir / 'document_analysis.db'))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                document_type TEXT,
                document_title TEXT,
                image_path TEXT,
                analysis_result TEXT,
                mindmap_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES document_sessions(session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_db(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.base_dir / 'document_analysis.db'))
        conn.row_factory = sqlite3.Row
        return conn
    
    def compress_image(self, image_path: str, max_size: int = 800, quality: int = 75) -> bytes:
        """
        压缩图片以减少传输大小
        
        Args:
            image_path: 图片路径
            max_size: 最大边长（像素）
            quality: JPEG 质量（1-95）
            
        Returns:
            压缩后的图片 bytes
        """
        with Image.open(image_path) as img:
            # 转换为 RGB（处理 PNG 透明通道）
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # 等比例缩放
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # 保存到内存
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            return buffer.getvalue()
    
    def save_image(self, image_path: str) -> str:
        """保存图片到上传目录"""
        src = Path(image_path)
        if not src.exists():
            raise FileNotFoundError(f"图片文件不存在：{image_path}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = hashlib.md5(src.read_bytes()).hexdigest()[:8]
        ext = src.suffix.lower()
        filename = f"doc-{timestamp}-{file_hash}{ext}"
        
        date_dir = datetime.now().strftime('%Y-%m')
        dest_dir = self.upload_dir / date_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = dest_dir / filename
        shutil.copy2(src, dest_path)
        
        return f"static/uploads/documents/{date_dir}/{filename}"
    
    def analyze_document(
        self, 
        image_path: str, 
        question: str = None,
        scenario: str = "general",
        session_id: str = None
    ) -> Dict:
        """
        分析文档图片
        
        Args:
            image_path: 图片路径
            question: 用户问题（可选）
            scenario: 分析场景
            session_id: 会话ID（多轮对话用）
            
        Returns:
            分析结果
        """
        # 压缩并编码图片
        try:
            compressed_image = self.compress_image(image_path)
            image_base64 = base64.b64encode(compressed_image).decode('utf-8')
        except Exception as e:
            # 如果压缩失败，使用原图
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 获取场景配置
        scenario_config = self.SCENARIOS.get(scenario, self.SCENARIOS["general"])
        system_prompt = scenario_config["system_prompt"]
        
        # 构建用户问题
        if question:
            user_prompt = f"""
{system_prompt}

用户问题：{question}

请根据图片内容和用户问题进行分析，返回 JSON 格式结果。"""
        else:
            user_prompt = system_prompt
        
        # 构建请求
        request_body = json.dumps({
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": f"data:image/jpeg;base64,{image_base64}"
                            },
                            {
                                "text": user_prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        })
        
        # 发送请求
        try:
            conn = http.client.HTTPSConnection("dashscope.aliyuncs.com", timeout=60)
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            conn.request(
                "POST",
                "/api/v1/services/aigc/multimodal-generation/generation",
                body=request_body,
                headers=headers
            )
            
            response = conn.getresponse()
            result = response.read().decode('utf-8')
            conn.close()
            
            # 解析响应
            result_json = json.loads(result)
            
            if 'output' in result_json and 'choices' in result_json['output']:
                content = result_json['output']['choices'][0]['message']['content']
                
                if isinstance(content, list):
                    text = content[0].get('text', '') if content else ''
                else:
                    text = content
                
                # 提取 JSON
                analysis = self._extract_json(text)
                
                # 保存会话
                if not session_id:
                    session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(image_path.encode()).hexdigest()[:6]}"
                
                saved_path = self.save_image(image_path)
                self._save_session(session_id, scenario, saved_path, analysis, question)
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'analysis': analysis,
                    'mindmap_data': analysis.get('mindmap_structure', {})
                }
            else:
                return {
                    'success': False,
                    'error': 'API 响应格式异常',
                    'raw_response': result_json
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_json(self, text: str) -> Dict:
        """从文本中提取 JSON"""
        # 尝试匹配 markdown 代码块
        json_match = re.search(r'```json\s*(.+?)\s*```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)
        else:
            # 尝试匹配普通 JSON
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                text = json_match.group(0)
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            # 尝试修复常见 JSON 错误
            try:
                # 去除尾部逗号
                text = re.sub(r',(\s*[}\]])', r'\1', text)
                return json.loads(text)
            except:
                return {
                    'error': f'JSON 解析失败: {e}',
                    'raw_text': text[:2000]
                }
    
    def _save_session(
        self, 
        session_id: str, 
        document_type: str, 
        image_path: str, 
        analysis: Dict,
        question: str = None
    ):
        """保存会话到数据库"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute('SELECT id FROM document_sessions WHERE session_id = ?', (session_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE document_sessions 
                SET analysis_result = ?, mindmap_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (json.dumps(analysis, ensure_ascii=False), 
                  json.dumps(analysis.get('mindmap_structure', {}), ensure_ascii=False),
                  session_id))
        else:
            cursor.execute('''
                INSERT INTO document_sessions 
                (session_id, document_type, document_title, image_path, analysis_result, mindmap_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, document_type, 
                  analysis.get('title', '未命名文档'),
                  image_path,
                  json.dumps(analysis, ensure_ascii=False),
                  json.dumps(analysis.get('mindmap_structure', {}), ensure_ascii=False)))
        
        # 保存对话历史
        if question:
            cursor.execute('''
                INSERT INTO chat_history (session_id, role, content)
                VALUES (?, ?, ?)
            ''', (session_id, 'user', question))
            
            cursor.execute('''
                INSERT INTO chat_history (session_id, role, content)
                VALUES (?, ?, ?)
            ''', (session_id, 'assistant', json.dumps(analysis, ensure_ascii=False)))
        
        conn.commit()
        conn.close()
    
    def chat(
        self, 
        session_id: str, 
        question: str,
        image_path: str = None
    ) -> Dict:
        """
        多轮对话
        
        Args:
            session_id: 会话ID
            question: 用户问题
            image_path: 图片路径（可选，新图片）
            
        Returns:
            回答结果
        """
        # 获取历史会话
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM document_sessions WHERE session_id = ?
        ''', (session_id,))
        session = cursor.fetchone()
        
        if not session:
            conn.close()
            return {'success': False, 'error': '会话不存在'}
        
        # 获取历史对话
        cursor.execute('''
            SELECT role, content FROM chat_history 
            WHERE session_id = ? ORDER BY created_at
        ''', (session_id,))
        history = cursor.fetchall()
        conn.close()
        
        # 构建上下文
        context = []
        for h in history[-5:]:  # 最近5轮
            role, content = h
            if role == 'assistant':
                try:
                    content_json = json.loads(content)
                    content = content_json.get('summary', str(content_json)[:500])
                except:
                    pass
            context.append(f"{role}: {content}")
        
        context_str = "\n".join(context)
        
        # 获取图片并压缩
        img_path = image_path or session['image_path']
        if img_path and not img_path.startswith('/'):
            img_path = str(self.base_dir / img_path)
        
        try:
            compressed_image = self.compress_image(img_path)
            image_base64 = base64.b64encode(compressed_image).decode('utf-8')
        except Exception as e:
            # 如果压缩失败，使用原图
            with open(img_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 构建提示词
        prompt = f"""基于之前的文档分析，回答用户的新问题。

历史对话：
{context_str}

用户新问题：{question}

请直接回答用户的问题，可以引用文档中的具体数据或信息。如果问题涉及新的分析，请返回 JSON 格式，包含：
{{
    "answer": "直接回答",
    "referenced_data": ["引用的数据1", "数据2"],
    "additional_insights": ["额外洞察"]
}}"""
        
        # 发送请求
        request_body = json.dumps({
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "image": f"data:image/jpeg;base64,{image_base64}"
                            },
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        })
        
        try:
            conn_http = http.client.HTTPSConnection("dashscope.aliyuncs.com")
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            conn_http.request(
                "POST",
                "/api/v1/services/aigc/multimodal-generation/generation",
                body=request_body,
                headers=headers
            )
            
            response = conn_http.getresponse()
            result = response.read().decode('utf-8')
            conn_http.close()
            
            result_json = json.loads(result)
            
            if 'output' in result_json and 'choices' in result_json['output']:
                content = result_json['output']['choices'][0]['message']['content']
                
                if isinstance(content, list):
                    text = content[0].get('text', '') if content else ''
                else:
                    text = content
                
                # 尝试解析 JSON，否则直接返回文本
                try:
                    answer_data = self._extract_json(text)
                except:
                    answer_data = {"answer": text}
                
                # 保存对话
                conn = self._get_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chat_history (session_id, role, content)
                    VALUES (?, ?, ?)
                ''', (session_id, 'user', question))
                cursor.execute('''
                    INSERT INTO chat_history (session_id, role, content)
                    VALUES (?, ?, ?)
                ''', (session_id, 'assistant', json.dumps(answer_data, ensure_ascii=False)))
                conn.commit()
                conn.close()
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'answer': answer_data
                }
            else:
                return {
                    'success': False,
                    'error': 'API 响应异常'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话详情"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM document_sessions WHERE session_id = ?
        ''', (session_id,))
        session = cursor.fetchone()
        
        if not session:
            conn.close()
            return None
        
        # 获取对话历史
        cursor.execute('''
            SELECT role, content, created_at FROM chat_history 
            WHERE session_id = ? ORDER BY created_at
        ''', (session_id,))
        history = cursor.fetchall()
        
        conn.close()
        
        return {
            'session_id': session['session_id'],
            'document_type': session['document_type'],
            'document_title': session['document_title'],
            'image_path': session['image_path'],
            'analysis_result': json.loads(session['analysis_result'] or '{}'),
            'mindmap_data': json.loads(session['mindmap_data'] or '{}'),
            'created_at': session['created_at'],
            'chat_history': [
                {'role': h[0], 'content': h[1], 'time': h[2]} for h in history
            ]
        }
    
    def get_sessions(self, limit: int = 20) -> List[Dict]:
        """获取所有会话列表"""
        conn = self._get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT session_id, document_type, document_title, created_at
            FROM document_sessions
            ORDER BY updated_at DESC
            LIMIT ?
        ''', (limit,))
        
        sessions = cursor.fetchall()
        conn.close()
        
        return [
            {
                'session_id': s[0],
                'document_type': s[1],
                'document_title': s[2],
                'created_at': s[3]
            }
            for s in sessions
        ]
    
    def generate_mindmap_html(self, mindmap_data: Dict) -> str:
        """生成思维导图的 HTML 代码（使用 Markmap）"""
        if not mindmap_data:
            return "<p>暂无思维导图数据</p>"
        
        # 转换为 Markdown 格式
        def to_markdown(node, level=0):
            indent = "  " * level
            md = f"{indent}- {node.get('name', '未命名')}\n"
            for child in node.get('children', []):
                md += to_markdown(child, level + 1)
            return md
        
        markdown_content = to_markdown(mindmap_data)
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>思维导图</title>
    <script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.17"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        #mindmap {{ width: 100%; height: 80vh; }}
        .mindmap-container {{ border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; }}
    </style>
</head>
<body>
    <div class="mindmap-container">
        <div id="mindmap">
            <pre class="language-markdown">
{markdown_content}
            </pre>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const el = document.getElementById('mindmap');
            const markdown = el.querySelector('pre').textContent;
            markmap.autoLoader.render(el, markdown);
        }});
    </script>
</body>
</html>'''
        return html


# 便捷函数
def analyze_document(image_path: str, question: str = None, scenario: str = "general") -> Dict:
    """便捷函数：分析文档"""
    generator = DocumentMindMapGenerator()
    return generator.analyze_document(image_path, question, scenario)


def chat_with_document(session_id: str, question: str) -> Dict:
    """便捷函数：与文档对话"""
    generator = DocumentMindMapGenerator()
    return generator.chat(session_id, question)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='文档分析与思维导图生成器')
    parser.add_argument('image', help='文档图片路径')
    parser.add_argument('--question', '-q', help='分析问题')
    parser.add_argument('--scenario', '-s', default='general', 
                       choices=['financial_report', 'flowchart', 'architecture', 'mindmap', 'general'],
                       help='分析场景')
    parser.add_argument('--api-key', help='API Key')
    
    args = parser.parse_args()
    
    generator = DocumentMindMapGenerator({'api_key': args.api_key})
    result = generator.analyze_document(args.image, args.question, args.scenario)
    
    if result['success']:
        print(f"\n✅ 分析成功！")
        print(f"会话ID: {result['session_id']}")
        print(f"\n分析结果:")
        print(json.dumps(result['analysis'], ensure_ascii=False, indent=2))
    else:
        print(f"\n❌ 分析失败: {result.get('error')}")