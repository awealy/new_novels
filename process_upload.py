#!/usr/bin/env python3
"""
小说上传处理脚本 - 增强错误处理版本
"""

import os
import sys
import json
import shutil
import hashlib
import traceback
from datetime import datetime
from pathlib import Path

class UploadProcessor:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.uploads_dir = self.base_dir / "uploads" / "pending"
        self.novels_dir = self.base_dir / "novels"
        self.processed_dir = self.base_dir / "uploads" / "processed"
        self.failed_dir = self.base_dir / "uploads" / "failed"
        self.backup_dir = self.base_dir / "backups"
        self.log_file = self.base_dir / "upload_process.log"
        
    def setup_directories(self):
        """创建必要的目录结构"""
        try:
            for directory in [self.novels_dir, self.processed_dir, 
                             self.failed_dir, self.backup_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            self.log("✅ 目录结构初始化完成")
            return True
        except Exception as e:
            self.log(f"❌ 目录创建失败: {e}")
            return False
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\\n')
            
    def validate_environment(self):
        """验证运行环境"""
        self.log("🔍 验证运行环境...")
        
        # 检查必要目录
        if not self.uploads_dir.exists():
            self.log("⚠️ uploads/pending目录不存在")
            return False
            
        # 检查Git配置
        try:
            import subprocess
            result = subprocess.run(['git', 'status'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log("❌ Git环境异常")
                return False
        except Exception as e:
            self.log(f"❌ Git检查失败: {e}")
            return False
            
        self.log("✅ 环境验证通过")
        return True
        
    def backup_index(self):
        """备份当前索引文件"""
        index_file = self.base_dir / "novels.json"
        if index_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"index_backup_{timestamp}.json"
            try:
                shutil.copy2(index_file, backup_file)
                self.log(f"📦 索引备份创建: {backup_file}")
                return True
            except Exception as e:
                self.log(f"⚠️ 备份创建失败: {e}")
        else:
            self.log("ℹ️ 无现有索引文件需要备份")
        return False
        
    def scan_pending_uploads(self):
        """扫描待处理的上传"""
        if not self.uploads_dir.exists():
            self.log("📭 无待处理的上传目录")
            return []
            
        upload_items = []
        for item in self.uploads_dir.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    upload_items.append(item.name)
                else:
                    self.log(f"⚠️ 跳过无效上传目录: {item.name} (缺少metadata.json)")
                    
        self.log(f"🔍 发现 {len(upload_items)} 个待处理上传")
        return upload_items
        
    def process_upload(self, upload_id):
        """处理单个上传"""
        upload_path = self.uploads_dir / upload_id
        
        try:
            self.log(f"🚀 开始处理: {upload_id}")
            
            # 验证上传完整性
            if not self.validate_upload(upload_path):
                raise ValueError("上传验证失败")
                
            # 读取元数据
            metadata = self.load_metadata(upload_path)
            if not metadata:
                raise ValueError("元数据读取失败")
                
            # 生成小说信息
            novel_info = self.create_novel_info(metadata, upload_path)
            
            # 创建小说目录
            novel_dir = self.novels_dir / novel_info['slug']
            if novel_dir.exists():
                raise ValueError(f"小说目录已存在: {novel_info['slug']}")
                
            novel_dir.mkdir(parents=True)
            
            # 处理章节文件
            chapters = self.process_chapters(upload_path, novel_dir)
            novel_info['chapters'] = chapters
            novel_info['wordCount'] = sum(c.get('wordCount', 0) for c in chapters)
            novel_info['chapterCount'] = len(chapters)
            
            # 保存小说信息
            self.save_novel_info(novel_dir, novel_info)
            
            # 更新主索引
            self.update_main_index(novel_info)
            
            # 移动处理完成的文件
            self.move_to_processed(upload_path, upload_id)
            
            self.log(f"✅ 成功处理: {novel_info['title']}")
            return True
            
        except Exception as e:
            self.log(f"❌ 处理失败 {upload_id}: {e}")
            self.log(f"🔍 错误详情: {traceback.format_exc()}")
            self.move_to_failed(upload_path, upload_id, str(e))
            return False
            
    def validate_upload(self, upload_path):
        """验证上传完整性"""
        required_files = ['metadata.json']
        
        for req_file in required_files:
            if not (upload_path / req_file).exists():
                raise ValueError(f"缺少必要文件: {req_file}")
                
        # 检查章节文件
        md_files = list(upload_path.glob("*.md"))
        if not md_files:
            raise ValueError("未找到Markdown章节文件")
            
        self.log(f"✅ 上传验证通过，找到 {len(md_files)} 个章节文件")
        return True
        
    def load_metadata(self, upload_path):
        """加载元数据"""
        metadata_file = upload_path / "metadata.json"
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            required_fields = ['title', 'author', 'description', 'tags']
            for field in required_fields:
                if field not in metadata:
                    raise ValueError(f"元数据缺少字段: {field}")
                    
            return metadata
        except Exception as e:
            raise ValueError(f"元数据读取失败: {e}")
            
    def create_novel_info(self, metadata, upload_path):
        """创建小说信息"""
        novel_id = self.generate_novel_id()
        novel_slug = self.create_slug(metadata['title'])
        
        return {
            'id': novel_id,
            'title': metadata['title'],
            'author': metadata['author'],
            'description': metadata['description'],
            'tags': metadata['tags'] if isinstance(metadata['tags'], list) else [metadata['tags']],
            'cover': metadata.get('cover', '📖'),
            'slug': novel_slug,
            'path': f'novels/{novel_slug}',
            'updateTime': datetime.now().isoformat(),
            'status': '连载中'
        }
        
    def generate_novel_id(self):
        """生成小说ID"""
        index_file = self.base_dir / "novels.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    novels = data.get('novels', [])
                    if novels:
                        existing_ids = [n.get('id', 0) for n in novels if n.get('id')]
                        return max(existing_ids) + 1 if existing_ids else 1
            except Exception as e:
                self.log(f"⚠️ 读取索引失败: {e}")
        return 1
        
    def create_slug(self, title):
        """生成URL友好的slug"""
        import re
        slug = re.sub(r'[^\\w\\s-]', '', title.lower())
        slug = re.sub(r'[-\\s]+', '-', slug)
        return slug[:50]
        
    def process_chapters(self, upload_path, novel_dir):
        """处理章节文件"""
        chapters = []
        md_files = sorted([f for f in upload_path.glob("*.md") if f.name != "metadata.json"])
        
        for i, md_file in enumerate(md_files, 1):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                word_count = len(content.strip())
                reading_time = max(1, word_count // 500)
                
                # 提取标题
                title = self.extract_chapter_title(content, md_file.name, i)
                
                # 复制文件
                chapter_file = f"chapter{i}.md"
                target_path = novel_dir / chapter_file
                shutil.copy2(md_file, target_path)
                
                chapters.append({
                    'number': i,
                    'title': title,
                    'file': chapter_file,
                    'wordCount': word_count,
                    'readingTime': f'{reading_time}分钟'
                })
                
            except Exception as e:
                self.log(f"⚠️ 处理章节失败 {md_file.name}: {e}")
                continue
                
        return chapters
        
    def extract_chapter_title(self, content, filename, chapter_num):
        """提取章节标题"""
        if not content.strip():
            return f"第{chapter_num}章"
            
        first_line = content.strip().split('\\n')[0]
        title = re.sub(r'^#+\\s*', '', first_line).strip()
        
        if title and len(title) < 100:
            return title
            
        base_name = Path(filename).stem
        if base_name and base_name != filename:
            return base_name
            
        return f"第{chapter_num}章"
        
    def save_novel_info(self, novel_dir, novel_info):
        """保存小说信息"""
        info_file = novel_dir / "info.json"
        try:
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(novel_info, f, ensure_ascii=False, indent=2)
            self.log(f"💾 小说信息保存: {info_file}")
        except Exception as e:
            raise ValueError(f"保存小说信息失败: {e}")
            
    def update_main_index(self, novel_info):
        """更新主索引"""
        index_file = self.base_dir / "novels.json"
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self.log(f"⚠️ 读取索引失败，创建新索引: {e}")
                data = {'version': '2.0', 'novels': []}
        else:
            data = {'version': '2.0', 'novels': []}
            
        # 移除重复ID
        data['novels'] = [n for n in data['novels'] if n.get('id') != novel_info['id']]
        data['novels'].append(novel_info)
        data['novels'].sort(key=lambda x: x.get('id', 0))
        
        # 更新统计信息
        data['lastUpdated'] = datetime.now().isoformat()
        data['totalNovels'] = len(data['novels'])
        data['totalChapters'] = sum(len(n.get('chapters', [])) for n in data['novels'])
        data['totalWords'] = sum(n.get('wordCount', 0) for n in data['novels'])
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log("📚 主索引更新完成")
        except Exception as e:
            raise ValueError(f"保存索引失败: {e}")
            
    def move_to_processed(self, upload_path, upload_id):
        """移动到已处理目录"""
        processed_path = self.processed_dir / upload_id
        if upload_path.exists():
            shutil.move(upload_path, processed_path)
            self.log(f"📁 移动到已处理: {processed_path}")
            
    def move_to_failed(self, upload_path, upload_id, error_msg):
        """移动到失败目录"""
        failed_path = self.failed_dir / upload_id
        if upload_path.exists():
            shutil.move(upload_path, failed_path)
            
            # 记录错误信息
            error_log = {
                'upload_id': upload_id,
                'error_time': datetime.now().isoformat(),
                'error_message': error_msg
            }
            
            error_file = failed_path / 'error.json'
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_log, f, indent=2)
                
            self.log(f"❌ 移动到失败目录: {failed_path}")
            
    def run(self):
        """主运行方法"""
        self.log("🎬 开始小说上传处理流程")
        
        # 环境设置
        if not self.setup_directories():
            return False, 0, 0
            
        if not self.validate_environment():
            return False, 0, 0
            
        # 备份和扫描
        self.backup_index()
        upload_items = self.scan_pending_uploads()
        
        if not upload_items:
            self.log("📭 无待处理的上传")
            return True, 0, 0
            
        # 处理上传
        success_count = 0
        fail_count = 0
        
        for upload_id in upload_items:
            if self.process_upload(upload_id):
                success_count += 1
            else:
                fail_count += 1
                
        self.log(f"📊 处理完成: 成功 {success_count}, 失败 {fail_count}")
        return True, success_count, fail_count
        
if __name__ == "__main__":
    processor = UploadProcessor()
    success, success_count, fail_count = processor.run()
    
    # 设置退出码
    if not success or fail_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)
