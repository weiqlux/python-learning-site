#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python 学习网站 - Flask 应用"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import json
import signal
import sys
import logging
import io
import re
from datetime import datetime
from question_manager import (
    add_question, get_question, get_questions_by_date, search_questions,
    record_answer, get_questions_by_difficulty, get_hard_questions,
    get_all_categories, get_date_range, init_db
)
from smart_add import smart_add_question
from ocr_analyzer import OCRQuestionAnalyzer
from ocr_question_manager import (
    get_questions_by_filter, search_questions, get_all_subjects,
    get_all_categories, get_all_lessons, get_statistics, record_answer,
    get_question as get_ocr_question
)
from document_mindmap import DocumentMindMapGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/python-learning-site.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 初始化数据库
init_db()

# OCR 题库数据库初始化
from ocr_question_manager import init_db as init_ocr_db
init_ocr_db()

# OCR 分析器初始化
ocr_analyzer = OCRQuestionAnalyzer()

# 文档分析与思维导图生成器初始化
api_key = os.environ.get('DASHSCOPE_API_KEY', '')
logger.info(f"DASHSCOPE_API_KEY 环境变量: {'已设置' if api_key else '未设置'}")
doc_mindmap_generator = DocumentMindMapGenerator({'api_key': api_key})

# 英语翻译练习素材
TRANSLATION_EXERCISES = {
    "harry_potter": {
        "title": "🪄 哈利波特系列",
        "description": "J.K.罗琳的经典魔幻小说片段",
        "exercises": [
            {
                "id": "hp_001",
                "title": "开学第一天的惊喜",
                "source": "哈利波特与魔法石",
                "original": "It did not do to dwell on dreams and forget to live.",
                "translation": "沉湎于虚幻的梦想而忘记现实的生活，这是毫无益处的。",
                "structure_analysis": [
                    {"text": "It", "pos": "代词", "role": "形式主语"},
                    {"text": "did not do", "pos": "动词短语", "role": "谓语（否定）"},
                    {"text": "to dwell on dreams", "pos": "不定式短语", "role": "真正主语"},
                    {"text": "and", "pos": "连词", "role": "连接并列成分"},
                    {"text": "forget to live", "pos": "动词短语", "role": "与 dwell 并列"}
                ],
                "key_words": [
                    {"word": "dwell on", "meaning": "沉湎于，老是想着", "example": "Don't dwell on the past."},
                    {"word": "dream", "meaning": "梦想，梦", "example": "I had a strange dream last night."},
                    {"word": "forget", "meaning": "忘记", "example": "Don't forget to call me."},
                    {"word": "live", "meaning": "生活，活着", "example": "Live your life to the fullest."}
                ],
                "tips": "这是一个经典谚语式句子，it 是形式主语，真正的主语是后面的不定式短语。"
            },
            {
                "id": "hp_002",
                "title": "邓布利多的智慧",
                "source": "哈利波特与密室",
                "original": "It is our choices, Harry, that show what we truly are, far more than our abilities.",
                "translation": "哈利，决定我们成为什么样人的，不是我们的能力，而是我们的选择。",
                "structure_analysis": [
                    {"text": "It", "pos": "代词", "role": "形式主语"},
                    {"text": "is", "pos": "系动词", "role": "谓语"},
                    {"text": "our choices", "pos": "名词短语", "role": "表语（被强调）"},
                    {"text": "Harry", "pos": "专有名词", "role": "称呼语"},
                    {"text": "that show...", "pos": "定语从句", "role": "强调句型"},
                    {"text": "what we truly are", "pos": "宾语从句", "role": "show 的宾语"},
                    {"text": "far more than our abilities", "pos": "比较状语", "role": "程度比较"}
                ],
                "key_words": [
                    {"word": "choice", "meaning": "选择", "example": "You have to make a choice."},
                    {"word": "show", "meaning": "展示，表明", "example": "Show me your homework."},
                    {"word": "truly", "meaning": "真正地", "example": "I truly believe in you."},
                    {"word": "ability", "meaning": "能力", "example": "She has the ability to succeed."}
                ],
                "tips": "这是一个强调句型 'It is... that...'，被强调的部分是 'our choices'。"
            },
            {
                "id": "hp_003",
                "title": "黑暗中的光明",
                "source": "哈利波特与凤凰社",
                "original": "Happiness can be found, even in the darkest of times, if one only remembers to turn on the light.",
                "translation": "即使在最黑暗的日子里，也能找到幸福，只要记得点亮光明。",
                "structure_analysis": [
                    {"text": "Happiness", "pos": "名词", "role": "主语"},
                    {"text": "can be found", "pos": "动词短语", "role": "谓语（被动语态）"},
                    {"text": "even in the darkest of times", "pos": "介词短语", "role": "让步状语"},
                    {"text": "if one only remembers", "pos": "条件状语从句", "role": "条件"},
                    {"text": "to turn on the light", "pos": "不定式短语", "role": "remembers 的宾语"}
                ],
                "key_words": [
                    {"word": "happiness", "meaning": "幸福，快乐", "example": "Money can't buy happiness."},
                    {"word": "darkest", "meaning": "最黑暗的", "example": "the darkest hour of the night"},
                    {"word": "remember", "meaning": "记得", "example": "Remember to lock the door."},
                    {"word": "turn on", "meaning": "打开（灯等）", "example": "Turn on the light, please."}
                ],
                "tips": "句子主干是 'Happiness can be found'，后面跟了让步状语和条件状语从句。"
            }
        ]
    },
    "minecraft": {
        "title": "⛏️ Minecraft 小说系列",
        "description": "基于 Minecraft 游戏的冒险小说片段",
        "exercises": [
            {
                "id": "mc_001",
                "title": "第一次挖矿",
                "source": "Minecraft: The Island",
                "original": "The sun was setting, and I knew I needed to find shelter before the monsters came out.",
                "translation": "太阳正在落山，我知道在怪物出现之前我需要找到避难所。",
                "structure_analysis": [
                    {"text": "The sun", "pos": "名词短语", "role": "主语"},
                    {"text": "was setting", "pos": "动词短语", "role": "谓语（过去进行时）"},
                    {"text": "and", "pos": "连词", "role": "连接并列句"},
                    {"text": "I knew", "pos": "主谓结构", "role": "第二分句主句"},
                    {"text": "I needed to find shelter", "pos": "宾语从句", "role": "knew 的宾语"},
                    {"text": "before the monsters came out", "pos": "时间状语从句", "role": "时间状语"}
                ],
                "key_words": [
                    {"word": "set", "meaning": "（太阳）落山", "example": "The sun sets in the west."},
                    {"word": "shelter", "meaning": "避难所，庇护所", "example": "We need to build a shelter."},
                    {"word": "monster", "meaning": "怪物", "example": "Monsters appear at night."},
                    {"word": "come out", "meaning": "出现，出来", "example": "The stars came out."}
                ],
                "tips": "句子由 and 连接两个并列分句，第二个分句包含宾语从句和时间状语从句。"
            },
            {
                "id": "mc_002",
                "title": "建造家园",
                "source": "Minecraft: The Crash",
                "original": "Every block I placed was a step toward making this place feel like home.",
                "translation": "我放置的每一个方块，都是让这个地方像家一样的进步。",
                "structure_analysis": [
                    {"text": "Every block", "pos": "名词短语", "role": "主语"},
                    {"text": "I placed", "pos": "定语从句", "role": "修饰 block（省略 that）"},
                    {"text": "was", "pos": "系动词", "role": "谓语"},
                    {"text": "a step", "pos": "名词短语", "role": "表语"},
                    {"text": "toward making this place feel like home", "pos": "介词短语", "role": "后置定语"}
                ],
                "key_words": [
                    {"word": "block", "meaning": "方块", "example": "Place a block here."},
                    {"word": "place", "meaning": "放置", "example": "Place the torch on the wall."},
                    {"word": "step", "meaning": "步骤，一步", "example": "Take the first step."},
                    {"word": "feel like", "meaning": "感觉像", "example": "It feels like home."}
                ],
                "tips": "定语从句 'I placed' 修饰 'Every block'，省略了关系代词 that/which。"
            },
            {
                "id": "mc_003",
                "title": "矿洞探险",
                "source": "Minecraft: The Lost Journals",
                "original": "Deep underground, the diamonds were waiting, but so were the dangers that lurked in the shadows.",
                "translation": "在深深的地底，钻石正在等待，但潜伏在阴影中的危险也是如此。",
                "structure_analysis": [
                    {"text": "Deep underground", "pos": "副词短语", "role": "地点状语"},
                    {"text": "the diamonds", "pos": "名词短语", "role": "主语"},
                    {"text": "were waiting", "pos": "动词短语", "role": "谓语（过去进行时）"},
                    {"text": "but", "pos": "连词", "role": "表示转折"},
                    {"text": "so were the dangers", "pos": "倒装句", "role": "表示'危险也是如此'"},
                    {"text": "that lurked in the shadows", "pos": "定语从句", "role": "修饰 dangers"}
                ],
                "key_words": [
                    {"word": "underground", "meaning": "地下", "example": "The tunnel goes underground."},
                    {"word": "diamond", "meaning": "钻石", "example": "Diamonds are rare."},
                    {"word": "danger", "meaning": "危险", "example": "Be aware of the danger."},
                    {"word": "lurk", "meaning": "潜伏，埋伏", "example": "Someone is lurking in the dark."}
                ],
                "tips": "'so were the dangers' 是倒装结构，表示'危险也是如此（在等待）'，避免重复。"
            }
        ]
    }
}

