**PRD: StarSense - 智能星标仓库管理与洞察系统**

### **1. 项目背景 (Project Background)**

**问题陈述:** GitHub 用户的 Star 列表是一个宝贵的个人技术资产库，但随着数量增长，它会变得混乱无序，难以检索和回顾。手动整理耗时耗力，导致“收藏吃灰”现象普遍存在。

**解决方案:** 本项目旨在创建一个名为 "StarSense" 的自动化系统。该系统通过 GitHub Actions 定期运行，利用大型语言模型 (LLM) 对用户 Star 的仓库进行智能分析、分类和摘要，并将结果持久化到 SQLite 数据库中。最终，系统会生成一份结构化的 Awesome List (`README.md`) 和一份个性化的技术洞察周报，将无序的收藏转变为一个动态、可管理、可洞察的个人知识库。

### **2. 典型用户用例 (Typical User Use Cases)**

这些用例旨在指导数据库和测试用例的生成。

#### **用例 1: 首次初始化 (Initial Setup)**

*   **场景:** 用户首次 Fork 本项目并配置好 Secrets，手动触发 GitHub Actions。
*   **输入:**
    *   用户的 `GH_TOKEN`。
    *   用户的 `LLM_API_KEY`。
    *   一个空的或不存在的 `database.sqlite` 文件。
    *   一个默认的 `tags.yml` 和 `templates/` 目录。
*   **处理流程:**
    1.  脚本检测到 `database.sqlite` 不存在，执行数据库初始化，创建所有表。
    2.  通过 GitHub API，获取用户 Star 的**所有**仓库信息。
    3.  将所有仓库的基本信息存入 `repositories` 表，`starred_at` 字段记录准确。
    4.  加载 `tags.yml` 作为自定义标签字典。
    5.  对**所有**仓库调用 LLM 进行分析（生成摘要、价值和标签）。
    6.  将 LLM 分析结果更新回 `repositories` 表，并将标签关系存入 `repo_tags` 表。
    7.  根据数据库内容，生成完整的 `README.md`。
    8.  由于是首次运行，不生成周报。
    9.  将更新后的 `database.sqlite` 和 `README.md` commit 并 push 回仓库。
*   **预期输出:**
    *   一个 `database.sqlite` 文件，包含所有 Star 仓库及其分析数据。
    *   一个 `README.md` 文件，格式为 Awesome List，按自定义标签分类。

#### **用例 2: 每周增量更新 (Incremental Weekly Update)**

*   **场景:** GitHub Actions 按预定的 cron 表达式（例如，每周日凌晨）自动触发。
*   **输入:**
    *   一个已存在的 `database.sqlite` 文件，包含上周及之前的数据。
    *   用户的 GitHub 账户在本周新增了 5 个 Star，并有 2 个旧的 Star 仓库更新了描述。
*   **处理流程:**
    1.  脚本连接到 `database.sqlite`。
    2.  通过 GitHub API 获取用户所有 Star 仓库，并与数据库中的记录进行比对。
    3.  识别出 5 个新增的仓库，并将其插入 `repositories` 表。
    4.  识别出 2 个信息有变的仓库，并更新其在 `repositories` 表中的记录。
    5.  仅对这 7 个新增或有变动的仓库调用 LLM 进行分析。
    6.  更新这 7 个仓库的 LLM 分析结果和标签。
    7.  根据**当前最新**的数据库内容，**重新生成**完整的 `README.md`。
    8.  查询数据库中 `starred_at` 在过去 7 天内的所有仓库。
    9.  将这些周增量数据和上周的数据（用于对比）作为上下文。
    10. 加载用户配置的报告模板和配套的 Prompt。
    11. 调用 LLM 生成周报的各个部分内容。
    12. 将内容填充到报告模板中，生成 `weekly_report.md`。
    13. 将更新后的 `database.sqlite`, `README.md`, `weekly_report.md` commit 并 push 回仓库。
*   **预期输出:**
    *   `database.sqlite` 文件被更新。
    *   `README.md` 被更新。
    *   一个新的 `weekly_report.md` 文件被创建或覆盖。

