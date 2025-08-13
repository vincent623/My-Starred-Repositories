#!/usr/bin/env python3
"""
My Starred Repositories 主程序 V3 - 优化版本
改进标签逻辑和数据流，直接写入数据库
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
import requests
from openai import OpenAI
from tqdm import tqdm
import click
from dotenv import load_dotenv
from loguru import logger
import dateutil.parser
import re

# 导入配置和数据库
from config import *
from database_v3 import get_database_v3

# 加载环境变量
load_dotenv()

# 设置日志
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), level="INFO")
logger.add("starred_repos.log", rotation="1 week")

class StarredReposManagerV3:
    """GitHub Star 仓库管理器 V3 - 优化版本"""
    
    def __init__(self):
        """初始化管理器"""
        self.github_token = os.getenv("GH_TOKEN")
        self.llm_api_key = os.getenv("LLM_API_KEY")
        self.llm_api_base = os.getenv("LLM_API_BASE_URL", LLM_API_BASE_URL)
        self.llm_model = os.getenv("LLM_MODEL_NAME", LLM_MODEL_NAME)

        # 优先使用 Silicon Flow（如果提供了 SILICONFLOW_API_KEY 且未显式设置 LLM_API_KEY）
        if not self.llm_api_key and os.getenv("SILICONFLOW_API_KEY"):
            self.llm_api_key = os.getenv("SILICONFLOW_API_KEY")
            # 默认 Silicon Flow 端点与模型
            if not os.getenv("LLM_API_BASE_URL"):
                self.llm_api_base = "https://api.siliconflow.cn/v1"
            if not os.getenv("LLM_MODEL_NAME"):
                self.llm_model = "Qwen/Qwen2.5-Coder-32B-Instruct"
        
        # 验证必要的配置
        if not self.github_token:
            raise ValueError("请设置 GH_TOKEN 环境变量")
        if not self.llm_api_key:
            raise ValueError("请设置 LLM_API_KEY 环境变量")
        
        # 初始化客户端
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.github_token}',
            # 需要 starred_at 字段必须使用 star+json 媒体类型
            'Accept': 'application/vnd.github.v3.star+json',
            'User-Agent': 'My-Starred-Repos'
        })
        
        # SSL 校验：默认开启；如需在受限网络下跳过校验，可通过环境变量控制
        import urllib3
        disable_verify = os.getenv("DISABLE_SSL_VERIFY", "0") == "1"
        if disable_verify:
            self.session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 设置更长的超时时间和重试机制
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        # 创建适配器并挂载重试策略
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # 设置超时时间
        self.session.timeout = 30
        
        self.llm_client = OpenAI(
            api_key=self.llm_api_key,
            base_url=self.llm_api_base,
            default_headers={
                "HTTP-Referer": OPENROUTER_REFERER,
                "X-Title": OPENROUTER_TITLE
            }
        )
        
        # 初始化数据库 V3
        self.db = get_database_v3()
        
        # 初始化个人标签词典
        self._initialize_personal_tag_dictionary()
        
        logger.info("StarredReposManagerV3 初始化完成")
    
    def _initialize_personal_tag_dictionary(self):
        """初始化个人标签词典"""
        logger.info("初始化个人标签词典...")
        
        # 从配置中加载标签词典
        dictionary = self.db.get_personal_tag_dictionary()
        
        # 如果词典为空，则从 TAG_MERGE_RULES 初始化
        if not dictionary:
            logger.info("个人标签词典为空，从配置初始化...")
            
            # 使用有序主类初始化个人标签词典
            for main_tag in ORDERED_CATEGORIES:
                self.db.add_personal_tag_to_dictionary(tag=main_tag, description=f"个人标签：{main_tag}", category="主类")
            
            logger.info(f"已初始化 {len(TAG_MERGE_RULES)} 个个人标签")
        
        # 显示当前词典
        current_dict = self.db.get_personal_tag_dictionary()
        logger.info(f"当前个人标签词典包含 {len(current_dict)} 个标签")
    
    def get_starred_repositories(self) -> List[Dict]:
        """获取所有 Star 的仓库并直接写入数据库"""
        logger.info("开始获取 Star 仓库列表并直接写入数据库...")
        
        page = 1
        per_page = 100
        total_processed = 0
        
        try:
            # 首先验证连接
            logger.info("验证 GitHub 连接...")
            user_response = self.session.get('https://api.github.com/user')
            if user_response.status_code != 200:
                logger.error(f"无法获取用户信息，状态码: {user_response.status_code}")
                logger.error(f"响应内容: {user_response.text}")
                return []
            
            user_data = user_response.json()
            logger.info(f"成功连接到 GitHub，用户: {user_data['login']}")
            
            # 获取所有 star 的仓库
            logger.info("开始获取 Star 仓库...")
            
            while True:
                url = f'https://api.github.com/user/starred?page={page}&per_page={per_page}'
                response = self.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.error(f"获取 Star 仓库失败，状态码: {response.status_code}")
                    logger.error(f"响应内容: {response.text}")
                    break
                
                repos = response.json()
                if not repos:  # 没有更多数据了
                    break
                
                for repo in repos:
                    try:
                        # 兼容 Accept: application/vnd.github.v3.star+json 的结构（带 repo 嵌套）
                        repo_obj = repo.get('repo', repo)
                        repo_info = {
                            'id': str(repo_obj['id']),
                            'name': repo_obj['full_name'],
                            'description': repo_obj.get('description', '') or '',
                            'language': repo_obj.get('language', 'Unknown') or 'Unknown',
                            'topics': repo_obj.get('topics', []) or [],
                            'starred_at': repo.get('starred_at', repo_obj.get('starred_at', '')),
                            'html_url': repo_obj['html_url'],
                            'updated_at': repo_obj.get('updated_at', '')
                        }
                        
                        # 过滤排除的语言
                        if repo_info['language'] in EXCLUDE_LANGUAGES:
                            continue
                        
                        # 直接写入数据库
                        if self.db.insert_repository_direct(repo_info):
                            total_processed += 1
                            
                            # 更新 GitHub topics 统计
                            if repo_info['topics']:
                                self.db.update_github_topics_stats(repo_info['topics'])
                        
                        if total_processed >= MAX_REPOS_TO_PROCESS:
                            logger.info(f"已达到最大处理数量 {MAX_REPOS_TO_PROCESS}")
                            return []
                            
                    except Exception as repo_error:
                        logger.warning(f"处理仓库时出错: {repo_error}")
                        continue
                
                # 每处理完一页输出一次进度
                logger.info(f"已处理第 {page} 页，共 {total_processed} 个仓库...")
                page += 1
                
                # 检查 API 限制
                remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                if remaining <= 1:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    wait_time = max(reset_time - int(datetime.now().timestamp()), 0)
                    logger.warning(f"API 限制已达到，等待 {wait_time} 秒后继续...")
                    import time
                    time.sleep(wait_time + 1)
            
            logger.info(f"成功获取并写入 {total_processed} 个 Star 仓库")
            return []
            
        except Exception as e:
            logger.error(f"获取 Star 仓库失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"详细错误信息:\n{traceback.format_exc()}")
            return []
    
    def get_enhanced_analysis_prompt(self, repo_info: Dict) -> str:
        """获取增强的分析提示词"""
        # 获取个人标签词典
        personal_tags = self.db.get_personal_tag_dictionary()
        # 固定为配置的 10 大主类；若库中不存在则兜底从配置读取
        tag_options = [item['tag'] for item in personal_tags] or ORDERED_CATEGORIES
        
        # 获取 GitHub topics，兼容不同的字段名
        github_topics = repo_info.get('github_topics', repo_info.get('topics', []))
        if isinstance(github_topics, str):
            github_topics = json.loads(github_topics)
        
        prompt = f"""
