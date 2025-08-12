#!/usr/bin/env python3
"""
数据库操作模块 V3
优化标签逻辑和数据流，直接写入数据库
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
import os

from config import DATA_DIR, ORDERED_CATEGORIES, TAG_MERGE_RULES

logger = logging.getLogger(__name__)

class DatabaseManagerV3:
    """SQLite 数据库管理器 V3 - 优化版本"""
    
    def __init__(self, db_path: str = None):
        """初始化数据库管理器"""
        if db_path is None:
            db_path = os.path.join(DATA_DIR, "starred_repos_v3.db")
        
        self.db_path = db_path
        self.ensure_data_dir()
        self.init_database()
        
        logger.info(f"数据库管理器 V3 初始化完成，数据库路径: {self.db_path}")
    
    def ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs(DATA_DIR, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典形式的行
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建仓库表 - 优化字段设计
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS repositories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    language TEXT,
                    github_topics TEXT,  -- GitHub 原始 topics (JSON)
                    starred_at TEXT,
                    html_url TEXT NOT NULL,
                    updated_at TEXT,
                    
                    -- LLM 分析结果
                    summary TEXT,
                    personal_tags TEXT,  -- 个人自定义标签 (JSON)
                    value TEXT,
                    analyzed_at TEXT,
                    
                    -- 时间戳
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at_db TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建个人标签统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personal_tag_stats (
                    tag TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建个人标签词典表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personal_tag_dictionary (
                    tag TEXT PRIMARY KEY,
                    description TEXT,
                    category TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # 创建 GitHub topics 统计表（仅作参考）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS github_topics_stats (
                    topic TEXT PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建系统配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建处理历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    details TEXT,  -- JSON 格式存储
                    status TEXT DEFAULT 'success',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_repos_name ON repositories(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_repos_language ON repositories(language)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_repos_starred_at ON repositories(starred_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_repos_analyzed_at ON repositories(analyzed_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_personal_tags_count ON personal_tag_stats(count)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_github_topics_count ON github_topics_stats(count)')
            
            conn.commit()
            logger.info("数据库 V3 表结构初始化完成")
    
    def insert_repository_direct(self, repo_info: Dict) -> bool:
        """直接插入仓库数据（从 GitHub API 直接写入）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 准备数据
                data = {
                    'id': repo_info['id'],
                    'name': repo_info['name'],
                    'description': repo_info['description'],
                    'language': repo_info['language'],
                    'github_topics': json.dumps(repo_info['topics'], ensure_ascii=False),
                    'starred_at': repo_info['starred_at'],
                    'html_url': repo_info['html_url'],
                    'updated_at': repo_info['updated_at']
                }
                
                # 检查是否已存在
                cursor.execute('SELECT id FROM repositories WHERE id = ?', (data['id'],))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # 更新基本信息
                    set_clause = ', '.join([f"{k} = ?" for k in data.keys() if k != 'id'])
                    values = [v for k, v in data.items() if k != 'id']
                    values.append(data['id'])
                    
                    cursor.execute(f'UPDATE repositories SET {set_clause} WHERE id = ?', values)
                else:
                    # 插入新记录
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join(['?' for _ in data])
                    cursor.execute(f'INSERT INTO repositories ({columns}) VALUES ({placeholders})', list(data.values()))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"直接插入仓库数据失败: {e}")
            return False
    
    def update_repository_analysis(self, repo_id: str, analysis: Dict) -> bool:
        """更新仓库分析结果"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 准备分析数据
                data = {
                    'summary': analysis['summary'],
                    'personal_tags': json.dumps(analysis['tags'], ensure_ascii=False),
                    'value': analysis['value'],
                    'analyzed_at': analysis['analyzed_at'],
                    'updated_at_db': datetime.now().isoformat()
                }
                
                # 更新分析结果
                set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
                values = list(data.values())
                values.append(repo_id)
                
                cursor.execute(f'UPDATE repositories SET {set_clause} WHERE id = ?', values)
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"更新仓库分析结果失败: {e}")
            return False
    
    def get_repository(self, repo_id: str) -> Optional[Dict]:
        """获取单个仓库数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM repositories WHERE id = ?', (repo_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_dict(row)
                return None
                
        except Exception as e:
            logger.error(f"获取仓库数据失败: {e}")
            return None
    
    def get_repositories_needing_analysis(self, days_threshold: int = 30) -> List[Dict]:
        """获取需要重新分析的仓库"""
        try:
            threshold_date = datetime.now() - timedelta(days=days_threshold)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM repositories 
                    WHERE analyzed_at IS NULL OR analyzed_at < ?
                    ORDER BY starred_at DESC
                ''', (threshold_date.isoformat(),))
                
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"获取需要分析的仓库失败: {e}")
            return []
    
    def get_recent_repositories(self, days: int = 7) -> List[Dict]:
        """获取最近几天新增的仓库"""
        try:
            threshold_date = datetime.now() - timedelta(days=days)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM repositories 
                    WHERE starred_at >= ?
                    ORDER BY starred_at DESC
                ''', (threshold_date.isoformat(),))
                
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"获取最近仓库失败: {e}")
            return []
    
    def update_personal_tag_stats(self, tag: str, count: int = None) -> bool:
        """更新个人标签统计"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if count is None:
                    # 如果没有提供计数，则递增
                    cursor.execute('''
                        INSERT INTO personal_tag_stats (tag, count) 
                        VALUES (?, 1)
                        ON CONFLICT(tag) DO UPDATE SET count = count + 1, updated_at = CURRENT_TIMESTAMP
                    ''', (tag,))
                else:
                    # 设置具体计数
                    cursor.execute('''
                        INSERT OR REPLACE INTO personal_tag_stats (tag, count, updated_at) 
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (tag, count))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"更新个人标签统计失败: {e}")
            return False
    
    def rebuild_personal_tag_stats(self) -> bool:
        """重新构建个人标签统计"""
        try:
            logger.info("开始重新构建个人标签统计...")
            
            # 清空现有统计
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM personal_tag_stats')
                
                # 重新统计
                cursor.execute('SELECT personal_tags FROM repositories WHERE personal_tags IS NOT NULL')
                rows = cursor.fetchall()
                
                tag_counts = {}
                for row in rows:
                    tags = json.loads(row['personal_tags']) if row['personal_tags'] else []
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                # 插入新统计
                for tag, count in tag_counts.items():
                    cursor.execute('INSERT INTO personal_tag_stats (tag, count) VALUES (?, ?)', (tag, count))
                
                conn.commit()
                logger.info(f"个人标签统计重新构建完成，共 {len(tag_counts)} 个标签")
                return True
                
        except Exception as e:
            logger.error(f"重新构建个人标签统计失败: {e}")
            return False

    def normalize_personal_tags(self, allowed_tags: List[str] = None, default_tag: str = 'others') -> bool:
        """将所有仓库的个人标签规范为 10 大主类：
        - 若标签本身就是主类：保留
        - 若标签在合并规则的相似词中：映射到对应主类
        - 其他：归入 default_tag
        完成后重建统计
        """
        try:
            if allowed_tags is None:
                allowed_tags = ORDERED_CATEGORIES

            # 构建相似词到主类的映射（大小写不敏感）
            similar_to_main = {}
            for main_tag, similars in TAG_MERGE_RULES.items():
                for s in similars:
                    similar_to_main[s.lower()] = main_tag

            updated = 0
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, personal_tags FROM repositories')
                rows = cursor.fetchall()

                for row in rows:
                    tags = json.loads(row['personal_tags']) if row['personal_tags'] else []
                    normalized: List[str] = []
                    for t in tags:
                        if t in allowed_tags:
                            if t not in normalized:
                                normalized.append(t)
                            continue
                        mapped = similar_to_main.get(t.lower())
                        if mapped and mapped in allowed_tags and mapped not in normalized:
                            normalized.append(mapped)
                    if not normalized:
                        normalized = [default_tag]

                    serialized = json.dumps(normalized, ensure_ascii=False)
                    if serialized != (row['personal_tags'] or '[]'):
                        cursor.execute(
                            'UPDATE repositories SET personal_tags = ?, updated_at_db = CURRENT_TIMESTAMP WHERE id = ?',
                            (serialized, row['id'])
                        )
                        updated += 1

                conn.commit()

            # 重建统计
            self.rebuild_personal_tag_stats()
            logger.info(f"个人标签规范化完成，更新 {updated} 条记录")
            return True
        except Exception as e:
            logger.error(f"规范化个人标签失败: {e}")
            return False
    
    def get_all_personal_tag_stats(self) -> Dict[str, int]:
        """获取所有个人标签统计"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT tag, count FROM personal_tag_stats ORDER BY count DESC')
                rows = cursor.fetchall()
                
                return {row['tag']: row['count'] for row in rows}
                
        except Exception as e:
            logger.error(f"获取个人标签统计失败: {e}")
            return {}
    
    def get_repositories_by_personal_tag(self, tag: str) -> List[Dict]:
        """根据个人标签获取仓库"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM repositories 
                    WHERE json_extract(personal_tags, '$') LIKE ? 
                    ORDER BY starred_at DESC
                ''', (f'%{tag}%',))
                
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"根据个人标签获取仓库失败: {e}")
            return []
    
    def update_github_topics_stats(self, topics: List[str]) -> bool:
        """更新 GitHub topics 统计"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for topic in topics:
                    cursor.execute('''
                        INSERT INTO github_topics_stats (topic, count) 
                        VALUES (?, 1)
                        ON CONFLICT(topic) DO UPDATE SET count = count + 1
                    ''', (topic,))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"更新 GitHub topics 统计失败: {e}")
            return False
    
    def get_all_github_topics_stats(self) -> Dict[str, int]:
        """获取所有 GitHub topics 统计"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT topic, count FROM github_topics_stats ORDER BY count DESC')
                rows = cursor.fetchall()
                
                return {row['topic']: row['count'] for row in rows}
                
        except Exception as e:
            logger.error(f"获取 GitHub topics 统计失败: {e}")
            return {}
    
    def get_personal_tag_dictionary(self) -> List[Dict]:
        """获取个人标签词典"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM personal_tag_dictionary WHERE is_active = 1 ORDER BY category, tag')
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"获取个人标签词典失败: {e}")
            return []
    
    def add_personal_tag_to_dictionary(self, tag: str, description: str = '', category: str = '') -> bool:
        """添加标签到个人词典"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO personal_tag_dictionary (tag, description, category) 
                    VALUES (?, ?, ?)
                ''', (tag, description, category))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"添加个人标签到词典失败: {e}")
            return False

    def reset_personal_tag_dictionary(self, tags: List[str]) -> bool:
        """重置个人标签词典，仅保留传入的标签为激活状态"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # 将所有标签设为未激活
                cursor.execute('UPDATE personal_tag_dictionary SET is_active = 0')
                # 插入或激活指定标签
                for tag in tags:
                    cursor.execute('''
                        INSERT INTO personal_tag_dictionary (tag, description, category, is_active)
                        VALUES (?, ?, ?, 1)
                        ON CONFLICT(tag) DO UPDATE SET is_active = 1, category = excluded.category
                    ''', (tag, f"个人标签：{tag}", "主类"))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"重置个人标签词典失败: {e}")
            return False
    
    def get_system_config(self, key: str, default: Any = None) -> Any:
        """获取系统配置"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM system_config WHERE key = ?', (key,))
                row = cursor.fetchone()
                
                if row:
                    return json.loads(row['value'])
                return default
                
        except Exception as e:
            logger.error(f"获取系统配置失败: {e}")
            return default
    
    def set_system_config(self, key: str, value: Any) -> bool:
        """设置系统配置"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO system_config (key, value, updated_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, json.dumps(value, ensure_ascii=False)))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"设置系统配置失败: {e}")
            return False
    
    def log_processing_history(self, action: str, details: Dict = None, status: str = 'success') -> bool:
        """记录处理历史"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO processing_history (action, details, status) 
                    VALUES (?, ?, ?)
                ''', (action, json.dumps(details, ensure_ascii=False) if details else None, status))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"记录处理历史失败: {e}")
            return False
    
    def get_processing_history(self, limit: int = 50) -> List[Dict]:
        """获取处理历史"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM processing_history 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"获取处理历史失败: {e}")
            return []
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """将数据库行转换为字典"""
        result = dict(row)
        
        # 解析 JSON 字段
        if 'github_topics' in result and result['github_topics']:
            result['github_topics'] = json.loads(result['github_topics'])
        else:
            result['github_topics'] = []
        
        if 'personal_tags' in result and result['personal_tags']:
            result['personal_tags'] = json.loads(result['personal_tags'])
        else:
            result['personal_tags'] = []
        
        return result
    
    def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 仓库统计
                cursor.execute('SELECT COUNT(*) as count FROM repositories')
                stats['repositories_count'] = cursor.fetchone()['count']
                
                # 个人标签统计
                cursor.execute('SELECT COUNT(*) as count FROM personal_tag_stats')
                stats['personal_tags_count'] = cursor.fetchone()['count']
                
                # GitHub topics 统计
                cursor.execute('SELECT COUNT(*) as count FROM github_topics_stats')
                stats['github_topics_count'] = cursor.fetchone()['count']
                
                # 最近分析的仓库
                cursor.execute('SELECT COUNT(*) as count FROM repositories WHERE analyzed_at >= date("now", "-30 days")')
                stats['recently_analyzed'] = cursor.fetchone()['count']
                
                # 需要重新分析的仓库
                cursor.execute('SELECT COUNT(*) as count FROM repositories WHERE analyzed_at < date("now", "-30 days") OR analyzed_at IS NULL')
                stats['needs_analysis'] = cursor.fetchone()['count']
                
                # 数据库文件大小
                if os.path.exists(self.db_path):
                    stats['database_size'] = os.path.getsize(self.db_path)
                else:
                    stats['database_size'] = 0
                
                return stats
                
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
            return {}


# 全局数据库实例
_db_instance = None

def get_database_v3() -> DatabaseManagerV3:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManagerV3()
    return _db_instance


if __name__ == "__main__":
    # 测试数据库功能
    logging.basicConfig(level=logging.INFO)
    db = DatabaseManagerV3()
    
    # 显示统计信息
    stats = db.get_database_stats()
    print("数据库 V3 统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
