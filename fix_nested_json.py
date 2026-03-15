#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复数据库中嵌套JSON的问题数据"""

import sqlite3
import json
import sys

DB_PATH = 'ocr_questions.db'

def fix_nested_json():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 找出所有 topic_text 以 { 开头的记录
    cursor.execute("SELECT id, topic_text, knowledge_points, solution_steps, answer FROM ocr_questions WHERE topic_text LIKE '{%' AND is_active = 1")
    rows = cursor.fetchall()
    
    print(f"找到 {len(rows)} 条需要修复的记录")
    
    fixed_count = 0
    for row in rows:
        try:
            # 尝试解析嵌套的JSON
            nested = json.loads(row['topic_text'])
            if isinstance(nested, dict):
                # 提取嵌套的字段
                new_topic_text = nested.get('topic_text', '')
                new_topic_text_en = nested.get('topic_text_en', '')
                new_knowledge_points = json.dumps(nested.get('knowledge_points', []), ensure_ascii=False)
                new_solution_steps = json.dumps(nested.get('solution_steps', []), ensure_ascii=False)
                new_solution_thought = nested.get('solution_thought', '')
                new_answer = nested.get('answer', '待计算')
                new_keywords = json.dumps(nested.get('keywords', []), ensure_ascii=False)
                new_common_mistakes = json.dumps(nested.get('common_mistakes', []), ensure_ascii=False)
                
                # 更新数据库
                cursor.execute('''
                    UPDATE ocr_questions 
                    SET topic_text = ?,
                        topic_text_en = ?,
                        knowledge_points = ?,
                        solution_steps = ?,
                        solution_thought = ?,
                        answer = ?,
                        keywords = ?,
                        common_mistakes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    new_topic_text,
                    new_topic_text_en,
                    new_knowledge_points,
                    new_solution_steps,
                    new_solution_thought,
                    new_answer,
                    new_keywords,
                    new_common_mistakes,
                    row['id']
                ))
                
                print(f"✅ 修复记录 ID={row['id']}: {new_topic_text[:50]}...")
                fixed_count += 1
        except json.JSONDecodeError as e:
            print(f"❌ 记录 ID={row['id']} JSON解析失败: {e}")
        except Exception as e:
            print(f"❌ 记录 ID={row['id']} 修复失败: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n总计修复: {fixed_count} 条记录")

if __name__ == '__main__':
    fix_nested_json()
