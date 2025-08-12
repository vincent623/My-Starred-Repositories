# 配置文件 - 存储所有可配置的参数

# LLM 配置 - OpenRouter
LLM_MODEL_NAME = "openai/gpt-oss-20b:free"  # 默认使用的模型
LLM_API_BASE_URL = "https://openrouter.ai/api/v1"
LLM_TEMPERATURE = 0.7  # 创造性程度
OPENROUTER_REFERER = "https://github.com"  # OpenRouter HTTP-Referer
OPENROUTER_TITLE = "My Starred Repositories"  # OpenRouter X-Title

# 重试配置
LLM_MAX_RETRIES = 3  # LLM 调用最大重试次数
LLM_RETRY_DELAY = 2  # 重试延迟（秒）

# GitHub 配置
EXCLUDE_LANGUAGES = []  # 要排除的语言，例如 ["HTML", "CSS"]
MAX_REPOS_TO_PROCESS = 1000  # 最多处理的仓库数量

# 自定义分类与合并规则（仅保留以下 10 个主类）
# 注意：README 将按以下顺序分组展示
ORDERED_CATEGORIES = [
    "AI Agents",
    "LLMs & Inference",
    "RAG & Knowledge",
    "AI Tooling",
    "Multimodal & Digital Humans",
    "Data Processing",
    "Productivity",
    "Web Tools",
    "Specialized Apps",
    "others",
]

TAG_MERGE_RULES = {
    "AI Agents": [
        "Agent", "AI Agent", "Agents", "智能体", "自动化代理", "AutoGPT", "LangGraph", "Agentic",
    ],
    "LLMs & Inference": [
        "LLM", "LLMs", "大模型", "语言模型", "Inference", "推理引擎", "Serving", "部署",
        "vLLM", "TensorRT-LLM", "llama.cpp", "推理服务"
    ],
    "RAG & Knowledge": [
        "RAG", "检索增强", "向量检索", "Vector DB", "知识库", "Embedding", "检索",
        "Milvus", "FAISS", "Chroma", "知识管理"
    ],
    "AI Tooling": [
        "Prompt", "Prompt Engineering", "评测", "评价", "评测框架", "对齐", "标注",
        "微调", "Fine-tuning", "数据集", "Eval", "工具链"
    ],
    "Multimodal & Digital Humans": [
        "多模态", "语音合成", "TTS", "ASR", "图像生成", "视频生成", "音频", "数字人",
        "Vision", "OCR", "手势", "Avatar"
    ],
    "Data Processing": [
        "ETL", "数据处理", "数据清洗", "数据转换", "管道", "Pipeline", "爬虫", "抓取",
        "存储", "Database", "数据分析"
    ],
    "Productivity": [
        "效率", "生产力", "CLI", "命令行", "工作流", "Notes", "日程", "自动化",
        "脚本", "Shell", "DevTools"
    ],
    "Web Tools": [
        "Web", "前端", "后端", "全栈", "JavaScript", "TypeScript", "Node.js", "框架",
        "网站", "浏览器", "插件", "API", "HTTP"
    ],
    "Specialized Apps": [
        "行业应用", "专业应用", "教育", "金融", "医疗", "游戏", "机器人", "物联网",
        "桌面应用", "移动应用", "SaaS"
    ],
    "others": [
        "未分类", "其他", "其它", "杂项", "Misc", "General"
    ],
}

# 标签清理规则：移除特殊字符
TAG_CLEAN_RULES = {
    r'^\[': '',  # 移除开头的 [
    r'\]$': '',  # 移除结尾的 ]
    r'\s+/.*$': '',  # 移除 / 及后面的内容
    r'^[^\w\u4e00-\u9fff]+': '',  # 移除开头的非字母数字中文字符
    r'[^\w\u4e00-\u9fff]+$': '',  # 移除结尾的非字母数字中文字符
}

# 最小标签数量阈值（低于此数量的标签会被合并到"其他"）
MIN_TAG_COUNT = 3

# 处理配置
SAVE_INTERVAL = 10  # 每处理N个仓库保存一次数据

# 基础提示词（保留以备其他用途）
REPO_ANALYSIS_PROMPT = """
请分析以下 GitHub 仓库信息，并用中文回答：

仓库名：{name}
仓库描述：{description}
主要语言：{language}
主题标签：{topics}

请提供：
1. 一句话摘要（20-50字）
2. 分类标签（1-3个）
3. 价值描述（60-120字，说明定位、典型场景与核心优势，避免空话）

格式请严格按照：
摘要：[摘要内容]
标签：[标签1,标签2,标签3]
价值：[价值描述]
"""

REPORT_SUMMARY_PROMPT = """
分析以下本周新增的 GitHub Star 仓库数据，生成一份周报：

{weekly_data}

请包含以下内容：
1. 本周新增 Star 概览
2. 2-3个亮点项目分析
3. 技术趋势分析
4. 个人兴趣洞察

用中文回答，格式清晰，使用 Markdown 语法。
"""

# 文件路径
DATA_DIR = "data"
REPOS_FILE = f"{DATA_DIR}/repos.json"
TAGS_FILE = f"{DATA_DIR}/tags.json"
WEEKLY_REPORT_FILE = "weekly_report.md"

# 周报归档配置
# 保存每周洞察的归档文件到该目录下（按日期或周编号命名）
WEEKLY_REPORT_DIR = "weekly_reports"
# 可选：按日期保存或按 ISO 周保存
# 示例：weekly_report-2025-08-12.md 或 weekly_report-2025-W33.md
WEEKLY_REPORT_FILENAME_TEMPLATE_DATE = "weekly_report-{date}.md"      # {date}=YYYY-MM-DD
WEEKLY_REPORT_FILENAME_TEMPLATE_ISOWEEK = "weekly_report-{year}-W{week:02d}.md"
