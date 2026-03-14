#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AMC8 题目分析自动化脚本
功能：OCR 识别题目图片 → 大模型分析 → 生成结构化 Markdown 文档
"""

import os
import sys
import json
import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# OCR 相关
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️  未安装 pytesseract，将使用 API 模式进行 OCR")

# HTTP 请求
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("❌ 未安装 requests 库，请运行：pip install requests")
    sys.exit(1)


class AMC8Analyzer:
    """AMC8 题目分析器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化分析器
        
        Args:
            config: 配置字典，包含 API key、路径等
        """
        self.config = config or self._load_default_config()
        self.base_dir = Path(self.config.get('base_dir', '/home/admin/.openclaw/workspace/AMC8'))
        self.memory_dir = self.base_dir / 'memory'
        self.media_dir = self.memory_dir / 'media'
        
        # 确保目录存在
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # 计数器文件
        self.counter_file = self.memory_dir / '.counter.json'
        self.topic_counter = self._load_counter()
        
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            'base_dir': '/home/admin/.openclaw/workspace/AMC8',
            'ocr_api_url': os.getenv('OCR_API_URL', ''),
            'ocr_api_key': os.getenv('OCR_API_KEY', ''),
            'llm_api_url': os.getenv('LLM_API_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'),
            'llm_api_key': os.getenv('LLM_API_KEY', ''),
            'llm_model': os.getenv('LLM_MODEL', 'qwen-max'),
        }
    
    def _load_counter(self) -> int:
        """加载题目计数器"""
        if self.counter_file.exists():
            with open(self.counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('counter', 0)
        return 0
    
    def _save_counter(self):
        """保存题目计数器"""
        with open(self.counter_file, 'w', encoding='utf-8') as f:
            json.dump({'counter': self.topic_counter}, f, ensure_ascii=False, indent=2)
    
    def _generate_topic_id(self) -> str:
        """生成题目 ID"""
        self.topic_counter += 1
        self._save_counter()
        return f"{self.topic_counter:03d}"
    
    def _save_image(self, image_path: str) -> str:
        """
        保存题目图片到 media 目录
        
        Args:
            image_path: 原始图片路径
            
        Returns:
            保存后的媒体路径（相对路径）
        """
        src = Path(image_path)
        if not src.exists():
            raise FileNotFoundError(f"图片文件不存在：{image_path}")
        
        # 生成唯一文件名
        file_hash = hashlib.md5(src.read_bytes()).hexdigest()[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = src.suffix.lower()
        dest_name = f"原题-{timestamp}-{file_hash}{ext}"
        dest_path = self.media_dir / dest_name
        
        # 复制文件
        import shutil
        shutil.copy2(src, dest_path)
        
        # 返回相对路径
        return f"media/{dest_name}"
    
    def ocr_recognize(self, image_path: str) -> str:
        """
        OCR 识别图片文字
        
        Args:
            image_path: 图片路径
            
        Returns:
            识别的文字内容
        """
        # 方法 1：使用本地 Tesseract
        if OCR_AVAILABLE and not self.config.get('ocr_api_url'):
            try:
                img = Image.open(image_path)
                # 中文 + 英文
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                return text.strip()
            except Exception as e:
                print(f"⚠️  本地 OCR 失败：{e}，尝试 API 模式...")
        
        # 方法 2：使用 API（推荐：百度 OCR、阿里云 OCR 等）
        if self.config.get('ocr_api_url') and self.config.get('ocr_api_key'):
            return self._ocr_via_api(image_path)
        
        # 方法 3：使用视觉大模型直接识别（备用方案）
        return self._ocr_via_vlm(image_path)
    
    def _ocr_via_api(self, image_path: str) -> str:
        """通过 OCR API 识别"""
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        headers = {
            'Authorization': f"Bearer {self.config['ocr_api_key']}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'image': image_data,
            'language': 'ch'
        }
        
        response = requests.post(
            self.config['ocr_api_url'],
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        # 根据不同 API 格式解析
        if 'text' in result:
            return result['text']
        elif 'data' in result and 'text' in result['data']:
            return result['data']['text']
        else:
            return json.dumps(result, ensure_ascii=False)
    
    def _ocr_via_vlm(self, image_path: str) -> str:
        """通过视觉大模型识别图片文字"""
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        prompt = """请仔细识别这张图片中的所有文字内容（包括数学公式），按原格式输出。
如果是数学题目，请完整保留：
1. 题目编号
2. 题干文字
3. 所有选项（如果有）
4. 图形中的标注文字
5. 数学公式（用 LaTeX 格式表示）

