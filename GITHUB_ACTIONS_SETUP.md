# 🚀 GitHub Actions 自动化设置指南

## 📋 必需的 GitHub Secrets

在您的 GitHub 仓库中设置以下 Secrets：

### 1. 访问仓库设置
1. 进入您的 GitHub 仓库：https://github.com/vincent623/My-Starred-Repositories
2. 点击 `Settings` 标签
3. 在左侧菜单中点击 `Secrets and variables` → `Actions`
4. 点击 `New repository secret`

### 2. 必需的 Secrets

| Secret 名称 | 说明 | 示例值 | 是否必需 |
|------------|------|--------|----------|
| `GH_TOKEN` | GitHub Personal Access Token | `ghp_xxxxxxxxxxxx` | ✅ 必需 |
| `LLM_API_KEY` | LLM API 密钥 | `sk-or-xxxxx` 或 `sk-xxxxx` | ✅ 必需 |
| `LLM_API_BASE_URL` | LLM API 基础URL | `https://openrouter.ai/api/v1` | 🔹 可选 |
| `LLM_MODEL_NAME` | LLM 模型名称 | `openai/gpt-4o-mini` | 🔹 可选 |
| `SILICONFLOW_API_KEY` | Silicon Flow API 密钥 | `sk-xxxxx` | 🔹 可选 |

### 3. 详细配置说明

#### 🔑 GitHub Token (GH_TOKEN)
- 用途：访问您的 GitHub API，获取星标仓库
- 创建方法：
  1. 访问 https://github.com/settings/tokens
  2. 点击 "Generate new token" → "Generate new token (classic)"
  3. 选择权限：`public_repo` 或 `repo`
  4. 复制生成的 token

#### 🤖 LLM API 配置
选择以下任一选项：

**选项A：OpenRouter（推荐）**
- `LLM_API_KEY`: 您的 OpenRouter API Key
- `LLM_API_BASE_URL`: `https://openrouter.ai/api/v1`
- `LLM_MODEL_NAME`: `openai/gpt-4o-mini` 或其他模型

**选项B：Silicon Flow**
- `SILICONFLOW_API_KEY`: 您的 Silicon Flow API Key
- 其他 LLM 配置可留空，系统会自动使用 Silicon Flow

**选项C：OpenAI**
- `LLM_API_KEY`: 您的 OpenAI API Key
- `LLM_API_BASE_URL`: `https://api.openai.com/v1`
- `LLM_MODEL_NAME`: `gpt-4o-mini`

## ⚙️ 自动化工作流特性

### 🕒 自动运行时间表
- **每周运行**: 每周一上午9点（北京时间）
- **手动触发**: 随时可在 Actions 页面手动运行

### 🎛️ 手动运行选项
在 Actions 页面手动触发时，您可以选择：

1. **运行模式**:
   - `auto`: 自动模式（推荐）
   - `daily`: 每日更新模式
   - `weekly`: 周报生成模式

2. **强制重新分析**: 
   - 勾选后会重新分析所有仓库
   - 不勾选则只分析新增仓库

3. **测试模式**:
   - 输入数字（如 10）只分析前N个仓库
   - 用于快速测试

### 📊 自动生成内容
- ✅ 更新 `README.md`（分类整理的仓库列表）
- ✅ 生成 `weekly_report.md`（周报，仅周模式）
- ✅ 上传日志文件到 Artifacts
- ✅ 生成运行摘要报告

## 🔧 启用 GitHub Actions

### 1. 首次启用
1. 确保所有必需的 Secrets 已配置
2. 进入 `Actions` 标签
3. 如果看到 "Workflows aren't being run on this forked repository"，点击 "I understand my workflows, go ahead and enable them"

### 2. 手动测试
1. 进入 `Actions` → `🤖 Update Starred Repositories`
2. 点击 `Run workflow`
3. 选择运行参数（建议首次使用测试模式，如 `sample_size: 5`）
4. 点击 `Run workflow`

### 3. 查看结果
- ✅ **运行状态**: 在 Actions 页面查看运行进度
- ✅ **运行日志**: 点击具体运行查看详细日志
- ✅ **生成结果**: 查看更新的 README.md
- ✅ **下载日志**: 在 Artifacts 中下载日志文件

## 🚨 常见问题排查

### ❌ Token 权限不足
```
Error: Resource not accessible by integration
```
**解决方案**: 检查 `GH_TOKEN` 是否有足够权限

### ❌ LLM API 调用失败
```
Error: Unauthorized
```
**解决方案**: 检查 `LLM_API_KEY` 是否正确和有效

### ❌ 超时错误
```
Error: The operation was canceled.
```
**解决方案**: 仓库太多时使用 `sample_size` 参数限制数量

### 🔍 调试技巧
1. 使用 `sample_size: 5` 进行快速测试
2. 查看 Actions 的详细日志
3. 下载 Artifacts 中的日志文件分析
4. 检查 Secrets 配置是否正确

## 🎯 最佳实践

1. **首次运行**: 使用测试模式验证配置
2. **定期检查**: 偶尔查看 Actions 运行状态
3. **成本控制**: 根据需要调整运行频率
4. **备份重要数据**: 定期备份 README.md

## 📞 技术支持

如果遇到问题，可以：
1. 查看项目的 Issues 页面
2. 参考 `SETUP.md` 文档
3. 检查 Actions 的运行日志