# 教程内容
TUTORIALS = {
    "basic": {
        "title": "Python 基础",
        "lessons": [
            {
                "id": "hello",
                "title": "Hello World",
                "content": """
                <h2>第一个 Python 程序</h2>
                <p>学习编程的第一步，让我们打印 "Hello, World!"</p>
                
                <h3>代码示例</h3>
                <pre><code class="language-python">print("Hello, World!")</code></pre>
                
                <h3>运行结果</h3>
                <pre><code>Hello, World!</code></pre>
                
                <h3>练习</h3>
                <p>尝试修改代码，打印你的名字！</p>
                """,
                "exercise": "打印你的名字"
            },
            {
                "id": "variables",
                "title": "变量与数据类型",
                "content": """
                <h2>变量与数据类型</h2>
                <p>变量是存储数据的容器。</p>
                
                <h3>常见数据类型</h3>
                <ul>
                    <li><strong>字符串 (str)</strong>: "Hello"</li>
                    <li><strong>整数 (int)</strong>: 42</li>
                    <li><strong>浮点数 (float)</strong>: 3.14</li>
                    <li><strong>布尔值 (bool)</strong>: True, False</li>
                </ul>
                
                <h3>代码示例</h3>
                <pre><code class="language-python">name = "小明"
age = 18
height = 1.75
is_student = True

print(f"姓名：{name}, 年龄：{age}")</code></pre>
                """,
                "exercise": "创建一个变量存储你的城市名并打印"
            },
            {
                "id": "conditionals",
                "title": "条件判断",
                "content": """
                <h2>条件判断 (if/else)</h2>
                <p>根据条件执行不同的代码。</p>
                
                <h3>代码示例</h3>
                <pre><code class="language-python">age = 18

if age >= 18:
    print("你已成年")
else:
    print("你还未成年")</code></pre>
                
                <h3>比较运算符</h3>
                <ul>
                    <li><code>==</code> 等于</li>
                    <li><code>!=</code> 不等于</li>
                    <li><code>&gt;</code> 大于</li>
                    <li><code>&lt;</code> 小于</li>
                    <li><code>&gt;=</code> 大于等于</li>
                    <li><code>&lt;=</code> 小于等于</li>
                </ul>
                """,
                "exercise": "写一个判断成绩是否及格的程序（60 分及格）"
            },
            {
                "id": "loops",
                "title": "循环 (for/while)",
                "content": """
                <h2>循环</h2>
                <p>重复执行代码块。</p>
                
                <h3>for 循环</h3>
                <pre><code class="language-python">for i in range(5):
    print(f"第 {i} 次循环")</code></pre>
                
                <h3>while 循环</h3>
                <pre><code class="language-python">count = 0
while count < 5:
    print(count)
    count += 1</code></pre>
                """,
                "exercise": "用循环打印 1 到 10 的所有偶数"
            },
            {
                "id": "functions",
                "title": "函数",
                "content": """
                <h2>函数</h2>
                <p>函数是可重复使用的代码块。</p>
                
                <h3>定义函数</h3>
                <pre><code class="language-python">def greet(name):
    return f"你好，{name}！"

print(greet("小明"))
print(greet("小红"))</code></pre>
                
                <h3>带默认参数</h3>
                <pre><code class="language-python">def greet(name="朋友"):
    return f"你好，{name}！"</code></pre>
                """,
                "exercise": "写一个计算两个数之和的函数"
            }
        ]
    },
    "intermediate": {
        "title": "Python 进阶",
        "lessons": [
            {
                "id": "lists",
                "title": "列表与元组",
                "content": """
                <h2>列表 (List)</h2>
                <p>有序的可变集合。</p>
                
                <h3>基本操作</h3>
                <pre><code class="language-python">fruits = ["苹果", "香蕉", "橙子"]
fruits.append("葡萄")  # 添加
fruits.remove("香蕉")  # 删除
print(fruits[0])  # 访问：苹果
print(len(fruits))  # 长度</code></pre>
                
                <h3>列表推导式</h3>
                <pre><code class="language-python">squares = [x**2 for x in range(10)]
print(squares)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]</code></pre>
                """,
                "exercise": "创建一个包含 1-10 的列表，并打印所有偶数"
            },
            {
                "id": "dicts",
                "title": "字典",
                "content": """
                <h2>字典 (Dictionary)</h2>
                <p>键值对的集合。</p>
                
                <h3>基本操作</h3>
                <pre><code class="language-python">person = {
    "name": "小明",
    "age": 18,
    "city": "北京"
}

print(person["name"])  # 访问
person["email"] = "xiaoming@example.com"  # 添加
del person["city"]  # 删除</code></pre>
                
                <h3>遍历字典</h3>
                <pre><code class="language-python">for key, value in person.items():
    print(f"{key}: {value}")</code></pre>
                """,
                "exercise": "创建一个字典存储你的个人信息并打印"
            },
            {
                "id": "modules",
                "title": "模块与包",
                "content": """
                <h2>模块与包</h2>
                <p>导入和使用 Python 模块。</p>
                
                <h3>导入模块</h3>
                <pre><code class="language-python">import math
print(math.sqrt(16))  # 4.0
print(math.pi)  # 3.141592653589793

from datetime import datetime
print(datetime.now())</code></pre>
                
                <h3>常用内置模块</h3>
                <ul>
                    <li><code>math</code> - 数学函数</li>
                    <li><code>random</code> - 随机数</li>
                    <li><code>datetime</code> - 日期时间</li>
                    <li><code>os</code> - 操作系统接口</li>
                    <li><code>json</code> - JSON 处理</li>
                </ul>
                """,
                "exercise": "导入 random 模块，生成一个 1-100 的随机数"
            }
        ]
    }
}