请直接输出识别结果，不要添加其他说明。"""
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }
        ]
        
        result = self._call_llm(messages, model='qwen-vl-max')
        return result
    
    def analyze_topic(self, ocr_text: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        使用大模型分析题目
        
        Args:
            ocr_text: OCR 识别的文字
            image_path: 可选的图片路径（用于视觉模型）
            
        Returns:
            分析结果字典
        """
        prompt = f"""你是一位经验丰富的 AMC8 数学竞赛教练。请分析以下题目：

【题目内容】
{ocr_text}

请按照以下 JSON 格式输出分析结果（只输出 JSON，不要其他文字）：

{{
    "topic_text": "完整的题目文字（整理后的）",
    "knowledge_points": ["知识点 1", "知识点 2"],
    "difficulty": "简单/中等/困难",
    "solution_steps": ["步骤 1", "步骤 2", "步骤 3"],
    "answer": "最终答案",
    "solution_thought": "解题思路分析（关键突破点、为什么想到这个方法）",
    "keywords": ["标签 1", "标签 2", "标签 3"],
    "common_mistakes": ["易错点 1", "易错点 2"],
    "lesson_category": "Lesson-XX 或知识点名称"
}}

注意：
1. 数学公式用 LaTeX 格式表示，如 $x^2$, $\\frac{{a}}{{b}}$, $\\sqrt{{n}}$
2. keywords 使用 # 标签格式，如 "#勾股定理", "#数论"
3. lesson_category 用于确定保存的子目录"""

        messages = [
            {"role": "system", "content": "你是一位 AMC8 数学竞赛专家，擅长分析题目并给出清晰的解题步骤。"},
            {"role": "user", "content": prompt}
        ]
        
        result_text = self._call_llm(messages)
        
        # 解析 JSON 结果
        try:
            # 尝试提取 JSON（可能包含在 markdown 代码块中）
            import re
            json_match = re.search(r'```json\s*(.+?)\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            else:
                # 尝试直接解析
                json_match = re.search(r'\{.+?\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
            
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON 解析失败：{e}")
            print(f"原始结果：{result_text}")
            # 返回基础结构
            return {
                "topic_text": ocr_text,
                "knowledge_points": ["待分析"],
                "difficulty": "待评估",
                "solution_steps": ["待解析"],
                "answer": "待计算",
                "solution_thought": "待分析",
                "keywords": ["#待分类"],
                "common_mistakes": ["待补充"],
                "lesson_category": "未分类"
            }
    
    def _call_llm(self, messages: list, model: Optional[str] = None) -> str:
        """
        调用大语言模型
        
        Args:
            messages: 消息列表
            model: 模型名称
            
        Returns:
            模型回复内容
        """
        model = model or self.config.get('llm_model', 'qwen-max')
        api_key = self.config.get('llm_api_key')
        
        if not api_key:
            raise ValueError("未配置 LLM API Key，请设置环境变量 LLm_API_KEY")
        
        # 阿里云 DashScope 格式
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model,
            'input': {
                'messages': messages
            },
            'parameters': {
                'temperature': 0.7,
                'max_tokens': 2000
            }
        }
        
        try:
            response = requests.post(
                self.config['llm_api_url'],
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            if 'output' in result and 'text' in result['output']:
                return result['output']['text']
            elif 'choices' in result:
                return result['choices'][0]['message']['content']
            else:
                return json.dumps(result, ensure_ascii=False)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 调用失败：{e}")
            return ""
    
    def generate_markdown(self, analysis: Dict[str, Any], media_path: str, topic_id: str) -> str:
        """
        生成 Markdown 文档
        
        Args:
            analysis: 分析结果
            media_path: 图片媒体路径
            topic_id: 题目 ID
            
        Returns:
            Markdown 内容
        """
        md_content = f"""# 题目分析 - {topic_id}

---

## 📷 题目原图

![题目照片]({media_path})

---

## 📝 题目原文

> **题目：** {analysis.get('topic_text', '待识别')}

**难度：** {analysis.get('difficulty', '待评估')}

**考查知识点：** {', '.join(analysis.get('knowledge_points', ['待分析']))}

---

## ✏️ 解题步骤

"""
        # 添加解题步骤
        for i, step in enumerate(analysis.get('solution_steps', []), 1):
            md_content += f"**步骤 {i}：** {step}\n\n"
        
        md_content += f"""**答案：** {analysis.get('answer', '待计算')}

---

## 💡 解题思路

{analysis.get('solution_thought', '待分析')}

---

## 🔑 提示词/关键词

"""
        # 添加标签
        for kw in analysis.get('keywords', []):
            md_content += f"- {kw}\n"
        
        md_content += f"""
---

## ⚠️ 易错点提醒

"""
        for mistake in analysis.get('common_mistakes', []):
            md_content += f"- {mistake}\n"
        
        md_content += f"""
---

## 📚 相关题目

- [待补充类似题目]

---

**分析日期：** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**题目 ID：** {topic_id}
"""
        return md_content
    
    def save_analysis(self, md_content: str, category: str, topic_id: str) -> str:
        """
        保存分析文档
        
        Args:
            md_content: Markdown 内容
            category: 分类目录（Lesson-XX 或知识点）
            topic_id: 题目 ID
            
        Returns:
            保存的文件路径
        """
        # 清理分类名称
        category = category.replace('/', '-').replace('\\', '-')
        
        # 创建子目录
        target_dir = self.memory_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        filename = f"题目分析-{topic_id}.md"
        filepath = target_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(filepath)
    
    def process_image(self, image_path: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        完整处理流程：OCR → 分析 → 生成文档
        
        Args:
            image_path: 题目图片路径
            category: 可选的分类（如 "Lesson-12-勾股定理"）
            
        Returns:
            处理结果
        """
        print(f"\n📸 开始处理：{image_path}")
        
        # 1. 保存媒体文件
        print("  ① 保存图片...")
        media_path = self._save_image(image_path)
        
        # 2. OCR 识别
        print("  ② OCR 识别...")
        ocr_text = self.ocr_recognize(image_path)
        print(f"     识别结果：{len(ocr_text)} 字符")
        
        # 3. 大模型分析
        print("  ③ 题目分析...")
        analysis = self.analyze_topic(ocr_text, image_path)
        
        # 使用用户指定的分类或分析结果中的分类
        if category:
            analysis['lesson_category'] = category
        
        # 4. 生成题目 ID
        topic_id = self._generate_topic_id()
        
        # 5. 生成 Markdown
        print("  ④ 生成文档...")
        md_content = self.generate_markdown(analysis, media_path, topic_id)
        
        # 6. 保存文件
        print("  ⑤ 保存文档...")
        filepath = self.save_analysis(md_content, analysis.get('lesson_category', '未分类'), topic_id)
        
        print(f"\n✅ 完成！文档已保存：{filepath}")
        
        return {
            'topic_id': topic_id,
            'media_path': media_path,
            'filepath': filepath,
            'analysis': analysis
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AMC8 题目分析工具')
    parser.add_argument('image', nargs='?', help='题目图片路径')
    parser.add_argument('-c', '--category', help='分类目录（如 Lesson-12-勾股定理）')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--batch', help='批量处理目录')
    
    args = parser.parse_args()
    
    # 加载配置
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # 创建分析器
    analyzer = AMC8Analyzer(config)
    
    # 单张图片处理
    if args.image:
        result = analyzer.process_image(args.image, args.category)
        print(f"\n📊 分析摘要:")
        print(f"   题目 ID: {result['topic_id']}")
        print(f"   知识点：{', '.join(result['analysis'].get('knowledge_points', []))}")
        print(f"   难度：{result['analysis'].get('difficulty', '待评估')}")
        return
    
    # 批量处理
    if args.batch:
        batch_dir = Path(args.batch)
        image_files = list(batch_dir.glob('*.jpg')) + list(batch_dir.glob('*.png'))
        print(f"📁 发现 {len(image_files)} 张图片")
        
        for img in image_files:
            try:
                analyzer.process_image(str(img))
            except Exception as e:
                print(f"❌ 处理失败 {img}: {e}")
        return
    
    # 无参数时显示帮助
    parser.print_help()


if __name__ == '__main__':
    main()
