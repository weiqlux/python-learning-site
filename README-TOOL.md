# AMC8 题目分析自动化工具

📸 **拍照 → OCR 识别 → AI 分析 → 生成结构化文档**

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/AMC8
pip install -r requirements.txt
```

### 2. 配置 API Key

复制配置模板并编辑：

```bash
cp config.example.json config.json
```

编辑 `config.json`，填入你的 API Key：

```json
{
  "llm_api_key": "你的 DashScope API Key",
  "llm_model": "qwen-vl-max"
}
```

**获取 API Key：**
- 阿里云 DashScope: https://dashscope.console.aliyun.com/

### 3. 使用方式

#### 单张图片处理

```bash
python amc8_analyzer.py /path/to/question.jpg
```

#### 指定分类目录

```bash
python amc8_analyzer.py question.jpg -c "Lesson-12-勾股定理"
```

#### 批量处理

```bash
python amc8_analyzer.py --batch /path/to/images/
```

#### 使用配置文件

```bash
python amc8_analyzer.py question.jpg --config config.json
```

---

## 📋 输出结构

处理后的文件保存在 `AMC8/memory/` 目录下：

```
AMC8/memory/
├── Lesson-12-勾股定理/
│   ├── 题目分析 -001.md
│   ├── 题目分析 -002.md
│   └── media/
│       └── 原题 -20260314_092000-abc123.jpg
├── Lesson-03-方程/
│   └── 题目分析 -003.md
└── 错题本/
    └── 题目分析 -004.md
```

---

## 📝 生成的文档结构

每道题目分析包含：

| 模块 | 说明 |
|------|------|
| 📷 题目原图 | 原始照片引用 |
| 📝 题目原文 | OCR 识别 + 整理 |
| ✏️ 解题步骤 | 逐步解析 |
| 💡 解题思路 | 关键突破点分析 |
| 🔑 提示词 | 知识点标签 |
| ⚠️ 易错点 | 常见错误提醒 |

---

## 🔧 高级配置

### 环境变量方式

```bash
export LLM_API_KEY="your-api-key"
export LLM_MODEL="qwen-vl-max"
export OCR_API_URL="https://api.example.com/ocr"
export OCR_API_KEY="your-ocr-key"

python amc8_analyzer.py question.jpg
```

### 自定义输出目录

编辑 `config.json`：

```json
{
  "base_dir": "/your/custom/path/AMC8"
}
```

---

## 📊 示例输出

```markdown
# 题目分析 - 001

## 📷 题目原图
![题目照片](media/原题 -20260314_092000-abc123.jpg)

## 📝 题目原文
> **题目：** 直角三角形的两条直角边分别是 3 和 4，求斜边的长度。

**难度：** 简单

**考查知识点：** 勾股定理

## ✏️ 解题步骤
**步骤 1：** 根据勾股定理，斜边² = 3² + 4²

**步骤 2：** 计算：斜边² = 9 + 16 = 25

**步骤 3：** 斜边 = √25 = 5

**答案：** 5

## 💡 解题思路
这是勾股定理的直接应用题。识别出直角三角形后，直接套用公式 a² + b² = c²...

## 🔑 提示词
- #勾股定理
- #几何
- #直角三角形

## ⚠️ 易错点提醒
- 注意区分直角边和斜边
- 计算平方时不要出错
```

---

## 🛠️ 故障排除

### OCR 识别不准确

1. 确保图片清晰、光线充足
2. 尝试调整图片角度
3. 使用更高分辨率的照片

### API 调用失败

1. 检查 API Key 是否正确
2. 确认网络连接正常
3. 查看 API 额度是否充足

### JSON 解析错误

检查 `config.json` 格式是否正确，确保没有语法错误。

---

## 📚 相关文档

- [题目分析模板](memory/题目分析模板.md)
- [Memory 目录说明](memory/README.md)

---

**版本：** 1.0.0  
**最后更新：** 2026-03-14
