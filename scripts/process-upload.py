#!/usr/bin/env python3
"""
小说上传处理脚本
自动处理上传的Markdown文件，生成元数据和索引
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
import re

class NovelProcessor:
    def __init__(self):
        self.uploads_dir = "uploads/pending"
        self.novels_dir = "novels"
        self.processed_dir = "uploads/processed"
        self.novels_json = "novels.json"
        
    def ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.novels_dir, exist_ok=True)
        
    def get_next_novel_id(self):
        """获取下一个可用的novel ID"""
        if os.path.exists(self.novels_json):
            with open(self.novels_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                novels = data.get('novels', [])
                if novels:
                    return max(novel['id'] for novel in novels) + 1
        return 1
        
    def process_uploaded_files(self):
        """处理上传的文件"""
        if not os.path.exists(self.uploads_dir):
            print("No uploads to process")
            return
            
        for item in os.listdir(self.uploads_dir):
            item_path = os.path.join(self.uploads_dir, item)
            if os.path.isdir(item_path):
                self.process_novel_upload(item_path, item)
                
    def process_novel_upload(self, upload_path, upload_id):
        """处理单个小说上传"""
        try:
            # 读取上传的元数据
            metadata_file = os.path.join(upload_path, "metadata.json")
            if not os.path.exists(metadata_file):
                print(f"Metadata not found for {upload_id}")
                return
                
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # 获取下一个ID
            novel_id = self.get_next_novel_id()
            
            # 创建小说目录
            novel_slug = self.create_slug(metadata['title'])
            novel_dir = os.path.join(self.novels_dir, novel_slug)
            os.makedirs(novel_dir, exist_ok=True)
            
            # 处理章节文件
            chapters = self.process_chapters(upload_path, novel_dir)
            
            # 生成小说信息
            novel_info = {
                "id": novel_id,
                "title": metadata['title'],
                "author": metadata['author'],
                "description": metadata['description'],
                "tags": metadata['tags'],
                "cover": "📖",  # 默认封面
                "path": f"novels/{novel_slug}",
                "chapters": chapters,
                "updateTime": datetime.now().strftime("%Y-%m-%d"),
                "wordCount": sum(chap.get('wordCount', 0) for chap in chapters),
                "status": "连载中"
            }
            
            # 保存小说信息
            with open(os.path.join(novel_dir, "info.json"), 'w', encoding='utf-8') as f:
                json.dump(novel_info, f, ensure_ascii=False, indent=2)
                
            # 更新主索引
            self.update_novels_index(novel_info)
            
            # 移动处理完成的文件
            processed_path = os.path.join(self.processed_dir, upload_id)
            shutil.move(upload_path, processed_path)
            
            print(f"Successfully processed novel: {metadata['title']}")
            
        except Exception as e:
            print(f"Error processing novel {upload_id}: {str(e)}")
            
    def process_chapters(self, upload_path, novel_dir):
        """处理章节文件"""
        chapters = []
        chapter_files = []
        
        # 收集所有.md文件
        for file in os.listdir(upload_path):
            if file.endswith('.md') and file != 'metadata.json':
                chapter_files.append(file)
                
        # 按文件名排序
        chapter_files.sort()
        
        for i, filename in enumerate(chapter_files, 1):
            source_path = os.path.join(upload_path, filename)
            chapter_file = f"chapter{i}.md"
            target_path = os.path.join(novel_dir, chapter_file)
            
            # 读取章节内容
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 计算字数和阅读时间
            word_count = len(content.strip())
            reading_time = max(1, word_count // 500)  # 假设阅读速度500字/分钟
            
            # 从内容中提取标题（第一行作为标题）
            title = self.extract_chapter_title(content, filename, i)
            
            # 复制文件到小说目录
            shutil.copy2(source_path, target_path)
            
            chapters.append({
                "title": title,
                "file": chapter_file,
                "wordCount": word_count,
                "readingTime": f"{reading_time}分钟"
            })
            
        return chapters
        
    def extract_chapter_title(self, content, filename, chapter_num):
        """从内容中提取章节标题"""
        # 尝试从第一行提取标题
        first_line = content.strip().split('\n')[0] if content.strip() else ""
        
        # 移除Markdown标题标记
        title = re.sub(r'^#+\s*', '', first_line).strip()
        
        if title and len(title) < 100:  # 合理的标题长度
            return title
            
        # 如果无法从内容提取，使用文件名或生成默认标题
        base_name = os.path.splitext(filename)[0]
        if base_name and base_name != filename:
            return base_name
            
        return f"第{chapter_num}章"
        
    def update_novels_index(self, novel_info):
        """更新主novels.json索引"""
        novels_data = {"novels": [], "version": "1.0", "lastUpdated": datetime.now().isoformat()}
        
        if os.path.exists(self.novels_json):
            with open(self.novels_json, 'r', encoding='utf-8') as f:
                novels_data = json.load(f)
                
        # 检查是否已存在相同ID的小说
        novels_data['novels'] = [n for n in novels_data['novels'] if n['id'] != novel_info['id']]
        
        # 添加新小说
        novels_data['novels'].append(novel_info)
        
        # 按ID排序
        novels_data['novels'].sort(key=lambda x: x['id'])
        
        # 保存更新
        with open(self.novels_json, 'w', encoding='utf-8') as f:
            json.dump(novels_data, f, ensure_ascii=False, indent=2)
            
    def create_slug(self, title):
        """生成URL友好的slug"""
        # 移除特殊字符，替换空格为连字符
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:50]  # 限制长度
        
def main():
    processor = NovelProcessor()
    processor.ensure_directories()
    processor.process_uploaded_files()
    
if __name__ == "__main__":
    main()
