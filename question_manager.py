#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""题库管理模块 - 支持动态添加、答题统计、难度分析"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'translation_questions.db')

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 题目表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            source TEXT,
            original TEXT NOT NULL,
            translation TEXT NOT NULL,
            structure_analysis TEXT,
            key_words TEXT,
            tips TEXT,
            image_path TEXT,
            created_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # 用户答题记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_answer TEXT NOT NULL,
            is_correct INTEGER,
            similarity_score REAL,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    
    # 题目难度统计表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS question_stats (
            question_id INTEGER PRIMARY KEY,
            total_attempts INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0,
            avg_similarity REAL DEFAULT 0,
            difficulty_level TEXT DEFAULT 'medium',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_question(category: str, title: str, original: str, translation: str,
                 source: str = "", structure_analysis: List = None,
                 key_words: List = None, tips: str = "", image_path: str = None) -> int:
    """添加新题目"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO questions (category, title, source, original, translation,
                              structure_analysis, key_words, tips, image_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        category, title, source, original, translation,
        json.dumps(structure_analysis, ensure_ascii=False) if structure_analysis else None,
        json.dumps(key_words, ensure_ascii=False) if key_words else None,
        tips, image_path
    ))
    
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 初始化统计记录
    init_question_stats(question_id)
    
    return question_id

def get_question(question_id: int) -> Optional[Dict]:
    """获取单个题目"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM questions WHERE id = ? AND is_active = 1', (question_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_questions_by_date(date: str = None) -> List[Dict]:
    """按日期获取题目"""
    conn = get_db()
    cursor = conn.cursor()
    
    if date:
        cursor.execute('''
            SELECT * FROM questions 
            WHERE created_date = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (date,))
    else:
        cursor.execute('''
            SELECT * FROM questions 
            WHERE is_active = 1
            ORDER BY created_date DESC, created_at DESC
        ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def search_questions(keyword: str, category: str = None) -> List[Dict]:
    """搜索题目"""
    conn = get_db()
    cursor = conn.cursor()
    
    if category:
        cursor.execute('''
            SELECT * FROM questions 
            WHERE is_active = 1 AND category = ?
            AND (title LIKE ? OR original LIKE ? OR translation LIKE ?)
            ORDER BY created_date DESC
        ''', (category, f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    else:
        cursor.execute('''
            SELECT * FROM questions 
            WHERE is_active = 1
            AND (title LIKE ? OR original LIKE ? OR translation LIKE ?)
            ORDER BY created_date DESC
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def record_answer(question_id: int, user_answer: str, correct_answer: str) -> Dict:
    """记录用户答题"""
    # 计算相似度（简单版本）
    similarity = calculate_similarity(user_answer, correct_answer)
    is_correct = similarity >= 0.8
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 记录答题
    cursor.execute('''
        INSERT INTO user_answers (question_id, user_answer, is_correct, similarity_score)
        VALUES (?, ?, ?, ?)
    ''', (question_id, user_answer, 1 if is_correct else 0, similarity))
    
    # 更新统计
    update_question_stats(question_id)
    
    conn.commit()
    conn.close()
    
    return {
        'is_correct': is_correct,
        'similarity': similarity,
        'message': '回答正确！🎉' if is_correct else '继续加油！💪'
    }

def calculate_similarity(s1: str, s2: str) -> float:
    """计算两个字符串的相似度（简单版本）"""
    s1, s2 = s1.strip().lower(), s2.strip().lower()
    if s1 == s2:
        return 1.0
    
    # 使用简单的字符匹配
    common = sum(1 for c in s1 if c in s2)
    return common / max(len(s1), len(s2))

def init_question_stats(question_id: int):
    """初始化题目统计"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO question_stats (question_id)
        VALUES (?)
    ''', (question_id,))
    
    conn.commit()
    conn.close()

def update_question_stats(question_id: int):
    """更新题目统计数据"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as total, 
               SUM(is_correct) as correct,
               AVG(similarity_score) as avg_sim
        FROM user_answers 
        WHERE question_id = ?
    ''', (question_id,))
    
    row = cursor.fetchone()
    total = row['total'] or 0
    correct = row['correct'] or 0
    avg_sim = row['avg_sim'] or 0
    
    # 计算难度等级
    if total == 0:
        difficulty = 'new'
    elif correct / total >= 0.8:
        difficulty = 'easy'
    elif correct / total >= 0.5:
        difficulty = 'medium'
    else:
        difficulty = 'hard'
    
    cursor.execute('''
        UPDATE question_stats 
        SET total_attempts = ?, correct_count = ?, avg_similarity = ?,
            difficulty_level = ?, last_updated = CURRENT_TIMESTAMP
        WHERE question_id = ?
    ''', (total, correct, avg_sim, difficulty, question_id))
    
    conn.commit()
    conn.close()

def get_questions_by_difficulty(difficulty: str = None, limit: int = 10) -> List[Dict]:
    """按难度获取题目"""
    conn = get_db()
    cursor = conn.cursor()
    
    if difficulty:
        cursor.execute('''
            SELECT q.*, s.total_attempts, s.correct_count, 
                   s.avg_similarity, s.difficulty_level
            FROM questions q
            JOIN question_stats s ON q.id = s.question_id
            WHERE q.is_active = 1 AND s.difficulty_level = ?
            ORDER BY s.total_attempts DESC
            LIMIT ?
        ''', (difficulty, limit))
    else:
        cursor.execute('''
            SELECT q.*, s.total_attempts, s.correct_count, 
                   s.avg_similarity, s.difficulty_level
            FROM questions q
            JOIN question_stats s ON q.id = s.question_id
            WHERE q.is_active = 1
            ORDER BY 
                CASE s.difficulty_level
                    WHEN 'hard' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'easy' THEN 3
                    ELSE 4
                END,
                s.total_attempts DESC
            LIMIT ?
        ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_hard_questions(min_attempts: int = 3) -> List[Dict]:
    """获取高难度题目（正确率低于 50% 且答题次数达到阈值）"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT q.*, s.total_attempts, s.correct_count, 
               s.avg_similarity, s.difficulty_level,
               ROUND(CAST(s.correct_count AS FLOAT) / s.total_attempts * 100, 1) as correct_rate
        FROM questions q
        JOIN question_stats s ON q.id = s.question_id
        WHERE q.is_active = 1 
          AND s.total_attempts >= ?
          AND s.difficulty_level = 'hard'
        ORDER BY s.avg_similarity ASC, s.total_attempts DESC
    ''', (min_attempts,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_all_categories() -> List[str]:
    """获取所有分类"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT DISTINCT category FROM questions WHERE is_active = 1')
    rows = cursor.fetchall()
    conn.close()
    
    return [row['category'] for row in rows]

def get_date_range() -> Dict:
    """获取题目的日期范围"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT MIN(created_date) as min_date, 
               MAX(created_date) as max_date 
        FROM questions 
        WHERE is_active = 1
    ''')
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        'min_date': row['min_date'],
        'max_date': row['max_date']
    }

# 初始化数据库
init_db()