@app.route('/')
def index():
    """首页"""
    return render_template('index.html', tutorials=TUTORIALS)


@app.route('/tutorial/<category>/<lesson_id>')
def tutorial(category, lesson_id):
    """教程页面"""
    if category in TUTORIALS:
        for lesson in TUTORIALS[category]['lessons']:
            if lesson['id'] == lesson_id:
                return render_template('tutorial.html', 
                                     category=category,
                                     lesson=lesson,
                                     tutorials=TUTORIALS)
    return "教程未找到", 404


@app.route('/api/tutorials')
def api_tutorials():
    """API: 获取所有教程"""
    return jsonify(TUTORIALS)


@app.route('/jingangjing')
def jingangjing():
    """金刚经三十二品纲要页面"""
    return render_template('jingangjing.html')


@app.route('/translation')
def translation_index():
    """英语翻译练习首页"""
    return render_template('translation_index.html', exercises=TRANSLATION_EXERCISES)


@app.route('/translation/<category>/<exercise_id>')
def translation_exercise(category, exercise_id):
    """翻译练习详情页面"""
    if category in TRANSLATION_EXERCISES:
        for exercise in TRANSLATION_EXERCISES[category]['exercises']:
            if exercise['id'] == exercise_id:
                return render_template('translation_exercise.html', 
                                     category=category,
                                     category_info=TRANSLATION_EXERCISES[category],
                                     exercise=exercise,
                                     exercises=TRANSLATION_EXERCISES)
    return "练习未找到", 404


