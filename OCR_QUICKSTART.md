# 🚀 OCR 拍照建题 - 快速入门

## 1️⃣ 配置 API Key

```bash
# 设置环境变量（临时）
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"

# 或永久添加到 ~/.bashrc
echo 'export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"' >> ~/.bashrc
source ~/.bashrc
```

**获取 API Key：** https://dashscope.console.aliyun.com/

---

## 2️⃣ 启动服务

```bash
cd /home/admin/.openclaw/workspace/python-learning-site
python app.py
```

服务启动后，访问：
- **主页：** http://localhost:5000/
- **OCR 上传：** http://localhost:5000/ocr-upload

---

## 3️⃣ 上传题目

### 方法 A：Web 界面（推荐）

1. 打开 http://localhost:5000/ocr-upload
2. 拖拽题目照片到上传区域
3. 填写分类信息（学科、分类、课程）
4. 点击 "🚀 开始分析"
5. 等待 AI 分析（10-30 秒）
6. 查看结果，确认保存

### 方法 B：命令行

```bash
# 单张图片
python ocr_analyzer.py /path/to/question.jpg \
  --category "数论" \
  --lesson "Lesson-05-质数合数"

# 批量处理
python ocr_analyzer.py --batch ./photos/ \
  --category "几何" \
  --lesson "Lesson-12-勾股定理"
```

### 方法 C：Python 代码

```python
from ocr_analyzer import OCRQuestionAnalyzer

analyzer = OCRQuestionAnalyzer()

# 单张处理
result = analyzer.process_and_save(
    'question.jpg',
    subject='Math',
    category='AMC8',
    lesson='Lesson-12-勾股定理'
)
print(f"题目 ID: {result['question_id']}")

# 批量处理
stats = analyzer.batch_process('./photos/', category='数论')
print(f"成功：{stats['success']}, 失败：{stats['failed']}")
```

---

## 4️⃣ 查看题目

### Web 界面

访问 `/ocr-upload` 页面，底部显示最近添加的题目。

### API 查询

```bash
# 获取所有题目
curl http://localhost:5000/api/ocr/questions

# 按分类筛选
curl "http://localhost:5000/api/ocr/questions?category=数论"

# 搜索题目
curl "http://localhost:5000/api/ocr/search?q=勾股定理"

# 查看统计
curl http://localhost:5000/api/ocr/stats
```

### Python 查询

```python
from ocr_question_manager import (
    get_questions_by_filter, 
    search_questions, 
    get_statistics
)

# 筛选题目
questions = get_questions_by_filter(
    category='数论',
    lesson='Lesson-05',
    limit=10
)

# 搜索题目
results = search_questions('勾股定理')

# 查看统计
stats = get_statistics()
print(f"总题目数：{stats['total_questions']}")
```

---

## 5️⃣ 答题统计

记录答题情况：

```python
from ocr_question_manager import record_answer

# 记录答题
record_answer(
    question_id=1,
    user_answer="5",
    is_correct=True,
    time_spent=120,  # 秒
    notes="第一次做对"
)
```

---

## 📁 文件存储

### 图片存储位置

```
static/uploads/ocr-questions/
└── 2026-03/
    ├── question-20260314_092000-abc123.jpg
    └── question-20260314_093000-def456.jpg
```

### 数据库文件

```
ocr_questions.db  # OCR 题库数据库
```

---

## 🎯 分类建议

### 学科

- `Math` - 数学
- `Physics` - 物理
- `Chemistry` - 化学
- `English` - 英语

### 数学分类示例

```
AMC8 - 综合竞赛题
数论 - 质数、整除、余数、因数倍数
几何 - 三角形、圆、多边形、立体几何
代数 - 方程、不等式、函数、数列
组合 - 排列组合、概率、逻辑推理
应用题 - 分数、百分比、比例、距离问题
```

### 课程命名规范

```
Lesson-01-数列与数表
Lesson-05-质数合数
Lesson-12-勾股定理
Lesson-15-概率
```

---

## ⚡ 快捷键

Web 页面支持：

- **Ctrl+V** - 粘贴剪贴板中的图片
- **拖拽** - 直接拖拽图片到上传区域

---

## 🛠️ 常见问题

### Q: API 调用失败？

**A:** 检查 API Key 是否正确配置：

```bash
echo $DASHSCOPE_API_KEY
# 应该显示你的 API Key
```

### Q: 图片上传失败？

**A:** 检查图片大小（最大 10MB）和格式（JPG/PNG）。

### Q: OCR 识别不准确？

**A:** 
- 确保图片清晰、光线充足
- 避免倾斜和反光
- 分辨率建议 1000x1000 以上

### Q: 如何导出题目？

**A:** 使用 API 或直接查询数据库：

```python
from ocr_question_manager import get_questions_by_filter
import json

questions = get_questions_by_filter(limit=100)
with open('export.json', 'w') as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)
```

---

## 📊 示例输出

AI 分析结果示例：

```json
{
  "topic_text": "直角三角形的两条直角边分别是 3 和 4，求斜边的长度。",
  "knowledge_points": ["勾股定理", "直角三角形"],
  "difficulty": "easy",
  "solution_steps": [
    "根据勾股定理：斜边² = 3² + 4²",
    "计算：斜边² = 9 + 16 = 25",
    "斜边 = √25 = 5"
  ],
  "answer": "5",
  "keywords": ["#勾股定理", "#几何", "#直角三角形"],
  "common_mistakes": [
    "注意区分直角边和斜边",
    "计算平方时不要出错"
  ]
}
```

---

## 🔗 更多文档

- [OCR_MODULE_README.md](OCR_MODULE_README.md) - 完整功能文档
- [API_KEY_SETUP.md](API_KEY_SETUP.md) - API Key 配置指南

---

**开始拍照建题吧！** 📸✨
