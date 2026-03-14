#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMC8 题目批量分析工具
使用阿里云文本模型分析题目（需要人工辅助输入题目文字）
"""

import os
import sys
import json
import http.client
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ocr_question_manager import get_db, get_questions_by_filter


def analyze_with_llm(topic_text: str, category: str = "AMC8", lesson: str = "") -> dict:
    """使用大模型分析题目文字"""
    
    api_key = os.environ.get('DASHSCOPE_API_KEY', '')
    if not api_key:
        return {'error': '缺少 API Key'}
    
    prompt = f"""你是一位经验丰富的 AMC8 数学竞赛教练。请分析以下数学题目：

【题目】
{topic_text}

【分类】{category}
【课程】{lesson}

请分析这道题，按 JSON 格式返回：

{{
    "knowledge_points": ["知识点 1", "知识点 2"],
    "difficulty": "easy/medium/hard",
    "solution_steps": ["步骤 1", "步骤 2"],
    "solution_thought": "解题思路分析",
    "answer": "最终答案",
    "keywords": ["#标签 1", "#标签 2"],
    "common_mistakes": ["易错点 1"]
}}

注意：
1. 数学公式用 LaTeX：$x^2$, $\\frac{{a}}{{b}}$
2. keywords 用 # 标签
3. difficulty 用 easy/medium/hard
"""
    
    request_body = json.dumps({
        "model": "qwen-max",
        "input": {
            "messages": [
                {"role": "system", "content": "你是 AMC8 数学竞赛专家。"},
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {"result_format": "message"}
    })
    
    try:
        conn = http.client.HTTPSConnection("dashscope.aliyuncs.com", timeout=60)
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        
        conn.request("POST", "/api/v1/services/aigc/text-generation/generation", 
                    body=request_body, headers=headers)
        
        response = conn.getresponse()
        result = response.read().decode('utf-8')
        conn.close()
        
        result_json = json.loads(result)
        
        if 'output' in result_json and 'choices' in result_json['output']:
            content = result_json['output']['choices'][0]['message']['content']
            
            # 提取 JSON
            import re
            json_match = re.search(r'\{.+?\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        
        return {'error': '解析失败'}
        
    except Exception as e:
        return {'error': str(e)}


def batch_analyze_with_input(questions: list) -> dict:
    """批量分析题目（需要人工输入题目文字）"""
    
    print("=" * 70)
    print("📝 AMC8 题目批量分析工具")
    print("=" * 70)
    print(f"共有 {len(questions)} 道题目需要分析\n")
    print("💡 使用方法：")
    print("   1. 查看题目图片路径")
    print("   2. 手动输入题目文字（或从图片识别后粘贴）")
    print("   3. AI 自动分析解题步骤和知识点")
    print("   4. 确认保存\n")
    
    results = {'total': len(questions), 'success': 0, 'failed': 0, 'skipped': 0}
    
    for i, q in enumerate(questions, 1):
        print(f"\n{'='*70}")
        print(f"题目 {i}/{len(questions)} (ID: {q['id']})")
        print(f"分类：{q.get('category', '未分类')} | 课程：{q.get('lesson', '未分类')}")
        print(f"图片：{q.get('image_path', '无')}")
        print(f"{'='*70}")
        
        # 显示当前题目信息
        if q.get('topic_text') and q['topic_text'] != '待识别':
            print(f"\n当前题目文字：{q['topic_text'][:200]}")
        
        # 询问是否跳过
        skip = input("\n是否跳过？(y/n，默认 n): ").strip().lower()
        if skip == 'y':
            results['skipped'] += 1
            continue
        
        # 输入题目文字
        print("\n请输入题目文字（直接回车使用现有文字，输入 'q' 退出）：")
        topic_text = input("> ").strip()
        
        if topic_text == 'q':
            print("退出批量分析")
            break
        
        if not topic_text:
            topic_text = q.get('topic_text', '')
        
        if not topic_text or topic_text == '待识别':
            print("⚠️  题目文字为空，跳过")
            results['failed'] += 1
            continue
        
        # AI 分析
        print("\n🤖 AI 正在分析...")
        analysis = analyze_with_llm(
            topic_text, 
            q.get('category', 'AMC8'), 
            q.get('lesson', '')
        )
        
        if 'error' in analysis:
            print(f"❌ 分析失败：{analysis['error']}")
            results['failed'] += 1
            continue
        
        # 显示分析结果
        print("\n✅ 分析结果:")
        print(f"   知识点：{', '.join(analysis.get('knowledge_points', []))}")
        print(f"   难度：{analysis.get('difficulty', 'medium')}")
        print(f"   答案：{analysis.get('answer', '待计算')}")
        print(f"   标签：{', '.join(analysis.get('keywords', []))}")
        
        # 确认保存
        confirm = input("\n是否保存？(y/n，默认 y): ").strip().lower()
        if confirm == 'n':
            print("已跳过")
            results['skipped'] += 1
            continue
        
        # 保存到数据库
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ocr_questions 
            SET topic_text = ?,
                knowledge_points = ?,
                difficulty = ?,
                solution_steps = ?,
                solution_thought = ?,
                answer = ?,
                keywords = ?,
                common_mistakes = ?,
                analysis_json = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            topic_text,
            json.dumps(analysis.get('knowledge_points', []), ensure_ascii=False),
            analysis.get('difficulty', 'medium'),
            json.dumps(analysis.get('solution_steps', []), ensure_ascii=False),
            analysis.get('solution_thought', ''),
            analysis.get('answer', '待计算'),
            json.dumps(analysis.get('keywords', []), ensure_ascii=False),
            json.dumps(analysis.get('common_mistakes', []), ensure_ascii=False),
            json.dumps(analysis, ensure_ascii=False),
            q['id']
        ))
        
        # 更新标签
        cursor.execute('DELETE FROM question_tags WHERE question_id = ?', (q['id'],))
        keywords = analysis.get('keywords', [])
        for kw in keywords:
            tag_name = kw.lstrip('#') if kw.startswith('#') else kw
            cursor.execute('INSERT INTO question_tags (question_id, tag_name, tag_type) VALUES (?, ?, ?)',
                          (q['id'], tag_name, 'knowledge'))
        
        conn.commit()
        conn.close()
        
        print("✅ 已保存！")
        results['success'] += 1
    
    # 统计
    print(f"\n{'='*70}")
    print("📊 批量分析完成！")
    print(f"{'='*70}")
    print(f"   总计：{results['total']}")
    print(f"   成功：{results['success']} ✅")
    print(f"   失败：{results['failed']} ❌")
    print(f"   跳过：{results['skipped']} ⏭️")
    print(f"{'='*70}\n")
    
    return results


if __name__ == '__main__':
    # 获取待分析的题目
    questions = get_questions_by_filter(limit=10)
    
    if not questions:
        print("❌ 没有找到题目")
        sys.exit(1)
    
    # 批量分析
    batch_analyze_with_input(questions)
