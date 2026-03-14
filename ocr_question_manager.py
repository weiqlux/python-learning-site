#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 题库管理模块 - 拍照建题专用
支持：数学公式、几何图形、选择题、解答题
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(__file__), 'ocr_questions.db')


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # OCR 题目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            lesson TEXT,
            topic_text TEXT NOT NULL,
            topic_text_en TEXT,
            knowledge_points TEXT,
            difficulty TEXT DEFAULT 'medium',
            solution_steps TEXT,
            solution_thought TEXT,
            answer TEXT,
            keywords TEXT,
            common_mistakes TEXT,
            image_path TEXT NOT NULL,
            ocr_raw TEXT,
            analysis_json TEXT,
            created_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            source TEXT
        )
    ''')
    
    # 题目标签表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            tag_name TEXT NOT NULL,
            tag_type TEXT DEFAULT 'knowledge',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES ocr_questions(id)
        )
    ''')
    
    # 答题记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_answer TEXT,
            is_correct INTEGER,
            time_spent INTEGER,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (question_id) REFERENCES ocr_questions(id)
        )
    ''')
    
    # 题目统计表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ocr_question_stats (
            question_id INTEGER PRIMARY KEY,
            total_attempts INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            avg_time_spent REAL DEFAULT 0,
            error_rate REAL DEFAULT 0,
            last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES ocr_questions(id)
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subject ON ocr_questions(subject)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON ocr_questions(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_lesson ON ocr_questions(lesson)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_difficulty ON ocr_questions(difficulty)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_date ON ocr_questions(created_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags ON question_tags(tag_name)')
    
    conn.commit()
    conn.close()


def add_ocr_question(
    subject: str,
    category: str,
    topic_text: str,
    image_path: str,
    topic_text_en: str = None,
    lesson: str = None,
    knowledge_points: List[str] = None,
    difficulty: str = 'medium',
    solution_steps: List[str] = None,
    solution_thought: str = '',
    answer: str = '',
    keywords: List[str] = None,
    common_mistakes: List[str] = None,
    ocr_raw: str = '',
    analysis_json: Dict = None,
    source: str = ''
) -> int:
    """
    添加 OCR 题目
    
    Returns:
        题目 ID
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO ocr_questions (
            subject, category, lesson, topic_text, topic_text_en,
            knowledge_points, difficulty, solution_steps, solution_thought,
            answer, keywords, common_mistakes, image_path, ocr_raw,
            analysis_json, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        subject,
        category,
        lesson,
        topic_text,
        topic_text_en,
        json.dumps(knowledge_points or [], ensure_ascii=False),
        difficulty,
        json.dumps(solution_steps or [], ensure_ascii=False),
        solution_thought,
        answer,
        json.dumps(keywords or [], ensure_ascii=False),
        json.dumps(common_mistakes or [], ensure_ascii=False),
        image_path,
        ocr_raw,
        json.dumps(analysis_json or {}, ensure_ascii=False),
        source
    ))
    
    question_id = cursor.lastrowid
    
    # 添加标签
    if keywords:
        for kw in keywords:
            tag_name = kw.lstrip('#') if kw.startswith('#') else kw
            cursor.execute('''
                INSERT INTO question_tags (question_id, tag_name, tag_type)
                VALUES (?, ?, 'knowledge')
            ''', (question_id, tag_name))
    
    conn.commit()
    conn.close()
    
    return question_id


def get_question(question_id: int) -> Optional[Dict]:
    """获取单个题目"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM ocr_questions WHERE id = ? AND is_active = 1', (question_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_questions_by_filter(
    subject: str = None,
    category: str = None,
    lesson: str = None,
    difficulty: str = None,
    keyword: str = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """根据条件筛选题目"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM ocr_questions WHERE is_active = 1'
    params = []
    
    if subject:
        query += ' AND subject = ?'
        params.append(subject)
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    if lesson:
        query += ' AND lesson LIKE ?'
        params.append(f'%{lesson}%')
    
    if difficulty:
        query += ' AND difficulty = ?'
        params.append(difficulty)
    
    if keyword:
        query += ' AND (topic_text LIKE ? OR knowledge_points LIKE ? OR keywords LIKE ?)'
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
    
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def search_questions(query_text: str, limit: int = 50) -> List[Dict]:
    """全文搜索题目"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM ocr_questions 
        WHERE is_active = 1 
        AND (topic_text LIKE ? OR knowledge_points LIKE ? OR answer LIKE ?)
        ORDER BY created_at DESC
        LIMIT ?
    ''', (f'%{query_text}%', f'%{query_text}%', f'%{query_text}%', limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_all_subjects() -> List[str]:
    """获取所有学科"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT subject FROM ocr_questions ORDER BY subject')
    rows = cursor.fetchall()
    conn.close()
    
    return [row['subject'] for row in rows]


def get_all_categories(subject: str = None) -> List[str]:
    """获取所有分类"""
    conn = get_db()
    cursor = conn.cursor()
    
    if subject:
        cursor.execute('SELECT DISTINCT category FROM ocr_questions WHERE subject = ? ORDER BY category', (subject,))
    else:
        cursor.execute('SELECT DISTINCT category FROM ocr_questions ORDER BY category')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row['category'] for row in rows]


def get_all_lessons(category: str = None) -> List[str]:
    """获取所有课程/章节"""
    conn = get_db()
    cursor = conn.cursor()
    
    if category:
        cursor.execute('SELECT DISTINCT lesson FROM ocr_questions WHERE category = ? AND lesson IS NOT NULL ORDER BY lesson', (category,))
    else:
        cursor.execute('SELECT DISTINCT lesson FROM ocr_questions WHERE lesson IS NOT NULL ORDER BY lesson')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row['lesson'] for row in rows]


def get_statistics() -> Dict:
    """获取题库统计信息"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # 总题目数
    cursor.execute('SELECT COUNT(*) as count FROM ocr_questions WHERE is_active = 1')
    stats['total_questions'] = cursor.fetchone()['count']
    
    # 按学科统计
    cursor.execute('''
        SELECT subject, COUNT(*) as count 
        FROM ocr_questions 
        WHERE is_active = 1 
        GROUP BY subject
    ''')
    stats['by_subject'] = {row['subject']: row['count'] for row in cursor.fetchall()}
    
    # 按难度统计
    cursor.execute('''
        SELECT difficulty, COUNT(*) as count 
        FROM ocr_questions 
        WHERE is_active = 1 
        GROUP BY difficulty
    ''')
    stats['by_difficulty'] = {row['difficulty']: row['count'] for row in cursor.fetchall()}
    
    # 最近添加
    cursor.execute('''
        SELECT id, topic_text, category, created_date 
        FROM ocr_questions 
        WHERE is_active = 1 
        ORDER BY created_at DESC 
        LIMIT 10
    ''')
    stats['recent_questions'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return stats


def record_answer(
    question_id: int,
    user_answer: str,
    is_correct: bool,
    time_spent: int = None,
    notes: str = ''
) -> int:
    """记录答题"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 添加答题记录
    cursor.execute('''
        INSERT INTO ocr_answers (question_id, user_answer, is_correct, time_spent, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (question_id, user_answer, 1 if is_correct else 0, time_spent, notes))
    
    answer_id = cursor.lastrowid
    
    # 更新统计
    cursor.execute('''
        INSERT OR REPLACE INTO ocr_question_stats (
            question_id, total_attempts, correct_count, avg_time_spent, error_rate, last_practiced
        )
        SELECT 
            ?,
            COALESCE((SELECT total_attempts FROM ocr_question_stats WHERE question_id = ?), 0) + 1,
            COALESCE((SELECT correct_count FROM ocr_question_stats WHERE question_id = ?), 0) + ?,
            (
                SELECT (COALESCE(avg_time_spent, 0) * COALESCE(total_attempts, 0) + COALESCE(?, 0)) 
                       / (COALESCE(total_attempts, 0) + 1)
                FROM ocr_question_stats WHERE question_id = ?
            ),
            1.0 - (COALESCE((SELECT correct_count FROM ocr_question_stats WHERE question_id = ?), 0) + ?) * 1.0 
                  / (COALESCE((SELECT total_attempts FROM ocr_question_stats WHERE question_id = ?), 0) + 1),
            CURRENT_TIMESTAMP
    ''', (question_id, question_id, question_id, 1 if is_correct else 0, time_spent, question_id, 
          1 if is_correct else 0, question_id, question_id))
    
    conn.commit()
    conn.close()
    
    return answer_id


def get_question_stats(question_id: int) -> Optional[Dict]:
    """获取题目统计"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM ocr_question_stats WHERE question_id = ?', (question_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def export_questions(format: str = 'json', filters: Dict = None) -> str:
    """导出题目"""
    questions = get_questions_by_filter(**filters) if filters else get_questions_by_filter()
    
    if format == 'json':
        return json.dumps(questions, ensure_ascii=False, indent=2)
    elif format == 'markdown':
        md = "# OCR 题库导出\n\n"
        for q in questions:
            md += f"## {q['topic_text']}\n\n"
            md += f"**分类：** {q['category']} | **难度：** {q['difficulty']}\n\n"
            md += f"**答案：** {q['answer']}\n\n"
            md += "---\n\n"
        return md
    
    return json.dumps(questions, ensure_ascii=False)


# 初始化管理
if __name__ == '__main__':
    init_db()
    print("✅ OCR 题库数据库初始化完成")
