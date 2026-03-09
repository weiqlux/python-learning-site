# 阿里云 DashScope API Key 配置

## 获取 API Key 步骤

### 1. 访问阿里云 DashScope 控制台
打开浏览器访问：https://dashscope.console.aliyun.com/

### 2. 登录/注册阿里云账号
- 如果没有账号，先注册一个（支持手机号注册）
- 登录控制台

### 3. 开通服务
- 首次使用需要开通 DashScope 服务
- 新用户有免费额度（通常足够学习使用）

### 4. 创建 API Key
- 进入"API Key 管理"页面
- 点击"创建新的 API Key"
- 复制生成的 Key（格式类似：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

### 5. 设置环境变量

**临时设置（当前会话有效）：**
```bash
export DASHSCOPE_API_KEY="sk-你的 API Key"
```

**永久设置（推荐）：**

编辑 `~/.bashrc` 或 `~/.bash_profile`：
```bash
echo 'export DASHSCOPE_API_KEY="sk-你的 API Key"' >> ~/.bashrc
source ~/.bashrc
```

或者编辑 `~/.profile`：
```bash
echo 'export DASHSCOPE_API_KEY="sk-你的 API Key"' >> ~/.profile
source ~/.profile
```

### 6. 验证配置
```bash
echo $DASHSCOPE_API_KEY
```
应该显示你的 API Key

### 7. 重启服务
```bash
pkill -f "python app.py"
cd /home/admin/.openclaw/workspace/python-learning-site
python app.py > /tmp/python-learning-site.log 2>&1 &
```

### 8. 测试智能添加
访问：http://172.24.1.146:5000/smart-add
上传一张包含英文的图片测试识别功能

---

## 费用说明

- 新用户注册赠送免费额度
- qwen-vl-max 模型价格：约 0.02 元/千 tokens
- 识别一张图片（含分析）约消耗 1-3 千 tokens
- 建议设置消费限额提醒

## 常见问题

**Q: API Key 不生效？**
A: 确保已执行 `source ~/.bashrc` 或重启终端

**Q: 提示余额不足？**
A: 检查阿里云账户余额，新用户通常有免费额度

**Q: 识别失败？**
A: 检查网络连接，确保能访问阿里云 API
