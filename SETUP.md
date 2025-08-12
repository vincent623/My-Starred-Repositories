# 🚀 快速设置指南

## 📋 前置准备

### 1. 获取 GitHub Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 填写说明（如：My Starred Repos）
4. 选择权限：
   - ✅ `public_repo` （如果只处理公开仓库）
   - ✅ `repo` （如果包含私有仓库）
5. 点击 "Generate token"
6. **立即复制并保存**（token 只显示一次！）

### 2. 获取 LLM API Key

#### 选项 A：OpenRouter（推荐）
1. 注册 OpenRouter 账号：https://openrouter.ai/
2. 获取 API Key（格式：sk-or-xxxxxxxx...）
3. OpenRouter 提供多种模型选择，包括 GPT-4o、Claude 3.5、Gemini 等
4. 相比其他平台，OpenRouter 通常价格更实惠，模型选择更丰富

#### 选项 B：OpenAI
1. 注册 OpenAI 账号：https://platform.openai.com/
2. 获取 API Key

#### 选项 C：阿里云通义千问
1. 注册阿里云账号：https://www.aliyun.com/
2. 开通通义千问服务
3. 获取 AccessKey Secret

## ⚙️ 配置项目

### 方法一：使用 GitHub Secrets（推荐，用于自动化）

1. **Fork 本仓库**到你的 GitHub 账户
2. 在你的 Fork 仓库中：
   - 进入 `Settings` → `Secrets and variables` → `Actions`
   - 点击 `New repository secret`
   - 添加以下 Secrets：

   | Name | Value |
   |------|-------|
   | `GH_TOKEN` | 你的 GitHub Personal Access Token |
   | `LLM_API_KEY` | 你的 LLM API Key |
   | `LLM_API_BASE_URL` | LLM API 地址（可选） |
   | `LLM_MODEL_NAME` | 模型名称（可选） |

### 方法二：本地运行（用于测试）

1. **克隆项目**：
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的配置
   ```

4. **运行程序**：
   ```bash
   python main.py
   ```

## 🎯 运行方式

### 自动运行（GitHub Actions）
- 设置完成后，程序会**每周一上午9点**自动运行
- 也可以手动触发：仓库页面 → `Actions` → `Update Starred Repos` → `Run workflow`

### 本地运行
```bash
# 普通运行
python main.py

# 调试模式（显示详细日志）
python main.py --debug
```

## 📁 生成的文件

运行后，你会看到以下文件：

### 主要文件
- `README.md` - 整理好的 Star 仓库列表
- `weekly_report.md` - 每周洞察报告
- `data/repos.json` - 仓库详细数据
- `data/tags.json` - 标签统计数据

### 日志文件
- `starred_repos.log` - 运行日志
- `debug.log` - 调试日志（仅在调试模式下生成）

## 🔧 自定义配置

编辑 `config.py` 文件可以调整：

```python
# 排除特定语言
EXCLUDE_LANGUAGES = ["HTML", "CSS"]

# 限制处理数量
MAX_REPOS_TO_PROCESS = 500

# 修改 LLM 模型
LLM_MODEL_NAME = "qwen-max"

# 调整分析提示词
REPO_ANALYSIS_PROMPT = """..."""
```

## 🐛 常见问题

### 1. "请设置 GH_TOKEN 环境变量"
- 检查 GitHub Secrets 或 .env 文件中的 `GH_TOKEN` 是否正确设置

### 2. "获取 Star 仓库失败"
- 检查 GitHub Token 是否有足够权限
- 检查网络连接

### 3. "分析仓库失败"
- 检查 LLM API Key 是否正确
- 检查 API 余额是否充足
- 检查 API 地址是否正确

### 4. GitHub Actions 失败
- 检查所有 Secrets 是否正确设置
- 查看 Actions 页面的错误日志
- 检查代码是否有语法错误

## 💡 使用技巧

1. **首次运行**：建议先在本地测试，确认正常后再设置 GitHub Actions
2. **成本控制**：可以通过 `MAX_REPOS_TO_PROCESS` 限制处理的仓库数量
3. **定期检查**：偶尔查看生成的 README.md 和周报，确保分析质量
4. **备份重要**：重要的 Star 建议手动备份，避免依赖自动化

## 🎉 完成！

设置完成后，你就可以享受自动化的 GitHub Star 仓库管理了！系统会：
- ✅ 自动获取所有 Star 仓库
- ✅ 智能分析每个项目
- ✅ 生成分类整理的列表
- ✅ 提供每周洞察报告
- ✅ 完全自动化，无需手动干预

祝你使用愉快！🚀
