# 🚀 My Starred Repositories V3 - 设置指南

[![Version](https://img.shields.io/badge/Version-V3-blue.svg)](https://github.com/vincent623/My-Starred-Repositories)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🤖 **AI驱动的GitHub星标仓库智能管理系统** - 完整设置指南

## ✨ 项目特色

- 🤖 **AI智能分析**: 使用大语言模型自动分析每个仓库的价值和用途
- 🏷️ **智能分类系统**: 自动归类到10大技术领域，支持自定义标签
- 📊 **数据洞察分析**: 提供详细的统计分析和技术趋势洞察
- ⚡ **全自动化**: GitHub Actions每周自动运行，无需人工干预
- 🔒 **隐私安全**: 本地SQLite数据库，完全开源
- 📈 **增量更新**: 智能识别新增仓库，避免重复分析
- 📝 **智能报告**: 自动生成结构化README和周报

## 🎯 支持的AI模型

| 服务商 | 模型示例 | 优势 | 推荐程度 |
|--------|----------|------|----------|
| **OpenRouter** | `openai/gpt-4o-mini` | 🥇 多模型选择，价格实惠 | ⭐⭐⭐⭐⭐ |
| **Silicon Flow** | `Qwen/Qwen2.5-Coder-32B-Instruct` | 🚀 专为中文优化，速度快 | ⭐⭐⭐⭐ |
| **OpenAI** | `gpt-4o-mini` | 🎯 原生API，稳定可靠 | ⭐⭐⭐ |

## 📋 前置准备

### 1. 获取 GitHub Personal Access Token

#### 🔑 创建步骤
1. 访问：https://github.com/settings/tokens
2. 点击 **"Generate new token"** → **"Generate new token (classic)"**
3. 填写说明：`My Starred Repositories V3`
4. 选择过期时间：建议选择 **90天** 或 **无过期**
5. 选择权限：
   - ✅ `public_repo` （处理公开仓库）
   - ✅ `repo` （如果包含私有仓库）
6. 点击 **"Generate token"**
7. **⚠️ 立即复制并保存**（token 只显示一次！）

### 2. 选择并配置 LLM API

#### 🥇 选项 A：OpenRouter（推荐）
**优势**: 多模型选择，价格实惠，支持最新模型

1. **注册账号**: https://openrouter.ai/
2. **获取API Key**: 
   - 进入 Settings → Keys
   - 创建新的API Key（格式：`sk-or-xxxxxxxx...`）
3. **推荐模型**:
   - `openai/gpt-4o-mini` - 性价比最高
   - `anthropic/claude-3-haiku` - 快速且准确
   - `google/gemini-flash-1.5` - Google最新模型

#### 🚀 选项 B：Silicon Flow（中文优化）
**优势**: 专为中文优化，响应速度快，免费额度大

1. **注册账号**: https://siliconflow.cn/
2. **获取API Key**: 
   - 进入控制台 → API密钥
   - 创建新密钥（格式：`sk-xxxxxxxx...`）
3. **推荐模型**:
   - `Qwen/Qwen2.5-Coder-32B-Instruct` - 专业代码分析
   - `Qwen/Qwen2.5-72B-Instruct` - 高质量中文理解

#### 🎯 选项 C：OpenAI（经典选择）
**优势**: 原生API，稳定可靠，模型质量高

1. **注册账号**: https://platform.openai.com/
2. **获取API Key**: 
   - 进入 API Keys 页面
   - 创建新的Secret Key
3. **推荐模型**:
   - `gpt-4o-mini` - 最新版本，性价比高
   - `gpt-3.5-turbo` - 经济实惠

## ⚙️ 部署方式

### 🌟 方式一：GitHub Actions（推荐）

**适合**: 希望完全自动化的用户

#### 1. Fork 本仓库
1. 访问：https://github.com/vincent623/My-Starred-Repositories
2. 点击右上角 **"Fork"** 按钮
3. 选择你的GitHub账户

#### 2. 配置 GitHub Secrets
1. 进入你Fork的仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **"New repository secret"**
4. 添加以下必需的Secrets：

| Secret名称 | 值 | 说明 |
|-----------|---|------|
| `GH_TOKEN` | 你的GitHub Token | 用于访问GitHub API |
| `LLM_API_KEY` | 你的LLM API Key | 用于AI分析 |

5. 可选的Secrets：

| Secret名称 | 值 | 说明 |
|-----------|---|------|
| `LLM_API_BASE_URL` | API基础URL | 如: `https://openrouter.ai/api/v1` |
| `LLM_MODEL_NAME` | 模型名称 | 如: `openai/gpt-4o-mini` |
| `SILICONFLOW_API_KEY` | Silicon Flow密钥 | 如果使用Silicon Flow |

#### 3. 启用 GitHub Actions
1. 进入 **Actions** 标签页
2. 如果看到提示，点击 **"I understand my workflows, go ahead and enable them"**
3. 首次手动运行测试：
   - 点击 **"🤖 Update Starred Repositories"**
   - 点击 **"Run workflow"**
   - 建议首次使用测试参数：
     - Mode: `auto`
     - Force reanalyze: ☑️
     - Sample size: `10`（测试模式）

### 🖥️ 方式二：本地运行

**适合**: 开发者或希望本地控制的用户

#### 1. 克隆项目
```bash
git clone https://github.com/vincent623/My-Starred-Repositories.git
cd My-Starred-Repositories
```

#### 2. 安装依赖
```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的配置
# GH_TOKEN=your_github_token
# LLM_API_KEY=your_llm_api_key
# LLM_API_BASE_URL=https://openrouter.ai/api/v1
# LLM_MODEL_NAME=openai/gpt-4o-mini
```

#### 4. 运行程序
```bash
# 首次运行（建议测试模式）
python main_v3.py --sample 10 --force-reanalyze

# 正常运行
python main_v3.py

# 查看更多选项
python main_v3.py --help
```

## 🎛️ 高级配置

### 📊 运行模式选择

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `auto` | 自动模式 | 日常使用，智能判断是否生成周报 |
| `daily` | 每日模式 | 仅更新README，不生成周报 |
| `weekly` | 周报模式 | 生成README和周报 |

### 🔧 命令行参数

```bash
# 查看数据库统计
python main_v3.py --stats

# 查看个人标签词典
python main_v3.py --show-dict

# 强制重新分析所有仓库
python main_v3.py --force-reanalyze

# 测试模式（仅分析前N个仓库）
python main_v3.py --sample 20

# 仅重建统计，不分析
python main_v3.py --rebuild-only

# 重置标签词典
python main_v3.py --reset-tags

# 调试模式
python main_v3.py --debug
```

### 🏷️ 自定义标签系统

项目使用10大智能分类：

1. **AI Agents** - 智能代理和自动化助手
2. **LLMs & Inference** - 大语言模型和推理引擎
3. **RAG & Knowledge** - 检索增强生成和知识管理
4. **AI Tooling** - AI工具链和开发框架
5. **Multimodal & Digital Humans** - 多模态和数字人技术
6. **Data Processing** - 数据处理和ETL工具
7. **Productivity** - 效率工具和自动化脚本
8. **Web Tools** - Web开发工具和框架
9. **Specialized Apps** - 专业应用和行业解决方案
10. **others** - 其他未分类项目

## 🚨 常见问题排查

### ❌ GitHub Token 权限错误
```
Error: Resource not accessible by integration
```
**解决方案**:
1. 检查Token是否有 `public_repo` 或 `repo` 权限
2. 确认Token未过期
3. 重新生成Token并更新Secrets

### ❌ LLM API 调用失败
```
Error: Unauthorized / Rate limit exceeded
```
**解决方案**:
1. 检查API Key是否正确
2. 确认账户余额充足
3. 检查API Base URL是否正确
4. 考虑使用不同的LLM服务商

### ❌ GitHub Actions 超时
```
Error: The operation was canceled
```
**解决方案**:
1. 使用 `sample` 参数限制分析数量
2. 分批次运行
3. 检查网络连接

### 🔍 调试技巧

1. **使用测试模式**: `--sample 5` 快速验证配置
2. **查看详细日志**: `--debug` 启用调试模式
3. **检查数据库状态**: `--stats` 查看统计信息
4. **逐步排查**: 先本地运行，再配置Actions

## 📈 性能优化建议

### 💰 成本控制
- **选择合适的模型**: `gpt-4o-mini` 性价比最高
- **使用免费服务**: Silicon Flow有较大免费额度
- **限制分析数量**: 使用 `sample` 参数控制成本

### ⚡ 提升效率
- **增量更新**: 默认只分析新增仓库
- **定期运行**: 建议每周运行一次
- **并行处理**: 系统自动处理多个仓库

### 🔒 安全建议
- **定期更新Token**: 建议90天更换一次
- **最小权限原则**: 仅给予必要的仓库权限
- **监控使用量**: 定期检查API调用量

## 🎯 最佳实践

### 🔄 定期维护
1. **每月检查**: Actions运行状态和错误日志
2. **季度更新**: 依赖包和模型版本
3. **年度优化**: 标签分类和分析逻辑

### 📊 数据管理
1. **备份重要数据**: 定期下载Artifacts中的数据库文件
2. **监控分析质量**: 抽查生成的摘要和分类
3. **调整配置**: 根据使用情况优化参数

### 🌟 扩展使用
1. **团队协作**: Fork后可用于团队技术栈管理
2. **知识库建设**: 结合周报用于技术趋势跟踪
3. **学习计划**: 根据分类制定系统学习路径

## 📞 获取帮助

### 📚 文档资源
- 📖 [README.md](./README.md) - 项目概览
- ⚙️ [GitHub Actions配置](./GITHUB_ACTIONS_SETUP.md) - 自动化详细指南
- 📋 [产品需求文档](./prd.md) - 技术架构说明

### 🐛 问题反馈
- 🔗 [GitHub Issues](https://github.com/vincent623/My-Starred-Repositories/issues) - 提交Bug和功能请求
- 📧 Email - 技术支持和合作洽谈

### 🤝 贡献代码
欢迎提交PR改进项目！请确保：
1. 代码符合项目规范
2. 添加适当的测试
3. 更新相关文档

---

🎉 **设置完成后，您将拥有一个全自动的AI驱动GitHub星标管理系统！**

*📅 文档更新时间: 2025-08-13 | 📖 版本: V3.0*