你是资深 AI 产品/研发顾问。请基于以下信息，用中文给出高质量分析：

仓库名：{repo_info['name']}
仓库描述：{repo_info['description']}
主要语言：{repo_info['language']}
GitHub 主题标签：{', '.join(github_topics)}

从下列主类中选择 1-3 个进行归类（只能选这些，不要造新词）：
{', '.join(tag_options)}

请输出：
1) 摘要（30-80字）：说明做什么、如何做、核心亮点。
2) 标签（1-3个）：严格从给定主类中选择。
3) 价值（80-160字）：
   - 典型应用场景（谁在何种场景使用）
   - 关键能力/技术路线（例如 RAG/Agent/Serving/评测等）
   - 适合人群或与同类差异点

格式严格如下（不要添加多余说明）：
摘要：[...]
标签：[标签1,标签2,标签3]
价值：[...]
"""
        return prompt
    
    def analyze_repository(self, repo_info: Dict) -> Dict:
        """使用 LLM 分析单个仓库，带重试机制"""
        import time
        
        # 获取增强的分析提示词
        prompt = self.get_enhanced_analysis_prompt(repo_info)
        
        # 获取个人标签词典用于验证
        personal_tags = self.db.get_personal_tag_dictionary()
        valid_tags = [item['tag'] for item in personal_tags]
        
        # 重试机制
        for attempt in range(LLM_MAX_RETRIES):
            try:
                # 调用 LLM
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=LLM_TEMPERATURE,
                    max_tokens=500
                )
                
                analysis_text = response.choices[0].message.content
                
                # 更强大的解析逻辑
                result = {
                    'summary': '',
                    'tags': [],
                    'value': '',
                    'analyzed_at': datetime.now().isoformat()
                }
                
                # 多种解析模式
                lines = analysis_text.split('\n')
                
                # 模式1：标准格式解析
                for line in lines:
                    line = line.strip()
                    if line.startswith('摘要：'):
                        result['summary'] = line[3:].strip()
                    elif line.startswith('标签：'):
                        tags_text = line[3:].strip()
                        # 清理和验证标签
                        parsed_tags = []
                        for tag in tags_text.split(','):
                            tag = tag.strip()
                            if tag and tag in valid_tags:
                                parsed_tags.append(tag)
                        result['tags'] = parsed_tags if parsed_tags else ['others']
                    elif line.startswith('价值：'):
                        result['value'] = line[3:].strip()
                
                # 模式2：如果标准解析失败，尝试灵活解析
                if not result['summary'] or not result['tags']:
                    # 使用正则表达式提取
                    import re
                    
                    # 提取摘要
                    summary_match = re.search(r'摘要[：:]\s*(.*?)(?=标签[：:]|$)', analysis_text)
                    if summary_match:
                        result['summary'] = summary_match.group(1).strip()
                    
                    # 提取标签
                    tags_match = re.search(r'标签[：:]\s*(.*?)(?=价值[：:]|$)', analysis_text)
                    if tags_match:
                        tags_text = tags_match.group(1).strip()
                        parsed_tags = []
                        for tag in tags_text.split(','):
                            tag = tag.strip()
                            if tag and tag in valid_tags:
                                parsed_tags.append(tag)
                        result['tags'] = parsed_tags if parsed_tags else ['others']
                    
                    # 提取价值
                    value_match = re.search(r'价值[：:]\s*(.*?)(?=$)', analysis_text)
                    if value_match:
                        result['value'] = value_match.group(1).strip()
                
                # 模式3：如果仍然失败，生成默认结果
                if not result['summary']:
                    result['summary'] = repo_info['description'][:50] if repo_info['description'] else '暂无描述'
                
                if not result['tags']:
                    result['tags'] = ['others']
                
                if not result['value']:
                    result['value'] = f'一个{repo_info["language"]}项目'
                
                # 验证结果基本完整性
                if result['summary'] and result['tags']:
                    return result
                else:
                    raise ValueError("解析结果仍然不完整")
                
            except Exception as e:
                logger.warning(f"分析仓库 {repo_info['name']} 第 {attempt + 1} 次尝试失败: {e}")
                if attempt < LLM_MAX_RETRIES - 1:
                    logger.info(f"等待 {LLM_RETRY_DELAY} 秒后重试...")
                    time.sleep(LLM_RETRY_DELAY)
                else:
                    logger.error(f"分析仓库 {repo_info['name']} 最终失败: {e}")
                    return {
                        'summary': repo_info['description'][:50] if repo_info['description'] else '分析失败',
                        'tags': ['others'],
                        'value': '无法分析此仓库',
                        'analyzed_at': datetime.now().isoformat()
                    }
    
    def process_repositories(self, force_reanalyze: bool = False, limit: Optional[int] = None) -> List[Dict]:
        """处理所有仓库，直接使用数据库"""
        logger.info("开始处理仓库...")
        
        # 获取需要分析的仓库；若强制则取全部，且可限量
        if force_reanalyze:
            repos_needing_analysis = self.db.get_repositories_needing_analysis(days_threshold=36500)
        else:
            repos_needing_analysis = self.db.get_repositories_needing_analysis()
        if limit is not None:
            repos_needing_analysis = repos_needing_analysis[:max(0, int(limit))]
        
        if not repos_needing_analysis:
            logger.info("没有需要分析的仓库")
            return []
        
        logger.info(f"找到 {len(repos_needing_analysis)} 个需要分析的仓库")
        
        processed_count = 0
        new_repos_this_week = []
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        for i, repo in enumerate(tqdm(repos_needing_analysis, desc="分析仓库")):
            # 分析仓库
            analysis = self.analyze_repository(repo)
            
            # 更新数据库中的分析结果
            if self.db.update_repository_analysis(repo['id'], analysis):
                processed_count += 1
                
                # 更新个人标签统计
                for tag in analysis['tags']:
                    self.db.update_personal_tag_stats(tag)
                
                # 检查是否是本周新增
                if repo['starred_at']:
                    starred_time = dateutil.parser.parse(repo['starred_at'])
                    # 统一为带时区的 UTC 时间
                    if starred_time.tzinfo is None:
                        starred_time = starred_time.replace(tzinfo=timezone.utc)
                    starred_time_utc = starred_time.astimezone(timezone.utc)
                    if starred_time_utc > one_week_ago:
                        new_repos_this_week.append({**repo, **analysis})
            
            # 增量保存：每处理 SAVE_INTERVAL 个仓库更新一次统计
            if (i + 1) % SAVE_INTERVAL == 0:
                logger.info(f"已分析 {i + 1} 个仓库，更新中间数据...")
                self.db.rebuild_personal_tag_stats()
        
        logger.info(f"处理完成，共分析 {processed_count} 个仓库")
        return new_repos_this_week
    
    def clean_tag(self, tag: str) -> str:
        """清理标签，移除特殊字符"""
        cleaned = tag.strip()
        
        # 应用清理规则
        for pattern, replacement in TAG_CLEAN_RULES.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned.strip()
    
    def merge_tags(self, tags: List[str]) -> List[str]:
        """合并相似的标签，包含清理功能"""
        merged_tags = []
        
        for tag in tags:
            # 首先清理标签
            cleaned_tag = self.clean_tag(tag)
            
            if not cleaned_tag:  # 如果清理后为空，跳过
                continue
            
            merged = False
            for main_tag, similar_tags in TAG_MERGE_RULES.items():
                if cleaned_tag in similar_tags:
                    if main_tag not in merged_tags:
                        merged_tags.append(main_tag)
                    merged = True
                    break
            
            if not merged:
                merged_tags.append(cleaned_tag)
        
        return merged_tags
    
    def update_tags_data(self) -> None:
        """更新标签数据（现在主要处理个人标签）"""
        logger.info("更新个人标签数据...")
        
        # 重新构建个人标签统计
        self.db.rebuild_personal_tag_stats()
        
        logger.info("个人标签数据更新完成")
    
    def generate_readme(self) -> None:
        """生成优化的 README.md 文件"""
        logger.info("生成 README.md...")
        
        # 获取个人标签统计
        tag_stats = self.db.get_all_personal_tag_stats()
        # 在生成前，先规范化一次标签，确保只保留 10 类
        self.db.normalize_personal_tags(ORDERED_CATEGORIES, default_tag='others')
        
        # 获取统计信息
        db_stats = self.db.get_database_stats()
        total_repos = db_stats.get('repositories_count', 0)
        
        # 生成头部内容
        content = f"""# ✨ My Starred Repositories ✨

