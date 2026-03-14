# 📸 OCR 拍照建题模块

拍照上传题目 → AI 自动识别分析 → 生成结构化题库

---

## 🚀 功能特性

### 核心功能

- ✅ **拍照建题** - 上传题目照片，AI 自动识别
- ✅ **智能分析** - 自动分析知识点、解题步骤、答案
- ✅ **结构化存储** - 按学科、分类、课程组织题目
- ✅ **标签系统** - 自动提取关键词标签
- ✅ **难度评估** - AI 自动评估题目难度
- ✅ **易错点提醒** - 分析常见错误和注意事项
- ✅ **答题统计** - 记录答题情况，统计正确率

### 支持的题目类型

- 📐 **数学题** - AMC8/AMC10/中考/高考数学
- ⚛️ **物理题** - 力学、电磁学、热学等
- 🧪 **化学题** - 方程式、计算题、实验题
- 📚 **英语题** - 阅读理解、语法题（待优化）

---

## 📋 快速开始

### 1. 配置 API Key

确保已设置阿里云 DashScope API Key：

```bash
export DASHSCOPE_API_KEY="your-api-key"
```

或在 `app.py` 中配置：

```python
os.environ['DASHSCOPE_API_KEY'] = 'your-api-key'
```

### 2. 启动服务

```bash
cd /home/admin/.openclaw/workspace/python-learning-site
python app.py
```

### 3. 访问页面

浏览器打开：http://localhost:5000/ocr-upload

---

## 🎯 使用流程

### 单题上传

1. 打开 **OCR 拍照建题** 页面
2. 点击上传区域或拖拽图片
3. 填写学科、分类、课程等信息
4. 点击 **"🚀 开始分析"**
5. 等待 AI 分析（10-30 秒）
6. 查看分析结果，确认保存

### 批量处理

```python
from ocr_analyzer import OCRQuestionAnalyzer

analyzer = OCRQuestionAnalyzer()

# 批量处理目录中的所有图片
results = analyzer.batch_process(
    '/path/to/questions',
    subject='Math',
    category='AMC8',
    lesson='Lesson-12-勾股定理'
)

print(f"成功：{results['success']}, 失败：{results['failed']}")
```

### 命令行使用

```bash
# 单张图片
python ocr_analyzer.py question.jpg --category "数论" --lesson "Lesson-05-质数"

# 批量处理
python ocr_analyzer.py --batch ./questions/ --category "几何"
```

---

## 📁 目录结构

```
python-learning-site/
├── ocr_question_manager.py    # OCR 题库管理
├── ocr_analyzer.py            # OCR 分析器
├── templates/
│   └── ocr_upload.html        # 上传页面
├── static/
│   └── uploads/
│       └── ocr-questions/     # 题目图片存储
│           └── 2026-03/
│               └── question-xxx.jpg
└── ocr_questions.db           # OCR 题库数据库
```

---

## 🗄️ 数据库结构

### ocr_questions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 题目 ID |
| subject | TEXT | 学科（Math/Physics/Chemistry） |
| category | TEXT | 分类（数论/几何/代数等） |
| lesson | TEXT | 课程/章节 |
| topic_text | TEXT | 题目文字（中文） |
| topic_text_en | TEXT | 题目文字（英文） |
| knowledge_points | TEXT | 知识点（JSON 数组） |
| difficulty | TEXT | 难度（easy/medium/hard） |
| solution_steps | TEXT | 解题步骤（JSON 数组） |
| solution_thought | TEXT | 解题思路 |
| answer | TEXT | 答案 |
| keywords | TEXT | 关键词标签（JSON 数组） |
| common_mistakes | TEXT | 易错点（JSON 数组） |
| image_path | TEXT | 图片路径 |
| created_date | DATE | 创建日期 |

### question_tags 表

题目标签表，支持多标签关联。

### ocr_answers 表

答题记录表，记录用户答题情况。

### ocr_question_stats 表

题目统计表，记录正确率、平均用时等。

---

## 🔌 API 接口

### POST /api/ocr/analyze

分析题目图片