#### **用例 3: 用户自定义标签体系 (User Customizes Tags)**

*   **场景:** 用户修改了 `tags.yml` 文件，添加了新的分类和标签，并希望系统重新分类所有项目。
*   **输入:**
    *   一个已存在的 `database.sqlite` 文件。
    *   一个被用户修改过的 `tags.yml` 文件。
    *   用户在 GitHub Actions 界面手动触发工作流，并可能传入一个 `force_reanalyze=true` 的参数。
*   **处理流程:**
    1.  脚本检测到 `force_reanalyze` 标志。
    2.  清空 `repo_tags` 表和 `repositories` 表中的 `llm_summary`, `llm_value` 字段。
    3.  加载**新**的 `tags.yml` 文件。
    4.  对数据库中的**所有**仓库，重新调用 LLM 进行打标和分析。
    5.  将新的分析结果和标签关系更新回数据库。
    6.  重新生成 `README.md`。
*   **预期输出:**
    *   `database.sqlite` 中的标签和分析数据被全面更新。
    *   `README.md` 的分类结构反映了新的 `tags.yml` 体系。

### **3. 技术选型架构 (Technical Architecture & Stack)**

*   **执行环境:** GitHub Actions (Ubuntu latest runner)
*   **核心语言:** Python 3.10+
*   **数据持久化:** SQLite 3
*   **Python 库:**
    *   `sqlite3`: 内置库，用于数据库交互。
    *   `requests` 或 `PyGithub`: 用于与 GitHub API 交互。
    *   `PyYAML`: 用于解析 `tags.yml` 和 `prompts/*.yml` 配置文件。
    *   `Jinja2`: 用于填充报告和 README 模板。
    *   `openai` 或其他 LLM 厂商的 SDK: 用于与 LLM API 交互。
*   **架构:** 一个由 GitHub Actions 调度的、无服务器的 ETL (Extract, Transform, Load) 流水线。
    1.  **Extract:** 从 GitHub API 拉取 Star 数据。
    2.  **Transform:** 使用 LLM 对数据进行分析、摘要和分类。
    3.  **Load:** 将处理后的结构化数据存入 SQLite 数据库。
    4.  **Present:** 从数据库中查询数据，生成 Markdown 文件（README 和报告）。

### **4. 核心流程 (Core Flow)**

主脚本 `main.py` 应遵循以下执行逻辑：

1.  **初始化 (Initialization):**
    *   解析命令行参数（例如 `--force-reanalyze`）。
    *   加载配置文件 (`config.py`) 和 Secrets (从环境变量读取)。
    *   初始化数据库连接，如果数据库文件不存在，则调用 `setup_database()`。

2.  **数据同步 (Data Synchronization):**
    *   调用 GitHub API 获取所有 Starred Repositories。
    *   将获取的数据与数据库中的数据进行比对，将新增或更新的仓库信息写入/更新到 `repositories` 表。

3.  **智能分析 (Intelligent Analysis):**
    *   从数据库中筛选出需要分析的仓库（新仓库或需要强制重新分析的仓库）。
    *   加载 `tags.yml`。
    *   对于每个待分析的仓库，构造 Prompt，调用 LLM 获取摘要、价值和标签。
    *   将分析结果更新回数据库。

4.  **内容生成 (Content Generation):**
    *   **Awesome List:** 从数据库查询所有仓库和标签，按分类组织数据，生成 `README.md`。
    *   **周报:**
        *   判断是否为周报生成日（或通过参数触发）。
        *   从数据库查询本周新增数据和历史对比数据。
        *   加载报告模板和对应的 Prompts。
        *   调用 LLM 生成报告各部分内容。
        *   使用 Jinja2 渲染模板，生成 `weekly_report.md`。

5.  **持久化 (Persistence):**
    *   执行 Git 命令 (`git add`, `git commit`, `git push`)，将 `database.sqlite`, `README.md`, `weekly_report.md` 等变动文件提交回仓库。

### **5. 关键技术实现 (Key Technical Implementation - Code Examples)**

#### **5.1. SQLite 数据库设置**

