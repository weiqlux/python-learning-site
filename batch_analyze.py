#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量分析题库中的题目
重新识别和解析已上传但未分析的题目
"""

import os
import sys
import json
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from ocr_analyzer import OCRQuestionAnalyzer
import http.client
import base64

# 添加编码函数
def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

# 修复：使用正确的 API 端点
original_request = OCRQuestionAnalyzer.analyze_image

def fixed_analyze_image(self, image_path: str, prompt: str = None):
    """修复后的分析函数，使用 multimodal-generation 端点"""
    
    if prompt is None:
        prompt = """你是一位经验丰富的数学竞赛教练（AMC8/AMC10）。请分析这张图片中的数学题目。

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
    
    image_base64 = encode_image_to_base64(image_path)
    api_key = self.api_key or os.environ.get('DASHSCOPE_API_KEY', '')
    
    if not api_key:
        return {'error': '缺少 API Key'}
    
    request_body = json.dumps({
        "model": self.model,
        "input": {
            "messages": [{
                "role": "user",
                "content": [
                    {"image": f"data:image/jpeg;base64,{image_base64}"},
                    {"text": prompt}
                ]
            }]
        },
        "parameters": {"result_format": "message"}
    })
    
    try:
        conn = http.client.HTTPSConnection("dashscope.aliyuncs.com", timeout=90)
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        
        conn.request("POST", "/api/v1/services/aigc/multimodal-generation/generation", 
                    body=request_body, headers=headers)
        
        response = conn.getresponse()
        result = response.read().decode('utf-8')
        conn.close()
        
        if response.status == 200:
            result_json = json.loads(result)
            content = result_json['output']['choices'][0]['message']['content']
            
            # multimodal 返回的是数组
            if isinstance(content, list):
                text = content[0].get('text', '') if content else ''
            else:
                text = content
            
            # 提取 JSON
            import re
            json_match = re.search(r'```json\s*(.+?)\s*```', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            else:
                json_match = re.search(r'\{.+?\}', text, re.DOTALL)
                if json_match:
                    text = json_match.group(0)
            
            analysis = json.loads(text)
            return analysis
        else:
            return {'error': f'API 失败：{response.status}', 'raw': result}
            
    except Exception as e:
        return {'error': str(e)}

OCRQuestionAnalyzer.analyze_image = fixed_analyze_image
from ocr_question_manager import (
    get_questions_by_filter, get_db, 
    add_ocr_question, init_db as init_ocr_db
)

def batch_analyze_existing_questions(limit=10):
    """
    批量分析已存在的题目
    """
    print("=" * 60)
    print("🚀 开始批量分析题库中的题目")
    print("=" * 60)
    
    # 初始化
    init_ocr_db()
    analyzer = OCRQuestionAnalyzer()
    
    # 获取未分析的题目
    questions = get_questions_by_filter(limit=limit)
    
    if not questions:
        print("❌ 没有找到题目")
        return
    
    print(f"📊 找到 {len(questions)} 道题目待分析\n")
    
    results = {
        'total': len(questions),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for i, q in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"📸 处理第 {i}/{len(questions)} 题 (ID: {q['id']})")
        print(f"   分类：{q.get('category', '未分类')}")
        print(f"   课程：{q.get('lesson', '未分类')}")
        print(f"   图片：{q.get('image_path', '无')}")
        print(f"{'='*60}")
        
        try:
            # 检查图片是否存在
            image_path = Path(__file__).parent / q['image_path']
            if not image_path.exists():
                print(f"   ⚠️  图片文件不存在：{image_path}")
                results['failed'] += 1
                results['details'].append({
                    'question_id': q['id'],
                    'status': 'failed',
                    'error': '图片文件不存在'
                })
                continue
            
            # AI 分析
            print("   🤖 正在 AI 分析...")
            analysis = analyzer.analyze_image(str(image_path))
            
            if 'error' in analysis:
                print(f"   ⚠️  分析警告：{analysis.get('error', '未知错误')}")
            
            # 更新数据库
            print("   💾 更新数据库...")
            
            # 获取原题目数据
            topic_text = analysis.get('topic_text', q.get('topic_text', '待识别'))
            category = q.get('category') or analysis.get('category', 'AMC8')
            lesson = q.get('lesson') or analysis.get('lesson_suggestion', '')
            source = q.get('source', '')
            
            # 更新题目
            conn = get_db()
            cursor = conn.cursor()
            
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
                topic_text,
                analysis.get('topic_text_en', ''),
                json.dumps(analysis.get('knowledge_points', []), ensure_ascii=False),
                analysis.get('difficulty', 'medium'),
                json.dumps(analysis.get('solution_steps', []), ensure_ascii=False),
                analysis.get('solution_thought', ''),
                analysis.get('answer', '待计算'),
                json.dumps(analysis.get('keywords', []), ensure_ascii=False),
                json.dumps(analysis.get('common_mistakes', []), ensure_ascii=False),
                topic_text,
                json.dumps(analysis, ensure_ascii=False),
                q['id']
            ))
            
            # 更新标签
            cursor.execute('DELETE FROM question_tags WHERE question_id = ?', (q['id'],))
            keywords = analysis.get('keywords', [])
            if keywords:
                for kw in keywords:
                    tag_name = kw.lstrip('#') if kw.startswith('#') else kw
                    cursor.execute('''
                        INSERT INTO question_tags (question_id, tag_name, tag_type)
                        VALUES (?, ?, 'knowledge')
                    ''', (q['id'], tag_name))
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ 分析完成！")
            print(f"      知识点：{', '.join(analysis.get('knowledge_points', [])[:3])}")
            print(f"      难度：{analysis.get('difficulty', 'medium')}")
            print(f"      答案：{analysis.get('answer', '待计算')}")
            
            results['success'] += 1
            results['details'].append({
                'question_id': q['id'],
                'status': 'success',
                'analysis': analysis
            })
            
        except Exception as e:
            print(f"   ❌ 处理失败：{e}")
            results['failed'] += 1
            results['details'].append({
                'question_id': q['id'],
                'status': 'failed',
                'error': str(e)
            })
    
    # 统计结果
    print(f"\n{'='*60}")
    print("📊 批量分析完成！")
    print(f"{'='*60}")
    print(f"   总计：{results['total']}")
    print(f"   成功：{results['success']} ✅")
    print(f"   失败：{results['failed']} ❌")
    print(f"{'='*60}\n")
    
    return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='批量分析题库中的题目')
    parser.add_argument('--limit', type=int, default=10, help='处理题目数量（默认 10）')
    
    args = parser.parse_args()
    
    results = batch_analyze_existing_questions(limit=args.limit)
    
    # 输出成功题目详情
    if results and results['success'] > 0:
        print("✅ 成功分析的题目:")
        for detail in results['details']:
            if detail['status'] == 'success':
                qid = detail['question_id']
                analysis = detail.get('analysis', {})
                print(f"  - 题目{qid}: {analysis.get('topic_text', '无标题')[:50]}...")