**请求：**
- Content-Type: multipart/form-data
- 参数：
  - `image`: 图片文件
  - `subject`: 学科
  - `category`: 分类
  - `lesson`: 课程
  - `source`: 来源

**响应：**
```json
{
  "success": true,
  "data": {
    "question_id": 1,
    "image_path": "static/uploads/ocr-questions/2026-03/question-xxx.jpg",
    "analysis": {
      "topic_text": "题目内容",
      "knowledge_points": ["知识点 1", "知识点 2"],
      "difficulty": "medium",
      "solution_steps": ["步骤 1", "步骤 2"],
      "answer": "答案",
      "keywords": ["#标签 1", "#标签 2"]
    }
  }
}
```

### GET /api/ocr/stats

获取题库统计信息

**响应：**
```json
{
  "total_questions": 150,
  "today_questions": 5,
  "total_categories": 8,
  "avg_accuracy": 75.5
}
```

### GET /api/ocr/questions

获取题目列表

**参数：**
- `limit`: 数量限制（默认 50）
- `subject`: 学科筛选
- `category`: 分类筛选
- `lesson`: 课程筛选

### GET /api/ocr/search

搜索题目

**参数：**
- `q`: 搜索关键词
- `limit`: 数量限制

### POST /api/ocr/answer

记录答题

**请求：**
```json
{
  "question_id": 1,
  "user_answer": "用户答案",
  "is_correct": true,
  "time_spent": 120,
  "notes": "备注"
}
```

---

## 🎨 页面功能

### OCR 拍照建题页面

访问：`/ocr-upload`

**功能区域：**

1. **统计卡片** - 总题目数、今日添加、分类数量、平均正确率
2. **上传区域** - 点击上传或拖拽图片
3. **表单配置** - 学科、分类、课程、来源
4. **分析结果** - AI 识别的题目、知识点、解题步骤等
5. **题目列表** - 最近添加的题目

---

## 💡 最佳实践

### 图片质量

- ✅ 光线充足，文字清晰
- ✅ 角度端正，避免倾斜
- ✅ 分辨率适中（1000x1000 以上）
- ❌ 避免模糊、过暗、反光

### 分类建议

```
学科：Math / Physics / Chemistry / English

数学分类示例：
- AMC8 - 综合竞赛题
- 数论 - 质数、整除、余数
- 几何 - 三角形、圆、立体几何
- 代数 - 方程、不等式、函数
- 组合 - 排列组合、概率

课程命名：
- Lesson-01-数列与数表
- Lesson-12-勾股定理
- Lesson-05-质数合数
```

### 标签系统

使用 `#` 前缀的标签：
- `#勾股定理` `#质数` `#排列组合`
- `#AMC8` `#数论` `#几何`
- `#易错题` `#经典题` `#难题`

---

## 🛠️ 故障排除

### API 调用失败

**问题：** "缺少 DASHSCOPE_API_KEY"

**解决：**
```bash
export DASHSCOPE_API_KEY="your-api-key"
# 重启 app.py
```

### 图片上传失败

**问题：** "图片大小超过限制"

**解决：** 压缩图片到 10MB 以内，或修改 `app.config['MAX_CONTENT_LENGTH']`

### OCR 识别不准确

**建议：**
1. 确保图片清晰
2. 调整图片角度
3. 检查光线条件
4. 手动修正识别结果

### 数据库错误

**问题：** "no such table"

**解决：**
```python
from ocr_question_manager import init_db
init_db()  # 重新初始化数据库
```

---

## 📊 数据统计

查看题库统计：

```python
from ocr_question_manager import get_statistics

stats = get_statistics()
print(f"总题目数：{stats['total_questions']}")
print(f"按学科：{stats['by_subject']}")
print(f"按难度：{stats['by_difficulty']}")
```

---

## 🔗 相关文档

- [API_KEY_SETUP.md](API_KEY_SETUP.md) - API Key 配置指南
- [smart_add.html](smart_add.html) - 智能添加题目（英语翻译）
- [question_manager.py](question_manager.py) - 英语题库管理

---

**版本：** 1.0.0  
**最后更新：** 2026-03-14
