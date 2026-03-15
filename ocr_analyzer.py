#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 题目分析器 - 拍照建题核心逻辑
集成：OCR 识别 + 视觉大模型分析 + 自动建题
"""

import os
import sys
import json
import base64
import hashlib
import shutil
import http.client
import ssl
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

# 导入题库管理
from ocr_question_manager import add_ocr_question, init_db


class OCRQuestionAnalyzer:
    """OCR 题目分析器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化分析器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key') or os.environ.get('DASHSCOPE_API_KEY', '')
        self.model = self.config.get('model', 'qwen-vl-max')
        
        # 上传目录
        self.base_dir = Path(__file__).parent
        self.upload_dir = self.base_dir / 'static' / 'uploads' / 'ocr-questions'
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        init_db()
    
    def save_image(self, image_path: str) -> str:
        """
        保存图片到上传目录
        
        Returns:
            相对路径（用于数据库存储）
        """
        src = Path(image_path)
        if not src.exists():
            raise FileNotFoundError(f"图片文件不存在：{image_path}")
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = hashlib.md5(src.read_bytes()).hexdigest()[:8]
        ext = src.suffix.lower()
        filename = f"question-{timestamp}-{file_hash}{ext}"
        
        # 按日期组织目录
        date_dir = datetime.now().strftime('%Y-%m')
        dest_dir = self.upload_dir / date_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = dest_dir / filename
        
        # 复制文件
        shutil.copy2(src, dest_path)
        
        # 返回相对路径（用于 web 访问）
        return f"static/uploads/ocr-questions/{date_dir}/{filename}"
    
    def analyze_image(self, image_path: str, custom_prompt: str = None) -> Dict:
        """
        使用视觉大模型分析题目图片
        
        Args:
            image_path: 图片路径
            custom_prompt: 自定义分析提示词
            
        Returns:
            分析结果字典
        """
        # 编码图片
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 默认提示词（针对数学题目优化）
        if custom_prompt is None:
            prompt = """
你是一位经验丰富的数学竞赛教练（AMC8/AMC10）。请分析这张图片中的数学题目。

请完成以下任务：
1. 完整识别题目文字（包括中文和英文）
2. 识别所有数学公式（用 LaTeX 格式表示）
3. 分析题目考查的知识点
4. 给出详细的解题步骤
5. 分析解题思路和关键突破点
6. 指出易错点和注意事项
7. 给出最终答案
8. 提取关键词标签

请严格按照以下 JSON 格式返回（只输出 JSON，不要其他文字）：

{
    "topic_text": "完整的题目文字（整理后，中文）",
    "topic_text_en": "英文题目（如果有）",
    "knowledge_points": ["知识点 1", "知识点 2"],
    "difficulty": "easy/medium/hard",
    "solution_steps": ["步骤 1", "步骤 2", "步骤 3"],
    "solution_thought": "解题思路分析（关键突破点、为什么想到这个方法）",
    "answer": "最终答案",
    "keywords": ["#标签 1", "#标签 2", "#标签 3"],
    "common_mistakes": ["易错点 1", "易错点 2"],
    "lesson_suggestion": "建议的课程分类（如 Lesson-12-勾股定理）",
    "subject": "学科（如 Math/数学）",
    "category": "题目类型（如 数论/几何/代数/组合）"
}

注意：
1. 数学公式用 LaTeX 格式：$x^2$, $\\frac{a}{b}$, $\\sqrt{n}$, $a^2 + b^2 = c^2$
2. 方程组用 cases 环境：$\\begin{cases} x+y=10 \\\\ x-y=4 \\end{cases}$
3. 几何符号：$\\triangle ABC$, $\\angle A$, $\\perp$, $\\parallel$, $\\odot O$
4. keywords 使用 # 标签格式
5. difficulty 使用 easy/medium/hard
"""
        else:
            prompt = custom_prompt
        
        # 构建请求 - 使用阿里云 DashScope 的 URL 格式
        # 注意：qwen-vl-max 支持 base64 编码的图片，但格式略有不同
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
        
        # 发送请求
        try:
            conn = http.client.HTTPSConnection("dashscope.aliyuncs.com")
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
                
                # 多模态模型返回的是数组，需要提取文本
                if isinstance(content, list):
                    text = content[0].get('text', '') if content else ''
                else:
                    text = content
                
                # 提取 JSON（可能包含在 markdown 代码块中）
                import re
                json_match = re.search(r'```json\s*(.+?)\s*```', text, re.DOTALL)
                if json_match:
                    text = json_match.group(1)
                else:
                    json_match = re.search(r'\{.+?\}', text, re.DOTALL)
                    if json_match:
                        text = json_match.group(0)
                
                try:
                    analysis = json.loads(text)
                    return analysis
                except json.JSONDecodeError as e:
                    return {
                        'error': f'JSON 解析失败: {e}',
                        'raw_text': text[:1000]
                    }
            else:
                return {
                    'error': 'API 响应格式异常',
                    'raw_response': result_json
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'message': 'API 调用失败，请检查网络和 API Key'
            }
    
    def process_and_save(
        self,
        image_path: str,
        subject: str = 'Math',
        category: str = None,
        lesson: str = None,
        source: str = '',
        custom_prompt: str = None
    ) -> Dict:
        """
        完整处理流程：保存图片 → OCR 分析 → 存入数据库
        
        Args:
            image_path: 题目图片路径
            subject: 学科
            category: 分类
            lesson: 课程/章节
            source: 题目来源
            custom_prompt: 自定义提示词
            
        Returns:
            处理结果
        """
        # 1. 保存图片
        saved_path = self.save_image(image_path)
        
        # 2. AI 分析
        analysis = self.analyze_image(image_path, custom_prompt)
        
        # 3. 检查分析结果
        topic_text = analysis.get('topic_text', '')
        
        # 如果 topic_text 是JSON字符串（嵌套JSON问题），尝试解析
        if topic_text and isinstance(topic_text, str) and topic_text.strip().startswith('{'):
            try:
                nested = json.loads(topic_text)
                if isinstance(nested, dict) and 'topic_text' in nested:
                    # 提取嵌套的字段
                    topic_text = nested.get('topic_text', '')
                    analysis['topic_text_en'] = nested.get('topic_text_en', analysis.get('topic_text_en', ''))
                    analysis['knowledge_points'] = nested.get('knowledge_points', analysis.get('knowledge_points', []))
                    analysis['difficulty'] = nested.get('difficulty', analysis.get('difficulty', 'medium'))
                    analysis['solution_steps'] = nested.get('solution_steps', analysis.get('solution_steps', []))
                    analysis['solution_thought'] = nested.get('solution_thought', analysis.get('solution_thought', ''))
                    analysis['answer'] = nested.get('answer', analysis.get('answer', '待计算'))
                    analysis['keywords'] = nested.get('keywords', analysis.get('keywords', []))
                    analysis['common_mistakes'] = nested.get('common_mistakes', analysis.get('common_mistakes', []))
            except json.JSONDecodeError:
                pass  # 不是有效的JSON，保持原样
        
        if not topic_text or topic_text == '待识别':
            topic_text = analysis.get('raw_text', '[识别失败，请手动编辑]')
        
        # 4. 使用用户指定的分类或分析结果
        final_category = category or analysis.get('category', '未分类')
        final_lesson = lesson or analysis.get('lesson_suggestion', '')
        
        # 5. 存入数据库
        question_id = add_ocr_question(
            subject=subject,
            category=final_category,
            lesson=final_lesson,
            topic_text=topic_text,
            topic_text_en=analysis.get('topic_text_en', ''),
            knowledge_points=analysis.get('knowledge_points', []),
            difficulty=analysis.get('difficulty', 'medium'),
            solution_steps=analysis.get('solution_steps', []),
            solution_thought=analysis.get('solution_thought', ''),
            answer=analysis.get('answer', '待计算'),
            keywords=analysis.get('keywords', []),
            common_mistakes=analysis.get('common_mistakes', []),
            image_path=saved_path,
            ocr_raw=analysis.get('raw_text', ''),
            analysis_json=analysis,
            source=source
        )
        
        return {
            'question_id': question_id,
            'image_path': saved_path,
            'analysis': analysis,
            'category': final_category,
            'lesson': final_lesson
        }
    
    def batch_process(
        self,
        image_dir: str,
        subject: str = 'Math',
        category: str = None,
        lesson: str = None
    ) -> Dict:
        """
        批量处理图片
        
        Args:
            image_dir: 图片目录
            subject: 学科
            category: 分类
            lesson: 课程
            
        Returns:
            处理统计
        """
        image_dir = Path(image_dir)
        if not image_dir.exists():
            raise FileNotFoundError(f"目录不存在：{image_dir}")
        
        # 查找所有图片
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            image_files.extend(image_dir.glob(ext))
        
        print(f"📁 发现 {len(image_files)} 张图片")
        
        results = {
            'total': len(image_files),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for img in image_files:
            try:
                result = self.process_and_save(
                    str(img),
                    subject=subject,
                    category=category,
                    lesson=lesson
                )
                results['success'] += 1
                results['details'].append({
                    'file': str(img),
                    'status': 'success',
                    'question_id': result['question_id']
                })
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'file': str(img),
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results


# 便捷函数
def analyze_question_image(image_path: str, api_key: str = None) -> Dict:
    """
    便捷函数：分析单张题目图片
    
    Args:
        image_path: 图片路径
        api_key: API Key（可选）
        
    Returns:
        分析结果
    """
    config = {'api_key': api_key} if api_key else {}
    analyzer = OCRQuestionAnalyzer(config)
    return analyzer.analyze_image(image_path)


def add_question_from_image(
    image_path: str,
    subject: str = 'Math',
    category: str = None,
    lesson: str = None,
    api_key: str = None
) -> int:
    """
    便捷函数：从图片添加题目到数据库
    
    Returns:
        题目 ID
    """
    config = {'api_key': api_key} if api_key else {}
    analyzer = OCRQuestionAnalyzer(config)
    result = analyzer.process_and_save(
        image_path,
        subject=subject,
        category=category,
        lesson=lesson
    )
    return result['question_id']


# 初始化管理
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='OCR 题目分析工具')
    parser.add_argument('image', help='题目图片路径')
    parser.add_argument('--category', help='分类')
    parser.add_argument('--lesson', help='课程/章节')
    parser.add_argument('--batch', help='批量处理目录')
    parser.add_argument('--api-key', help='API Key（可选）')
    
    args = parser.parse_args()
    
    analyzer = OCRQuestionAnalyzer({'api_key': args.api_key})
    
    if args.batch:
        results = analyzer.batch_process(args.batch)
        print(f"\n📊 处理统计:")
        print(f"   总计：{results['total']}")
        print(f"   成功：{results['success']}")
        print(f"   失败：{results['failed']}")
    else:
        result = analyzer.process_and_save(
            args.image,
            category=args.category,
            lesson=args.lesson
        )
        print(f"\n📊 分析摘要:")
        print(f"   题目 ID: {result['question_id']}")
        print(f"   分类：{result['category']}")
        print(f"   知识点：{', '.join(result['analysis'].get('knowledge_points', []))}")
