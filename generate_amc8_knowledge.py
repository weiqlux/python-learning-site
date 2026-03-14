#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMC8 知识讲义生成器
读取 Lesson 1-25 的 MD 文件，提取知识点，生成结构化讲义
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any


def parse_lesson_file(filepath: str) -> Dict[str, Any]:
    """解析单个 Lesson 文件，提取知识点"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取课程编号和名称
    filename = Path(filepath).stem
    lesson_match = re.match(r'Lesson\s+(\d+)\s+(.+)', filename)
    
    if lesson_match:
        lesson_num = int(lesson_match.group(1))
        lesson_name_en = lesson_match.group(2)
    else:
        lesson_num = 0
        lesson_name_en = filename
    
    # 提取中文标题（第一行 # 开头）
    lines = content.split('\n')
    lesson_name_cn = ""
    for line in lines[:10]:
        if line.startswith('# ') and '第' in line and '讲' in line:
            lesson_name_cn = line.replace('# ', '').strip()
            break
    
    # 提取知识点结构
    sections = []
    current_section = None
    
    for line in lines:
        # 一级标题（知识点类别）
        if line.startswith('# ') and '第' not in line:
            if current_section:
                sections.append(current_section)
            current_section = {
                'title': line.replace('# ', '').strip(),
                'content': [],
                'examples': []
            }
        
        # 二级标题（子知识点）
        elif line.startswith('## ') and current_section:
            current_section['content'].append({
                'type': 'subheading',
                'text': line.replace('## ', '').strip()
            })
        
        # 列表项（知识点内容）
        elif line.strip().startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')) and current_section:
            current_section['content'].append({
                'type': 'point',
                'text': line.strip()[3:].strip()
            })
        
        # 例题标记
        elif '**例题' in line or '## 例题' in line:
            if current_section:
                current_section['examples'].append({
                    'title': line.replace('**', '').replace('## ', '').strip(),
                    'content': []
                })
        
        # 例题内容
        elif current_section and current_section.get('examples') and line.strip():
            current_section['examples'][-1]['content'].append(line.strip())
    
    if current_section:
        sections.append(current_section)
    
    # 提取公式（LaTeX 格式）
    formulas = re.findall(r'\$[^$]+\$', content)
    formulas = list(set(formulas))[:20]  # 去重，最多 20 个
    
    # 提取关键概念（加粗文字）
    concepts = re.findall(r'\*\*([^*]+)\*\*', content)
    concepts = list(set([c for c in concepts if len(c) < 50]))[:15]  # 去重，短文本
    
    return {
        'lesson_num': lesson_num,
        'lesson_name_en': lesson_name_en,
        'lesson_name_cn': lesson_name_cn,
        'filename': filename,
        'sections': sections,
        'formulas': formulas,
        'concepts': concepts,
        'raw_content': content[:5000]  # 前 5000 字符用于预览
    }


def generate_knowledge_summary(lesson_data: Dict) -> Dict:
    """生成知识点摘要"""
    
    summary = {
        'lesson_num': lesson_data['lesson_num'],
        'title': lesson_data['lesson_name_cn'] or lesson_data['lesson_name_en'],
        'key_points': [],
        'formulas': lesson_data['formulas'][:10],
        'concepts': lesson_data['concepts'][:10]
    }
    
    # 提取关键知识点
    for section in lesson_data['sections']:
        if section['title'] and '例题' not in section['title']:
            summary['key_points'].append({
                'category': section['title'],
                'points': [item['text'] for item in section['content'] if item['type'] == 'point'][:5]
            })
    
    return summary


def create_amc8_knowledge_base():
    """创建 AMC8 知识库"""
    
    base_dir = Path('/home/admin/.openclaw/workspace/python-learning-site')
    
    # 查找所有 Lesson 文件
    lesson_files = sorted(base_dir.glob('Lesson *.md'))
    
    print(f"📚 找到 {len(lesson_files)} 个 Lesson 文件")
    
    all_lessons = []
    knowledge_summary = []
    
    for filepath in lesson_files:
        print(f"  解析: {filepath.name}")
        
        try:
            lesson_data = parse_lesson_file(str(filepath))
            all_lessons.append(lesson_data)
            
            summary = generate_knowledge_summary(lesson_data)
            knowledge_summary.append(summary)
        except Exception as e:
            print(f"    ❌ 解析失败: {e}")
    
    # 保存完整数据
    output_dir = base_dir / 'static' / 'amc8-knowledge'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存 JSON 数据
    with open(output_dir / 'amc8_lessons_full.json', 'w', encoding='utf-8') as f:
        json.dump(all_lessons, f, ensure_ascii=False, indent=2)
    
    with open(output_dir / 'amc8_knowledge_summary.json', 'w', encoding='utf-8') as f:
        json.dump(knowledge_summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 知识库已生成:")
    print(f"   - 完整数据: {output_dir / 'amc8_lessons_full.json'}")
    print(f"   - 知识点摘要: {output_dir / 'amc8_knowledge_summary.json'}")
    
    return all_lessons, knowledge_summary


if __name__ == '__main__':
    lessons, summary = create_amc8_knowledge_base()
    
    # 打印概览
    print(f"\n📊 AMC8 知识库概览:")
    print(f"   共 {len(lessons)} 个课程")
    
    for s in summary:
        print(f"\n   Lesson {s['lesson_num']}: {s['title']}")
        print(f"      知识点: {len(s['key_points'])} 个类别")
        print(f"      公式: {len(s['formulas'])} 个")