@app.route('/api/translations')
def api_translations():
    """API: 获取所有翻译练习"""
    return jsonify(TRANSLATION_EXERCISES)


# ============= 题库系统路由 =============

@app.route('/translation-db')
def translation_db_index():
    """题库首页 - 显示所有题目"""
    date = request.args.get('date')
    category = request.args.get('category')
    keyword = request.args.get('keyword')
    difficulty = request.args.get('difficulty')
    
    if keyword:
        questions = search_questions(keyword, category)
    elif difficulty:
        questions = get_questions_by_difficulty(difficulty)
    elif date:
        questions = get_questions_by_date(date)
    else:
        questions = get_questions_by_date()
    
    categories = get_all_categories()
    date_range = get_date_range()
    
    return render_template('translation_db_index.html', 
                         questions=questions, 
                         categories=categories,
                         date_range=date_range,
                         current_date=date,
                         current_category=category,
                         current_difficulty=difficulty)


@app.route('/translation-db/<int:question_id>')
def translation_db_question(question_id):
    """题库题目详情"""
    question = get_question(question_id)
    if not question:
        return "题目未找到", 404
    
    # 获取统计信息
    conn = __import__('sqlite3').connect('translation_questions.db')
    conn.row_factory = __import__('sqlite3').Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM question_stats WHERE question_id = ?
    ''', (question_id,))
    stats = cursor.fetchone()
    conn.close()
    
    return render_template('translation_db_question.html', 
                         question=question, stats=stats)


@app.route('/api/question/add', methods=['POST'])
def api_add_question():
    """API: 添加新题目"""
    data = request.json
    
    question_id = add_question(
        category=data.get('category', 'custom'),
        title=data.get('title'),
        original=data.get('original'),
        translation=data.get('translation'),
        source=data.get('source', ''),
        structure_analysis=data.get('structure_analysis'),
        key_words=data.get('key_words'),
        tips=data.get('tips', ''),
        image_path=data.get('image_path')
    )
    
    return jsonify({
        'success': True,
        'question_id': question_id,
        'message': '题目添加成功！'
    })


@app.route('/api/question/answer', methods=['POST'])
def api_submit_answer():
    """API: 提交答案"""
    data = request.json
    question_id = data.get('question_id')
    user_answer = data.get('user_answer')
    
    question = get_question(question_id)
    if not question:
        return jsonify({'success': False, 'message': '题目不存在'}), 404
    
    result = record_answer(question_id, user_answer, question['translation'])
    
    return jsonify({
        'success': True,
        **result
    })


@app.route('/api/questions/hard')
def api_hard_questions():
    """API: 获取高难度题目"""
    min_attempts = request.args.get('min_attempts', 3, type=int)
    questions = get_hard_questions(min_attempts)
    return jsonify({
        'count': len(questions),
        'questions': questions
    })


@app.route('/api/questions/stats')
def api_questions_stats():
    """API: 获取题目统计概览"""
    conn = __import__('sqlite3').connect('translation_questions.db')
    conn.row_factory = __import__('sqlite3').Row
    cursor = conn.cursor()
    
    # 总体统计
    cursor.execute('SELECT COUNT(*) as total FROM questions WHERE is_active = 1')
    total = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM question_stats WHERE difficulty_level = "hard"')
    hard = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM question_stats WHERE difficulty_level = "medium"')
    medium = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM question_stats WHERE difficulty_level = "easy"')
    easy = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM user_answers')
    total_answers = cursor.fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'total_questions': total,
        'by_difficulty': {
            'hard': hard,
            'medium': medium,
            'easy': easy
        },
        'total_answers': total_answers
    })


@app.route('/upload-image', methods=['POST'])
def upload_image():
    """上传图片"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': '没有图片文件'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    
    if file:
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'image_path': f"/static/uploads/{filename}",
            'filename': filename
        })


@app.route('/smart-add')
def smart_add_page():
    """智能添加题目页面"""
    return render_template('smart_add.html')


@app.route('/api/smart-add', methods=['POST'])
def api_smart_add():
    """API: 智能添加题目（上传图片自动识别）"""
    logger.info("收到智能添加题目请求")
    
    if 'image' not in request.files:
        logger.warning("请求缺少图片文件")
        return jsonify({'success': False, 'message': '请上传图片'}), 400
    
    file = request.files['image']
    if file.filename == '':
        logger.warning("文件名为空")
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    
    # 保存上传的图片
    filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    logger.info(f"图片已保存: {filepath}")
    
    # 获取分类
    category = request.form.get('category', 'smart')
    logger.info(f"分类: {category}")
    
    # 检查环境变量
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    logger.info(f"API Key 配置状态: {'已配置' if api_key else '未配置'}")
    
    # 智能识别并添加
    try:
        result = smart_add_question(filepath, category=category)
        logger.info(f"识别结果: success={result.get('success')}")
    except Exception as e:
        logger.exception("smart_add_question 执行异常")
        result = {'success': False, 'error': str(e)}
    
    if result['success']:
        return jsonify({
            'success': True,
            'question_id': result['question_id'],
            'message': '识别成功！题目已添加到题库',
            'analysis': result.get('analysis', {}),
            'redirect': f"/translation-db/{result['question_id']}"
        })
    else:
        logger.error(f"识别失败: {result.get('error')}, message: {result.get('message')}")
        # 删除上传的图片（如果识别失败）
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': result.get('error', '识别失败'),
            'message': result.get('message', '请重试或手动添加')
        }), 500


@app.route('/api/check-vlm-config')
def api_check_vlm_config():
    """API: 检查视觉模型配置"""
    import os
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    
    # 检查 dashscope 是否安装
    try:
        import dashscope
        dashscope_installed = True
    except ImportError:
        dashscope_installed = False
    
    return jsonify({
        'api_key_configured': bool(api_key),
        'dashscope_installed': dashscope_installed,
        'ready': bool(api_key)  # 我们使用 HTTP 直接调用，不需要 SDK
    })


@app.route('/config-success')
def config_success_page():
    """配置成功页面"""
    return render_template('config_success.html')


# ==================== OCR 拍照建题模块 ====================

@app.route('/ocr-upload')
def ocr_upload_page():
    """OCR 拍照建题页面"""
    return render_template('ocr_upload.html')


@app.route('/ocr-manage')
def ocr_manage_page():
    """OCR 题库管理页面"""
    return render_template('ocr_manage.html')


@app.route('/amc8-knowledge')
def amc8_knowledge_page():
    """AMC8 知识讲义页面"""
    return render_template('amc8_knowledge.html')


@app.route('/api/ocr/analyze', methods=['POST'])
def api_ocr_analyze():
    """API: OCR 题目分析"""
    try:
        # 检查文件
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': '未找到图片文件'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        # 保存临时文件
        temp_path = f'/tmp/ocr_{datetime.now().timestamp()}.jpg'
        file.save(temp_path)
        
        # 获取表单数据
        subject = request.form.get('subject', 'Math')
        category = request.form.get('category', 'AMC8')
        lesson = request.form.get('lesson', '')
        source = request.form.get('source', '')
        
        # 分析并保存
        result = ocr_analyzer.process_and_save(
            temp_path,
            subject=subject,
            category=category,
            lesson=lesson,
            source=source
        )
        
        # 清理临时文件
        try:
            os.remove(temp_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"OCR 分析失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ocr/options')
def api_ocr_options():
    """API: 获取下拉选项（课程/章节、题目来源）"""
    try:
        # AMC8 课程/章节列表
        lessons = [
            "Lesson-01-数列与数表",
            "Lesson-02-角度",
            "Lesson-03-方程",
            "Lesson-04-整除",
            "Lesson-05-质数合数",
            "Lesson-06-因数倍数",
            "Lesson-07-分数",
            "Lesson-08-百分比",
            "Lesson-09-比例",
            "Lesson-10-三角形面积（一）",
            "Lesson-11-三角形面积（二）",
            "Lesson-12-勾股定理",
            "Lesson-13-多边形周长面积",
            "Lesson-14-排列组合",
            "Lesson-15-概率",
            "Lesson-16-有理数无理数幂",
            "Lesson-17-余数",
            "Lesson-18-圆与扇形",
            "Lesson-19-逻辑推理",
            "Lesson-20-长方体立方体",
            "Lesson-21-不等式",
            "Lesson-22-一次函数",
            "Lesson-23-距离问题基础",
            "Lesson-24-距离问题比例",
            "Lesson-25-圆柱圆锥"
        ]
        
        # AMC8 历届真题年份（2000-2025）+ 讲义
        current_year = datetime.now().year
        years = list(range(2000, current_year + 1))
        years.reverse()  # 最新年份在前
        
        sources = [f"AMC8 {year}年真题" for year in years]
        sources.append("讲义")
        
        return jsonify({
            'lessons': lessons,
            'sources': sources
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ocr/stats')
def api_ocr_stats():
    """API: 获取题库统计"""
    try:
        stats = get_statistics()
        
        # 计算今日添加
        from datetime import date
        today = date.today().isoformat()
        today_questions = len([q for q in stats.get('recent_questions', []) 
                               if q.get('created_date') == today])
        
        return jsonify({
            'total_questions': stats.get('total_questions', 0),
            'today_questions': today_questions,
            'total_categories': len(stats.get('by_category', {})),
            'avg_accuracy': 0  # 待实现
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ocr/questions')
def api_ocr_questions():
    """API: 获取题目列表"""
    try:
        limit = int(request.args.get('limit', 50))
        subject = request.args.get('subject')
        category = request.args.get('category')
        lesson = request.args.get('lesson')
        
        questions = get_questions_by_filter(
            subject=subject,
            category=category,
            lesson=lesson,
            limit=limit
        )
        
        return jsonify(questions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ocr/search')
def api_ocr_search():
    """API: 搜索题目（支持多维度筛选）"""
    try:
        from ocr_question_manager import get_questions_by_filter
        
        query = request.args.get('q', '')
        lesson = request.args.get('lesson', '')
        source = request.args.get('source', '')
        category = request.args.get('category', '')
        difficulty = request.args.get('difficulty', '')
        limit = int(request.args.get('limit', 100))
        
        # 使用筛选函数
        questions = get_questions_by_filter(
            category=category if category else None,
            lesson=lesson if lesson else None,
            difficulty=difficulty if difficulty else None,
            limit=limit
        )
        
        # 如果有搜索关键词或来源，进一步筛选
        if query or source:
            filtered = []
            for q in questions:
                match = True
                if query:
                    # 全文搜索
                    search_text = f"{q.get('topic_text', '')} {q.get('knowledge_points', '')} {q.get('answer', '')}".lower()
                    if query.lower() not in search_text:
                        match = False
                
                if source and match:
                    # 来源搜索（支持模糊匹配）
                    q_source = q.get('source', '').lower()
                    if source.lower() not in q_source:
                        match = False
                
                if match:
                    filtered.append(q)
            
            questions = filtered
        
        return jsonify(questions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ocr/answer', methods=['POST'])
def api_ocr_answer():
    """API: 记录答题"""
    try:
        data = request.json
        question_id = data.get('question_id')
        user_answer = data.get('user_answer', '')
        is_correct = data.get('is_correct', False)
        time_spent = data.get('time_spent')
        notes = data.get('notes', '')
        
        if not question_id:
            return jsonify({'success': False, 'error': '缺少题目 ID'}), 400
        
        answer_id = record_answer(
            question_id=question_id,
            user_answer=user_answer,
            is_correct=is_correct,
            time_spent=time_spent,
            notes=notes
        )
        
        return jsonify({
            'success': True,
            'answer_id': answer_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ocr/question/<int:question_id>', methods=['GET'])
def api_ocr_get_question(question_id):
    """API: 获取单个题目详情"""
    try:
        from ocr_question_manager import get_question
        question = get_question(question_id)
        
        if not question:
            return jsonify({'error': '题目不存在'}), 404
        
        # 解析 JSON 字段
        import json
        question['knowledge_points'] = json.loads(question.get('knowledge_points', '[]') or '[]')
        question['solution_steps'] = json.loads(question.get('solution_steps', '[]') or '[]')
        question['keywords'] = json.loads(question.get('keywords', '[]') or '[]')
        question['common_mistakes'] = json.loads(question.get('common_mistakes', '[]') or '[]')
        question['analysis_json'] = json.loads(question.get('analysis_json', '{}') or '{}')
        
        return jsonify(question)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ocr/question/<int:question_id>', methods=['PUT'])
def api_ocr_update_question(question_id):
    """API: 更新题目"""
    try:
        from ocr_question_manager import get_db
        import json
        
        data = request.json
        
        conn = get_db()
        cursor = conn.cursor()
        
        # 构建更新字段
        update_fields = []
        params = []
        
        allowed_fields = ['topic_text', 'topic_text_en', 'category', 'lesson', 'difficulty',
                         'solution_steps', 'solution_thought', 'answer', 'keywords',
                         'common_mistakes', 'knowledge_points', 'source', 'is_active']
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                # JSON 字段需要序列化
                if field in ['solution_steps', 'keywords', 'common_mistakes', 'knowledge_points']:
                    value = json.dumps(value, ensure_ascii=False)
                update_fields.append(f'{field} = ?')
                params.append(value)
        
        if not update_fields:
            return jsonify({'success': False, 'error': '没有要更新的字段'}), 400
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        params.append(question_id)
        
        cursor.execute(f'''
            UPDATE ocr_questions 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '题目已更新'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ocr/question/<int:question_id>', methods=['DELETE'])
