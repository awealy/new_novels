#!/usr/bin/env python3
"""
智能小说索引生成脚本
自动扫描novels目录，解决目录冲突，生成统一索引
"""

import os
import sys
import json
import shutil
import hashlib
import random
import string
from datetime import datetime
from pathlib import Path

class SmartNovelIndexer:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.novels_dir = self.base_dir / "novels"
        self.index_file = self.base_dir / "novels.json"
        self.backup_dir = self.base_dir / "backups"
        self.log_file = self.base_dir / "indexer.log"
        
        # 确保目录存在
        self.novels_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
            
    def create_backup(self):
        """创建索引备份"""
        if self.index_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"index_backup_{timestamp}.json"
            try:
                shutil.copy2(self.index_file, backup_file)
                self.log(f"索引备份创建: {backup_file}")
                return True
            except Exception as e:
                self.log(f"备份创建失败: {e}", "WARNING")
        return False
        
    def generate_slug(self, title, max_length=50):
        """生成URL友好的slug"""
        import re
        
        if not title or not isinstance(title, str):
            title = "untitled"
            
        # 移除特殊字符，保留中文、字母、数字、空格、连字符
        slug = re.sub(r'[^\w\s\u4e00-\u9fa5-]', '', title.strip())
        # 将空格和连续分隔符替换为单个连字符
        slug = re.sub(r'[-\s]+', '-', slug)
        # 转换为小写并限制长度
        slug = slug.lower()[:max_length]
        
        return slug if slug else "novel"
        
    def ensure_unique_slug(self, base_slug, existing_slugs):
        """确保slug唯一性"""
        if base_slug not in existing_slugs:
            return base_slug
            
        # 如果冲突，添加随机后缀
        attempt = 0
        while attempt < 100:  # 防止无限循环
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            candidate_slug = f"{base_slug}-{random_suffix}"
            if candidate_slug not in existing_slugs:
                self.log(f"检测到目录冲突: {base_slug} -> {candidate_slug}")
                return candidate_slug
            attempt += 1
            
        # 如果随机后缀也冲突，使用时间戳
        timestamp = datetime.now().strftime("%H%M%S")
        unique_slug = f"{base_slug}-{timestamp}"
        self.log(f"使用时间戳解决冲突: {base_slug} -> {unique_slug}")
        return unique_slug
        
    def extract_chapter_info(self, content, filename, chapter_num):
        """从章节内容提取信息"""
        if not content.strip():
            return f"第{chapter_num}章", 0
            
        # 提取第一行作为标题（移除Markdown标题标记）
        first_line = content.strip().split('\n')[0]
        title = re.sub(r'^#+\s*', '', first_line).strip()
        
        # 如果标题无效，使用文件名或默认标题
        if not title or len(title) > 100:
            base_name = Path(filename).stem
            if base_name and base_name != filename and len(base_name) < 50:
                title = base_name
            else:
                title = f"第{chapter_num}章"
                
        word_count = len(content.strip())
        reading_time = max(1, word_count // 500)  # 估算阅读时间
        
        return title, word_count, f"{reading_time}分钟"
        
    def scan_novel_directory(self, novel_path, novel_slug):
        """扫描小说目录并提取信息"""
        info_file = novel_path / "info.json"
        
        if not info_file.exists():
            self.log(f"跳过目录 {novel_slug} (缺少info.json)", "WARNING")
            return None
            
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                novel_info = json.load(f)
                
            # 验证必要字段
            required_fields = ['id', 'title', 'author']
            for field in required_fields:
                if field not in novel_info:
                    self.log(f"小说 {novel_slug} 缺少必要字段: {field}", "WARNING")
                    return None
                    
            # 扫描章节文件
            chapters = []
            total_words = 0
            
            # 查找章节文件
            chapter_files = []
            for pattern in ['chapter*.md', '第*章.md', '*.md']:
                chapter_files.extend(novel_path.glob(pattern))
                
            # 排序章节文件
            chapter_files.sort()
            
            for i, chapter_file in enumerate(chapter_files, 1):
                if chapter_file.name == 'info.json':
                    continue
                    
                try:
                    with open(chapter_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    title, word_count, reading_time = self.extract_chapter_info(
                        content, chapter_file.name, i
                    )
                    
                    chapter_info = {
                        'number': i,
                        'title': title,
                        'file': chapter_file.name,
                        'wordCount': word_count,
                        'readingTime': reading_time
                    }
                    
                    chapters.append(chapter_info)
                    total_words += word_count
                    
                except Exception as e:
                    self.log(f"处理章节失败 {chapter_file}: {e}", "WARNING")
                    continue
                    
            # 更新小说信息
            novel_info['chapters'] = chapters
            novel_info['chapterCount'] = len(chapters)
            novel_info['wordCount'] = total_words
            novel_info['slug'] = novel_slug
            novel_info['path'] = f"novels/{novel_slug}"
            novel_info['lastUpdated'] = datetime.now().isoformat()
            
            # 确保封面图存在
            if 'cover' not in novel_info:
                novel_info['cover'] = '📖'
                
            # 确保描述存在
            if 'description' not in novel_info:
                novel_info['description'] = f"{novel_info['title']}，作者：{novel_info['author']}"
                
            # 确保标签存在
            if 'tags' not in novel_info or not novel_info['tags']:
                novel_info['tags'] = ['小说']
                
            # 确保状态存在
            if 'status' not in novel_info:
                novel_info['status'] = '连载中'
                
            self.log(f"已索引: {novel_info['title']} ({len(chapters)}章, {total_words}字)")
            return novel_info
            
        except Exception as e:
            self.log(f"处理小说失败 {novel_slug}: {e}", "ERROR")
            return None
            
    def generate_index(self):
        """生成主索引文件"""
        self.log("开始生成小说索引")
        
        # 创建备份
        self.create_backup()
        
        # 初始化索引数据结构
        index_data = {
            'version': '2.0',
            'lastUpdated': datetime.now().isoformat(),
            'totalNovels': 0,
            'totalChapters': 0,
            'totalWords': 0,
            'novels': []
        }
        
        if not self.novels_dir.exists():
            self.log("小说目录不存在，创建空索引")
            self.save_index(index_data)
            return True
            
        # 收集现有slug避免冲突
        existing_slugs = set()
        novel_directories = []
        
        # 第一遍扫描：收集所有现有目录
        for item in self.novels_dir.iterdir():
            if item.is_dir():
                existing_slugs.add(item.name)
                novel_directories.append(item)
                
        self.log(f"发现 {len(novel_directories)} 个小说目录")
        
        # 第二遍扫描：处理每个小说目录
        successful_novels = 0
        failed_novels = 0
        
        for novel_dir in novel_directories:
            novel_slug = novel_dir.name
            
            # 处理小说目录
            novel_info = self.scan_novel_directory(novel_dir, novel_slug)
            if novel_info:
                index_data['novels'].append(novel_info)
                successful_novels += 1
            else:
                failed_novels += 1
                
        # 计算统计信息
        index_data['totalNovels'] = successful_novels
        index_data['totalChapters'] = sum(len(novel.get('chapters', [])) for novel in index_data['novels'])
        index_data['totalWords'] = sum(novel.get('wordCount', 0) for novel in index_data['novels'])
        
        # 按ID排序
        index_data['novels'].sort(key=lambda x: x.get('id', 0))
        
        # 保存索引
        success = self.save_index(index_data)
        
        if success:
            self.log(f"索引生成完成: {successful_novels}本小说, {index_data['totalChapters']}个章节, {index_data['totalWords']}字")
        else:
            self.log("索引生成失败", "ERROR")
            
        return success and failed_novels == 0
        
    def save_index(self, index_data):
        """保存索引到文件"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            self.log(f"索引已保存: {self.index_file}")
            return True
        except Exception as e:
            self.log(f"保存索引失败: {e}", "ERROR")
            return False
            
    def cleanup_orphaned_directories(self):
        """清理孤儿目录（没有info.json的目录）"""
        if not self.novels_dir.exists():
            return
            
        orphaned_dirs = []
        for item in self.novels_dir.iterdir():
            if item.is_dir() and not (item / "info.json").exists():
                orphaned_dirs.append(item)
                
        if orphaned_dirs:
            self.log(f"发现 {len(orphaned_dirs)} 个孤儿目录")
            for dir_path in orphaned_dirs:
                self.log(f"孤儿目录: {dir_path.name}")
                
        return len(orphaned_dirs)

def main():
    """主函数"""
    try:
        indexer = SmartNovelIndexer()
        indexer.log("🎬 开始小说索引生成流程")
        
        success = indexer.generate_index()
        
        # 检查孤儿目录（只记录，不自动删除）
        orphaned_count = indexer.cleanup_orphaned_directories()
        if orphaned_count > 0:
            indexer.log(f"发现 {orphaned_count} 个孤儿目录，建议手动处理")
        
        if success:
            indexer.log("✅ 索引生成流程完成")
            return 0
        else:
            indexer.log("❌ 索引生成流程失败")
            return 1
            
    except Exception as e:
        print(f"💥 致命错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
