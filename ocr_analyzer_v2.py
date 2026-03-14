#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 题目分析器 - 使用文本模型分析（无需视觉模型）
流程：本地 OCR 识别文字 → 文本模型分析题目
"""

import os
import sys
import json
import base64
import hashlib
import shutil
import http.client
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# 导入题库管理
from ocr_question_manager import add_ocr_question, init_db


class OCRQuestionAnalyzer:
    """OCR 题目分析器（文本模型版本）"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key') or os.environ.get('DASHSCOPE_API_KEY', '')
        self.model = self.config.get('model', 'qwen-max')
        
        # 上传目录
        self.base_dir = Path(__file__).parent
        self.upload_dir = self.base_dir / 'static' / 'uploads' / 'ocr-questions'
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        init_db()
    
    def save_image(self, image_path: str) -> str:
        """保存图片到上传目录"""
        src = Path(image_path)
        if not src.exists():
            raise FileNotFoundError(f"图片文件不存在：{image_path}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_hash = hashlib.md5(src.read_bytes()).hexdigest()[:8]
        ext = src.suffix.lower()
        filename = f"question-{timestamp}-{file_hash}{ext}"
        
        date_dir = datetime.now().strftime('%Y-%m')
        dest_dir = self.upload_dir / date_dir
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        dest_path = dest_dir / filename
        shutil.copy2(src, dest_path)
        
        return f"static/uploads/ocr-questions/{date_dir}/{filename}"
    
    def ocr_with_tesseract(self, image_path: str) -> str:
        """使用 Tesseract 进行 OCR 识别"""
        try:
            # 检查 tesseract 是否安装
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            
            # 执行 OCR（中文 + 英文）
            output = subprocess.run(
                ['tesseract', image_path, 'stdout', '-l', 'chi_sim+eng'],
                capture_output=True, text=True, timeout=30
            )
            
            return output.stdout.strip()
        except FileNotFoundError:
            return ""
        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            print(f"Tesseract OCR 失败：{e}")
            return ""
    
    def ocr_with_api(self, image_path: str) -> str:
        """使用阿里云 OCR API"""
        # 简化版本：直接返回图片路径，让用户手动输入
        return f"[图片：{image_path}]"
    
    def analyze_text(self, ocr_text: str, image_hint: str = "") -> Dict:
        """
        使用文本模型分析 OCR 识别的文字
        
        Args:
            ocr_text: OCR 识别的文字
            image_hint: 图片提示（如分类信息）
            
        Returns:
            分析结果字典
        """
        prompt = f"""你是一位经验丰富的数学竞赛教练（AMC8/AMC10）。请分析以下识别自图片的数学题目文字。

【识别的文字内容】
{ocr_text}

{image_hint if image_hint else ''}

注意：以上文字是从图片中 OCR 识别的，可能有不准确或缺漏的地方。请根据上下文理解题目意思。

请完成以下任务：
1. 整理题目文字（修正 OCR 错误）
2. 分析题目考查的知识点
3. 给出详细的解题步骤
4. 分析解题思路和关键突破点
5. 指出易错点和注意事项
6. 给出最终答案
7. 提取关键词标签
8. 评估题目难度

请严格按照以下 JSON 格式返回（只输出 JSON，不要其他文字）：

{{
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
    "category": "题目类型（如 数论/几何/代数/组合）"
}}

注意：
1. 数学公式用 LaTeX 格式：$x^2$, $\\frac{{a}}{{b}}$, $\\sqrt{{n}}$
2. keywords 使用 # 标签格式
3. difficulty 使用 easy/medium/hard
"""
        
        # 构建请求
        request_body = json.dumps({
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位 AMC8 数学竞赛专家，擅长分析题目并给出清晰的解题步骤。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "result_format": "message",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        })
        
        try:
            conn = http.client.HTTPSConnection("dashscope.aliyuncs.com", timeout=60)
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            conn.request(
                "POST",
                "/api/v1/services/aigc/text-generation/generation",
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
                
                # 提取 JSON
                import re
                json_match = re.search(r'```json\s*(.+?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
                else:
                    json_match = re.search(r'\{.+?\}', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(0)
                
                analysis = json.loads(content)
                return analysis
            else:
                return {
                    'error': 'API 响应格式异常',
                    'raw_response': result_json
                }
                
        except Exception as e:
            return {
                'error': str(e),
                'message': 'API 调用失败'
            }
    
    def process_and_save(
        self,
        image_path: str,
        subject: str = 'Math',
        category: str = None,
        lesson: str = None,
        source: str = '',
        use_tesseract: bool = True
    ) -> Dict:
        """
        完整处理流程：保存图片 → OCR → 分析 → 存入数据库
        """
        print(f"\n📸 开始处理题目：{image_path}")
        
        # 1. 保存图片
        print("  ① 保存图片...")
        saved_path = self.save_image(image_path)
        print(f"     保存位置：{saved_path}")
        
        # 2. OCR 识别
        print("  ② OCR 识别...")
        ocr_text = ""
        
        if use_tesseract:
            ocr_text = self.ocr_with_tesseract(image_path)
            if ocr_text:
                print(f"     Tesseract 识别：{len(ocr_text)} 字符")
            else:
                print(f"     ⚠️  Tesseract 失败，可能未安装")
        
        if not ocr_text:
            # 如果 OCR 失败，创建一个占位文本
            ocr_text = f"[图片题目：{saved_path}]\n请手动补充题目内容"
            print(f"     使用占位文本")
        
        # 3. AI 分析
        print("  ③ AI 分析题目...")
        image_hint = f"分类：{category}, 课程：{lesson}" if category else ""
        analysis = self.analyze_text(ocr_text, image_hint)
        
        if 'error' in analysis:
            print(f"     ⚠️  分析警告：{analysis.get('error', '未知错误')}")
        
        # 4. 使用用户指定的分类或分析结果
        final_category = category or analysis.get('category', '未分类')
        final_lesson = lesson or analysis.get('lesson_suggestion', '')
        
        # 5. 存入数据库
        print("  ④ 存入数据库...")
        try:
            question_id = add_ocr_question(
                subject=subject,
                category=final_category,
                lesson=final_lesson,
                topic_text=analysis.get('topic_text', ocr_text),
                topic_text_en=analysis.get('topic_text_en', ''),
                knowledge_points=analysis.get('knowledge_points', []),
                difficulty=analysis.get('difficulty', 'medium'),
                solution_steps=analysis.get('solution_steps', []),
                solution_thought=analysis.get('solution_thought', ''),
                answer=analysis.get('answer', '待计算'),
                keywords=analysis.get('keywords', []),
                common_mistakes=analysis.get('common_mistakes', []),
                image_path=saved_path,
                ocr_raw=ocr_text,
                analysis_json=analysis,
                source=source
            )
            print(f"     ✅ 题目 ID: {question_id}")
        except Exception as e:
            print(f"     ❌ 数据库错误：{e}")
            raise
        
        print(f"\n✅ 完成！题目已保存")
        
        return {
            'question_id': question_id,
            'image_path': saved_path,
            'analysis': analysis,
            'category': final_category,
            'lesson': final_lesson,
            'ocr_text': ocr_text
        }


# 便捷函数
def analyze_existing_question(question_id: int, lesson: str = None) -> Dict:
    """
    重新分析已存在的题目
    
    Args:
        question_id: 题目 ID
        lesson: 课程提示
        
    Returns:
        分析结果
    """
    from ocr_question_manager import get_db
    
    # 获取题目信息
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ocr_questions WHERE id = ?', (question_id,))
    question = cursor.fetchone()
    conn.close()
    
    if not question:
        return {'error': '题目不存在'}
    
    # 创建分析器
    analyzer = OCRQuestionAnalyzer()
    
    # 获取图片路径
    image_path = Path(__file__).parent / question['image_path']
    if not image_path.exists():
        return {'error': '图片文件不存在'}
    
    # 重新分析
    result = analyzer.process_and_save(
        str(image_path),
        subject=question['subject'],
        category=question['category'],
        lesson=lesson or question['lesson'],
        source=question.get('source', '')
    )
    
    # 更新数据库
    conn = get_db()
    cursor = conn.cursor()
    
    analysis = result['analysis']
    cursor.execute('''
        UPDATE ocr_questions 
        SET topic_text = ?,
            topic_text_en = ?,
            knowledge_points = ?,
            difficulty = ?,
            solution_steps = ?,
            solution_thought = ?,
            answer = ?,
            keywords = ?,
            common_mistakes = ?,
            ocr_raw = ?,
            analysis_json = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        analysis.get('topic_text', question['topic_text']),
        analysis.get('topic_text_en', ''),
        json.dumps(analysis.get('knowledge_points', []), ensure_ascii=False),
        analysis.get('difficulty', 'medium'),
        json.dumps(analysis.get('solution_steps', []), ensure_ascii=False),
        analysis.get('solution_thought', ''),
        analysis.get('answer', '待计算'),
        json.dumps(analysis.get('keywords', []), ensure_ascii=False),
        json.dumps(analysis.get('common_mistakes', []), ensure_ascii=False),
        result['ocr_text'],
        json.dumps(analysis, ensure_ascii=False),
        question_id
    ))
    
    # 更新标签
    cursor.execute('DELETE FROM question_tags WHERE question_id = ?', (question_id,))
    keywords = analysis.get('keywords', [])
    if keywords:
        for kw in keywords:
            tag_name = kw.lstrip('#') if kw.startswith('#') else kw
            cursor.execute('''
                INSERT INTO question_tags (question_id, tag_name, tag_type)
                VALUES (?, ?, 'knowledge')
            ''', (question_id, tag_name))
    
    conn.commit()
    conn.close()
    
    return result


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='OCR 题目分析工具（文本模型版）')
    parser.add_argument('image', nargs='?', help='题目图片路径')
    parser.add_argument('--category', help='分类')
    parser.add_argument('--lesson', help='课程/章节')
    parser.add_argument('--question-id', type=int, help='重新分析已有题目 ID')
    
    args = parser.parse_args()
    
    if args.question_id:
        result = analyze_existing_question(args.question_id, args.lesson)
        print(f"\n📊 分析结果:")
        print(f"   知识点：{result.get('analysis', {}).get('knowledge_points', [])}")
        print(f"   难度：{result.get('analysis', {}).get('difficulty', 'medium')}")
    elif args.image:
        analyzer = OCRQuestionAnalyzer()
        result = analyzer.process_and_save(
            args.image,
            category=args.category,
            lesson=args.lesson
        )
        print(f"\n📊 分析摘要:")
        print(f"   题目 ID: {result['question_id']}")
        print(f"   OCR 文字：{result['ocr_text'][:100]}...")