```python
# file: database.py
import sqlite3

def setup_database(db_path='database.sqlite'):
    """Initializes the database and creates tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Repositories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repositories (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        language TEXT,
        html_url TEXT NOT NULL,
        starred_at DATETIME NOT NULL,
        updated_at DATETIME,
        stars_count INTEGER,
        forks_count INTEGER,
        llm_summary TEXT,
        llm_value TEXT,
        analyzed_at DATETIME
    )
    ''')

    # Tags dictionary table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        category TEXT
    )
    ''')
  
    # Association table for many-to-many relationship
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repo_tags (
        repo_id INTEGER,
        tag_id INTEGER,
        FOREIGN KEY (repo_id) REFERENCES repositories (id),
        FOREIGN KEY (tag_id) REFERENCES tags (id),
        PRIMARY KEY (repo_id, tag_id)
    )
    ''')

    conn.commit()
    conn.close()
```

#### **5.2. 使用自定义标签字典进行 LLM 智能打标**

```python
# file: llm_analyzer.py
import yaml
import json
# Assume 'call_llm_api' is a function that handles the API call

def load_custom_tags(file_path='tags.yml'):
    """Loads custom tags from a YAML file and formats them for the prompt."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tags_data = yaml.safe_load(f)
  
    tag_list = []
    for category, tags in tags_data.items():
        for tag in tags:
            tag_list.append(f"{category}/{tag}")
    return tag_list

def get_llm_tags(repo_info: dict, custom_tags: list) -> list:
    """Gets relevant tags for a repo from a custom list using an LLM."""
    prompt = f"""
    As an expert AI tech analyst, your task is to classify a GitHub repository.
    Based on the repository's information below, select 3 to 5 of the most relevant tags from the provided list.

    **Repository Information:**
    - Name: {repo_info.get('name')}
    - Description: {repo_info.get('description')}
    - Topics: {repo_info.get('topics', [])}

    **Available Tags List:**
    {custom_tags}

    Return your answer as a JSON array of strings, and nothing else.
    Example: ["AI核心技术/Agent", "技术栈/Python", "应用领域/智能办公"]
    """
  
    response_text = call_llm_api(prompt)
  
    try:
        # Validate that the returned tags are in the custom list
        llm_tags = json.loads(response_text)
        valid_tags = [tag for tag in llm_tags if tag in custom_tags]
        return valid_tags
    except (json.JSONDecodeError, TypeError):
        return []
```

#### **5.3. 使用 Jinja2 模板生成报告**

```python
# file: report_generator.py
from jinja2 import Environment, FileSystemLoader

def generate_report(template_name: str, data: dict, output_path: str):
    """Generates a report using a Jinja2 template."""
    env = Environment(loader=FileSystemLoader('templates/'))
    template = env.get_template(f'{template_name}.md')
  
    rendered_content = template.render(data)
  
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rendered_content)

# Example usage in main.py
# weekly_data = {
#     'report_date': '2025-08-18',
#     'weekly_summary': '本周收获满满，主要集中在AI Agent领域...',
#     'highlight_projects': [
#         {'name': 'user/repo1', 'summary': '这是一个...'},
#         {'name': 'user/repo2', 'summary': '这是另一个...'}
#     ],
#     'trend_analysis': '与上周相比，对Rust的关注度显著提升...'
# }
# generate_report('weekly_report_default', weekly_data, 'weekly_report.md')
```

### **6. 预期文件结构 (Expected File Structure)**

```
.
├── .github/
│   └── workflows/
│       └── main.yml         # GitHub Actions workflow
├── data/                    # (Optional, for temporary files)
├── templates/
│   ├── weekly_report_default.md
│   └── weekly_report_professional.md
├── prompts/
│   ├── weekly_report_default.yml
│   └── weekly_report_professional.yml
├── .gitignore
├── README.md                # The generated Awesome List
├── weekly_report.md         # The generated weekly report
├── config.py                # User configuration (LLM model, template choice, etc.)
├── database.sqlite          # The SQLite database file
├── main.py                  # The main script orchestrating the flow
├── requirements.txt         # Python dependencies
└── tags.yml                   # The user's custom tag dictionary