[![Stars](https://img.shields.io/badge/Total%20Repos-{total_repos}-blue.svg)](https://github.com/vincent623/My-Starred-Repositories)
[![AI Powered](https://img.shields.io/badge/AI%20Powered-🤖-brightgreen.svg)](https://github.com/vincent623/My-Starred-Repositories)
[![Auto Updated](https://img.shields.io/badge/Auto%20Updated-⚡-orange.svg)](https://github.com/vincent623/My-Starred-Repositories/actions)

> 🤖 **AI驱动的GitHub星标仓库智能管理系统** - 自动分析、分类和生成我收藏的优质项目清单

## 📊 统计概览

"""
        
        # 添加统计表格
        ordered_tags = [t for t in ORDERED_CATEGORIES if t in tag_stats]
        content += "| 分类 | 数量 | 占比 |\n"
        content += "|------|------|------|\n"
        
        for tag in ordered_tags:
            count = tag_stats[tag]
            percentage = (count / total_repos * 100) if total_repos > 0 else 0
            content += f"| {tag} | {count} | {percentage:.1f}% |\n"
        
        content += f"\n**总计**: {total_repos} 个精选仓库\n\n"
        
        # 生成目录
        content += "## 📖 分类目录\n\n"
        for tag in ordered_tags:
            count = tag_stats[tag]
            anchor = tag.lower().replace(' ', '-').replace('/', '-').replace('&', '')
            content += f"- [{tag}](#{anchor}) ({count}个)\n"
        
        content += "\n---\n\n"
        
        # 生成分类内容（折叠显示所有项目）
        for tag in ordered_tags:
            anchor = tag.lower().replace(' ', '-').replace('/', '-').replace('&', '')
            count = tag_stats[tag]
            
            # 获取该标签的所有仓库
            repos = self.db.get_repositories_by_personal_tag(tag)
            sorted_repos = sorted(repos, key=lambda x: x['name'])
            
            # 生成折叠标题
            content += f"## {tag}\n\n"
            content += f"<details>\n"
            content += f"<summary><strong>{count} 个精选项目</strong> 👆 点击展开</summary>\n\n"
            
            # 如果项目较多，添加顶部快速预览（前3个）
            if count > 3:
                content += "### 🌟 精选推荐\n\n"
                for repo in sorted_repos[:3]:
                    language = repo.get('language', 'Unknown')
                    summary = repo.get('summary', 'No summary')
                    url = repo['html_url']
                    content += f"- **[{repo['name']}]({url})** `{language}` - {summary}\n"
                content += f"\n### 📋 完整列表 ({count} 个项目)\n\n"
            
            # 生成完整项目列表
            for repo in sorted_repos:
                language = repo.get('language', 'Unknown')
                summary = repo.get('summary', 'No summary')
                url = repo['html_url']
                
                # 简化显示格式
                content += f"- **[{repo['name']}]({url})** `{language}` - {summary}\n"
            
            content += "\n</details>\n\n"
        
        # 添加项目说明和页脚
        content += f"""---

## 🚀 关于本项目

这是一个**AI驱动的GitHub星标仓库管理系统**，具备以下特性：

- 🤖 **智能分析**: 使用大语言模型自动分析每个仓库的价值和用途
- 🏷️ **智能分类**: 自动归类到10大技术领域
- 📊 **数据洞察**: 提供详细的统计分析和趋势洞察
- ⚡ **自动更新**: 通过GitHub Actions每周自动更新
- 🔒 **隐私安全**: 本地数据库存储，代码完全开源

### 📋 技术栈

- **后端**: Python 3.11+ + SQLite
- **AI模型**: 支持OpenRouter、OpenAI、Silicon Flow等多种LLM
- **自动化**: GitHub Actions
- **数据处理**: 智能标签合并与去重

### 🎯 快速开始

1. **Fork本仓库**: [My-Starred-Repositories](https://github.com/vincent623/My-Starred-Repositories)
2. **配置Secrets**: 参考 [GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)
3. **手动运行**: 在Actions页面触发首次运行
4. **享受自动化**: 每周一自动更新分析

### 📚 文档

- 📖 [详细设置指南](./SETUP.md)
- ⚙️ [GitHub Actions配置](./GITHUB_ACTIONS_SETUP.md)
- 📋 [产品需求文档](./prd.md)

---

*📅 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 🤖 自动生成 by [My Starred Repositories V3](https://github.com/vincent623/My-Starred-Repositories)*
"""
        
        # 保存文件
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("README.md 生成完成")
    
    def generate_weekly_report(self, new_repos: List[Dict]) -> None:
        """生成每周报告"""
        if not new_repos:
            logger.info("本周没有新增 Star 仓库，跳过周报生成")
            return
        
        logger.info("生成每周报告...")
        
        # 准备数据
        weekly_data = []
        for repo in new_repos:
            weekly_data.append(f"""
仓库：{repo['name']}
语言：{repo['language']}
GitHub主题：{', '.join(repo.get('github_topics', []))}
摘要：{repo['summary']}
个人标签：{', '.join(repo['tags'])}
价值：{repo['value']}
""")
        
        weekly_text = "\n".join(weekly_data)
        
        # 调用 LLM 生成报告
        prompt = REPORT_SUMMARY_PROMPT.format(weekly_data=weekly_text)
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=LLM_TEMPERATURE,
                max_tokens=1000
            )
            
            report_content = response.choices[0].message.content
            
            # 添加标题和时间
            final_report = f"""# My Starred Repos Weekly Insight Report - {datetime.now().strftime('%Y-%m-%d')}

{report_content}

---
*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*自动生成 by My Starred Repositories V3*
"""
            
            # 保存报告（覆盖最新）
            with open(WEEKLY_REPORT_FILE, 'w', encoding='utf-8') as f:
                f.write(final_report)

            # 归档一份周报（单独保存）
            try:
                os.makedirs(WEEKLY_REPORT_DIR, exist_ok=True)
                today = datetime.now()
                # 采用 ISO 周编号命名
                iso_year, iso_week, _ = today.isocalendar()
                archive_name = WEEKLY_REPORT_FILENAME_TEMPLATE_ISOWEEK.format(
                    year=iso_year, week=iso_week
                )
                archive_path = os.path.join(WEEKLY_REPORT_DIR, archive_name)
                with open(archive_path, 'w', encoding='utf-8') as f:
                    f.write(final_report)
            except Exception as arch_e:
                logger.warning(f"周报归档失败: {arch_e}")
            
            logger.info("每周报告生成完成")
            
        except Exception as e:
            logger.error(f"生成每周报告失败: {e}")
    
    def run(self, mode: str = "auto", force_reanalyze: bool = False, sample: Optional[int] = None, rebuild_only: bool = False) -> None:
        """运行主程序"""
        try:
            logger.info("开始运行 My Starred Repositories V3...")
            
            # 记录开始时间
            start_time = datetime.now()
            
            # 1. 获取 Star 仓库并直接写入数据库（每日/每周都应执行同步）
            self.get_starred_repositories()
            
            # 2. 处理仓库分析（支持强制/抽样）
            new_repos = []
            if not rebuild_only:
                new_repos = self.process_repositories(force_reanalyze=force_reanalyze, limit=sample)
            
            # 3. 更新标签数据
            self.update_tags_data()
            
            # 4. 生成 README.md
            self.generate_readme()
            
            # 5. 生成每周报告（按模式/周期控制）
            should_generate_weekly = False
            if mode == "weekly":
                should_generate_weekly = True
            elif mode == "auto":
                # 每周一生成
                try:
                    should_generate_weekly = datetime.now().weekday() == 0
                except Exception:
                    should_generate_weekly = False
            # daily 模式不生成

            if should_generate_weekly:
                self.generate_weekly_report(new_repos)
            
            # 记录处理历史
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.db.log_processing_history(
                action="full_run_v3",
                details={
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration": duration,
                    "new_repos": len(new_repos)
                }
            )
            
            # 显示统计信息
            stats = self.db.get_database_stats()
            logger.info("数据库 V3 统计信息:")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
            
            logger.info("所有任务完成！")
            
        except Exception as e:
            logger.error(f"程序运行出错: {e}")
            # 记录错误历史
            try:
                self.db.log_processing_history(
                    action="full_run_v3",
                    details={"error": str(e)},
                    status="error"
                )
            except:
                pass
            raise

@click.command()
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.option('--stats', is_flag=True, help='显示数据库统计信息')
@click.option('--init-dict', is_flag=True, help='初始化个人标签词典')
@click.option('--show-dict', is_flag=True, help='显示个人标签词典')
@click.option('--mode', type=click.Choice(['daily', 'weekly', 'auto']), default='auto', show_default=True, help='运行模式：daily=每日更新README；weekly=仅生成本周洞察；auto=每日更新且每周一生成洞察')
@click.option('--reset-tags', is_flag=True, help='将个人标签词典重置为配置的 10 大主类')
@click.option('--force-reanalyze', is_flag=True, help='强制全量重分析（忽略 analyzed_at 阈值）')
@click.option('--sample', type=int, default=None, help='仅分析前 N 个仓库用于快速验证')
@click.option('--rebuild-only', is_flag=True, help='不分析，仅重建统计并生成 README')
def main(debug, stats, init_dict, show_dict, mode, reset_tags, force_reanalyze, sample, rebuild_only):
    """主函数"""
    if debug:
        logger.add("debug.log", level="DEBUG")
    
    try:
        manager = StarredReposManagerV3()
        
        if stats:
            # 显示统计信息
            stats = manager.db.get_database_stats()
            print("数据库 V3 统计信息:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            return
        
        if init_dict:
            # 初始化个人标签词典
            logger.info("初始化个人标签词典...")
            manager._initialize_personal_tag_dictionary()
            logger.info("个人标签词典初始化完成")
            return
        
        if show_dict:
            # 显示个人标签词典
            dictionary = manager.db.get_personal_tag_dictionary()
            print("个人标签词典:")
            for item in dictionary:
                print(f"  {item['tag']} - {item['category']}: {item['description']}")
            return
        
        if reset_tags:
            # 重置个人标签词典为 10 大主类
            manager.db.reset_personal_tag_dictionary(ORDERED_CATEGORIES)
            logger.info("已将个人标签词典重置为 10 大主类")
            return
        
        # 正常运行
        manager.run(mode=mode, force_reanalyze=force_reanalyze, sample=sample, rebuild_only=rebuild_only)
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        exit(1)

if __name__ == "__main__":
    main()
