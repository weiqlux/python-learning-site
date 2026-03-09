#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能题目添加 - OCR 识别 + 大模型分析"""

import os
import json
import base64
import http.client
import ssl
from datetime import datetime
from typing import Dict, Optional

# 使用 question_manager 添加题目
from question_manager import add_question

def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为 base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def analyze_with_vlm(image_path: str, prompt: str = None) -> Dict:
    """
    使用视觉语言模型分析图片（使用 HTTP 直接调用，无需 SDK）
    返回：原文、翻译、语法分析、重点词汇
    """
    if prompt is None:
        prompt = """
请分析这张图片中的英文文本，完成以下任务：

1. 提取图片中的英文原文（精确识别）
2. 将英文翻译成流畅的中文
3. 分析句子的语法结构（每个成分的词性和作用）
4. 列出重点词汇（单词、词性、中文意思、例句）
5. 给出翻译提示或技巧

请严格按照以下 JSON 格式返回：
{
    "original": "英文原文",
    "translation": "中文翻译",
    "structure_analysis": [
        {"text": "句子成分", "pos": "词性", "role": "在句中的作用"}
    ],
    "key_words": [
        {"word": "单词", "pos": "词性", "meaning": "中文意思", "example": "例句"}
    ],
    "tips": "翻译提示或技巧",
    "source_guess": "猜测的出处（如不确定则填'未知'）",
    "title_suggestion": "建议的题目名称"
}
"""

    # 读取并编码图片
    image_base64 = encode_image_to_base64(image_path)
    
    # 获取 API key
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    if not api_key:
        return {
            'error': '缺少 DASHSCOPE_API_KEY 环境变量',
            'message': '请设置：export DASHSCOPE_API_KEY="your-key"'
        }
    
    try:
        # 构建请求体
        request_body = json.dumps({
            "model": "qwen-vl-max",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": f"data:image/jpeg;base64,{image_base64}"},
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        })
        
        # 发送 HTTPS 请求
        conn = http.client.HTTPSConnection("dashscope.aliyuncs.com", timeout=60)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        conn.request("POST", "/api/v1/services/aigc/multimodal-generation/generation", request_body, headers)
        response = conn.getresponse()
        response_body = response.read().decode('utf-8')
        conn.close()
        
        if response.status == 200:
            result_data = json.loads(response_body)
            result_text = result_data['output']['choices'][0]['message']['content'][0]['text']
            
            # 解析 JSON 结果
            try:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = result_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    return {'error': '无法解析模型返回结果', 'raw': result_text}
            except json.JSONDecodeError as e:
                return {'error': f'JSON 解析失败：{str(e)}', 'raw': result_text}
        else:
            error_data = json.loads(response_body) if response_body else {}
            return {
                'error': f'API 调用失败：HTTP {response.status}',
                'message': error_data.get('message', response_body[:200])
            }
            
    except Exception as e:
        return {
            'error': f'识别失败：{str(e)}',
            'message': '请检查 API 配置和网络连接'
        }

def smart_add_question(image_path: str, category: str = "smart", auto_title: bool = True) -> Dict:
    """
    智能添加题目：上传图片 → OCR 识别 → 大模型分析 → 自动添加到题库
    
    参数：
        image_path: 图片文件路径
        category: 分类（默认 "smart"）
        auto_title: 是否使用模型建议的标题
    
    返回：
        添加结果（包含题目 ID 和分析结果）
    """
    # 检查文件是否存在
    if not os.path.exists(image_path):
        return {
            'success': False,
            'error': '图片文件不存在',
            'path': image_path
        }
    
    # 调用视觉模型分析
    analysis = analyze_with_vlm(image_path)
    
    if 'error' in analysis:
        return {
            'success': False,
            'error': analysis['error'],
            'message': analysis.get('message', '')
        }
    
    # 提取分析结果
    original = analysis.get('original', '')
    translation = analysis.get('translation', '')
    structure_analysis = analysis.get('structure_analysis', [])
    key_words = analysis.get('key_words', [])
    tips = analysis.get('tips', '')
    source = analysis.get('source_guess', '未知')
    title = analysis.get('title_suggestion', f'智能添加_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    
    if not original or not translation:
        return {
            'success': False,
            'error': '未能识别出有效内容',
            'analysis': analysis
        }
    
    # 添加到题库
    try:
        question_id = add_question(
            category=category,
            title=title,
            original=original,
            translation=translation,
            source=source,
            structure_analysis=structure_analysis,
            key_words=key_words,
            tips=tips,
            image_path=f"/static/uploads/{os.path.basename(image_path)}"
        )
        
        return {
            'success': True,
            'question_id': question_id,
            'analysis': analysis,
            'message': f'成功添加题目！ID: {question_id}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'添加题目失败：{str(e)}',
            'analysis': analysis
        }

# 命令行测试
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        result = smart_add_question(image_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("用法：python smart_add.py <图片路径>")