def api_ocr_delete_question(question_id):
    """API: 删除题目（软删除）"""
    try:
        from ocr_question_manager import get_db
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE ocr_questions 
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (question_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '题目已删除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ocr/question', methods=['POST'])
def api_ocr_create_question():
    """API: 创建新题目"""
    try:
        from ocr_question_manager import add_ocr_question
        import json
        
        data = request.json
        
        question_id = add_ocr_question(
            subject=data.get('subject', 'Math'),
            category=data.get('category', 'AMC8'),
            lesson=data.get('lesson', ''),
            topic_text=data.get('topic_text', ''),
            topic_text_en=data.get('topic_text_en', ''),
            knowledge_points=data.get('knowledge_points', []),
            difficulty=data.get('difficulty', 'medium'),
            solution_steps=data.get('solution_steps', []),
            solution_thought=data.get('solution_thought', ''),
            answer=data.get('answer', ''),
            keywords=data.get('keywords', []),
            common_mistakes=data.get('common_mistakes', []),
            source=data.get('source', '')
        )
        
        return jsonify({
            'success': True,
            'question_id': question_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ocr/export-pdf', methods=['POST'])
def api_ocr_export_pdf():
    """API: 导出选中题目为 HTML（前端转换为 PDF）"""
    try:
        data = request.json
        question_ids = data.get('question_ids', [])
        
        if not question_ids:
            return jsonify({'error': '未选择题目'}), 400
        
        # 获取题目详情
        questions = []
        for qid in question_ids:
            q = get_ocr_question(qid)
            if q:
                questions.append(q)
        
        if not questions:
            return jsonify({'error': '未找到题目'}), 404
        
        # 返回题目数据，前端生成 PDF
        return jsonify({
            'success': True,
            'questions': questions,
            'count': len(questions)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== 文档分析 + 思维导图模块 ====================

@app.route('/document-mindmap')
def document_mindmap_page():
    """文档分析与思维导图页面"""
    return render_template('document_mindmap.html')


@app.route('/api/document/analyze', methods=['POST'])
def api_document_analyze():
    """API: 分析文档图片"""
    try:
        # 检查文件
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': '未找到图片文件'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400

        # 保存临时文件
        temp_path = f'/tmp/doc_{datetime.now().timestamp()}.jpg'
        file.save(temp_path)

        # 获取参数
        question = request.form.get('question', '')
        scenario = request.form.get('scenario', 'general')

        # 分析文档
        result = doc_mindmap_generator.analyze_document(
            image_path=temp_path,
            question=question if question else None,
            scenario=scenario
        )

        # 清理临时文件
        try:
            os.remove(temp_path)
        except:
            pass

        return jsonify(result)

    except Exception as e:
        logger.error(f"文档分析失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/document/text-to-mindmap', methods=['POST'])
def api_text_to_mindmap():
    """API: 从纯文本生成思维导图（无需图片）"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        scenario = data.get('scenario', 'general')

        if not text:
            return jsonify({'success': False, 'error': '文本内容不能为空'}), 400

        if len(text) > 10000:
            return jsonify({'success': False, 'error': '文本内容过长，请控制在10000字以内'}), 400

        # 从文本生成思维导图
        result = doc_mindmap_generator.generate_mindmap_from_text(
            text=text,
            scenario=scenario
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"文本生成思维导图失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/document/chat', methods=['POST'])
def api_document_chat():
    """API: 与文档进行多轮对话"""
    try:
        data = request.json
        session_id = data.get('session_id')
        question = data.get('question')
        
        if not session_id:
            return jsonify({'success': False, 'error': '缺少会话ID'}), 400
        
        if not question:
            return jsonify({'success': False, 'error': '请输入问题'}), 400
        
        result = doc_mindmap_generator.chat(session_id, question)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"对话失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/document/sessions')
def api_document_sessions():
    """API: 获取所有会话列表"""
    try:
        sessions = doc_mindmap_generator.get_sessions(limit=20)
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/document/session/<session_id>')
def api_document_session(session_id):
    """API: 获取单个会话详情"""
    try:
        session = doc_mindmap_generator.get_session(session_id)
        if not session:
            return jsonify({'error': '会话不存在'}), 404
        return jsonify(session)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/document/scenarios')
def api_document_scenarios():
    """API: 获取所有分析场景"""
    try:
        scenarios = []
        for key, config in DocumentMindMapGenerator.SCENARIOS.items():
            scenarios.append({
                'id': key,
                'name': config['name'],
                'description': config['description']
            })
        return jsonify(scenarios)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/document/export/xmind', methods=['POST'])
def api_export_xmind():
    """API: 导出思维导图为 .xmind 文件"""
    try:
        data = request.json
        session_id = data.get('session_id')
        mindmap_data = data.get('mindmap_data')
        title = data.get('title', '思维导图')
        
        # 如果提供了 session_id，从数据库获取数据
        if session_id:
            session = doc_mindmap_generator.get_session(session_id)
            if not session:
                return jsonify({'success': False, 'error': '会话不存在'}), 404
            mindmap_data = session.get('mindmap_data', {})
            title = session.get('document_title', title)
        
        if not mindmap_data:
            return jsonify({'success': False, 'error': '没有思维导图数据'}), 400
        
        # 生成安全的文件名
        safe_title = re.sub(r'[^\w\u4e00-\u9fa5\-]', '_', title)[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_{timestamp}.xmind"
        output_path = f"/tmp/{filename}"
        
        # 导出为 xmind 文件
        export_path = doc_mindmap_generator.export_to_xmind(
            mindmap_data=mindmap_data,
            output_path=output_path,
            title=title
        )
        
        # 读取文件并返回
        with open(export_path, 'rb') as f:
            file_data = f.read()
        
        # 清理临时文件
        try:
            os.remove(export_path)
        except:
            pass
        
        return send_file(
            io.BytesIO(file_data),
            mimetype='application/xmind',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"导出 XMind 失败：{e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/document/export/xmind/<session_id>')
def api_export_xmind_by_session(session_id):
    """API: 通过会话ID导出思维导图为 .xmind 文件"""
    try:
        session = doc_mindmap_generator.get_session(session_id)
        if not session:
            return jsonify({'success': False, 'error': '会话不存在'}), 404
        
        mindmap_data = session.get('mindmap_data', {})
        if not mindmap_data:
            return jsonify({'success': False, 'error': '该会话没有思维导图数据'}), 400
        
        title = session.get('document_title', '思维导图')
        
        # 生成安全的文件名
        safe_title = re.sub(r'[^\w\u4e00-\u9fa5\-]', '_', title)[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_{timestamp}.xmind"
        output_path = f"/tmp/{filename}"
        
        # 导出为 xmind 文件
        export_path = doc_mindmap_generator.export_to_xmind(
            mindmap_data=mindmap_data,
            output_path=output_path,
            title=title
        )
        
        # 读取文件并返回
        with open(export_path, 'rb') as f:
            file_data = f.read()
        
        # 清理临时文件
        try:
            os.remove(export_path)
        except:
            pass
        
        return send_file(
            io.BytesIO(file_data),
            mimetype='application/xmind',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"导出 XMind 失败：{e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# 优雅关闭处理
shutdown_requested = False
server = None

def signal_handler(signum, frame):
    """处理 SIGTERM 和 SIGINT 信号，实现优雅关闭"""
    global shutdown_requested, server
    sig_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
    logger.info(f"收到 {sig_name} 信号，开始优雅关闭...")
    shutdown_requested = True
    if server:
        logger.info("正在关闭服务器...")
        server.shutdown()
    logger.info("服务器已关闭，退出程序")
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    from werkzeug.serving import make_server
    logger.info("启动 Python 学习网站服务...")
    logger.info("监听地址：http://0.0.0.0:5000")
    logger.info("按 Ctrl+C 或发送 SIGTERM 信号来停止服务")
    
    # 使用 make_server 以便支持优雅关闭
    server = make_server('0.0.0.0', 5000, app, threaded=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("收到键盘中断，正在关闭...")
    finally:
        server.shutdown()
        logger.info("服务已停止")
