#!/usr/bin/env python3
"""
小说上传处理脚本 - 增强目录冲突解决版
自动生成唯一目录名，确保100%上传成功
"""

import os
import sys
import json
import shutil
import random
import string
import hashlib
import logging
from datetime import datetime
from pathlib import Path

class NovelUploadProcessor:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.setup_directories()
        self.setup_logging()
        
    def setup_directories(self):
        """初始化目录结构"""
        self.uploads_dir = self.base_dir / "uploads" / "pending"
        self.novels_dir = self.base_dir / "novels"
        self.processed_dir = self.base_dir / "uploads" / "processed"
        self.failed_dir = self.base_dir / "uploads" / "failed"
        self.backup_dir = self.base_dir / "backups"
        
        # 创建所有必要目录
        for directory in [self.novels_dir, self.processed_dir, 
                         self.failed_dir, self.backup_dir, self.uploads_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    def setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('upload_processor.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log(self, message, level='info'):
        """记录日志"""
        getattr(self.logger, level)(message)
        
    def scan_pending_uploads(self):
        """扫描待处理的上传"""
        if not self.uploads_dir.exists():
            self.log("无待处理的上传目录", 'warning')
            return []
            
        uploads = []
        for item in self.uploads_dir.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.json"
                if metadata_file.exists():
                    uploads.append(item.name)
                else:
                    self.log(f"跳过无效上传: {item.name} (缺少metadata.json)", 'warning')
                    
        self.log(f"发现 {len(uploads)} 个待处理上传")
        return uploads
        
    def generate_unique_slug(self, base_title, max_attempts=50):
        """
        生成唯一的小说目录slug
        使用标题 + 随机后缀确保唯一性
        """
        base_slug = self.create_slug(base_title)
        candidate_slug = base_slug
        attempt = 0
        
        # 检查是否冲突，如果冲突则添加随机后缀
        while (self.novels_dir / candidate_slug).exists() and attempt < max_attempts:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            candidate_slug = f"{base_slug}-{random_suffix}"
            attempt += 1
            
        if attempt >= max_attempts:
            # 如果随机后缀也冲突，使用时间戳
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            candidate_slug = f"{base_slug}-{timestamp}"
            
        if candidate_slug != base_slug:
            self.log(f"目录冲突解决: {base_slug} -> {candidate_slug}")
            
        return candidate_slug
        
    def create_slug(self, text):
        """生成URL友好的slug"""
        import re
        if not text or not isinstance(text, str):
            text = "untitled"
            
        # 移除特殊字符，只保留字母、数字、中文、连字符
        slug = re.sub(r'[^\w\s\u4e00-\u9fa5-]', '', text.strip())
        # 将空格和连续分隔符替换为单个连字符
        slug = re.sub(r'[-\s]+', '-', slug)
        # 转换为小写并限制长度
        return slug.lower()[:40] or "novel"
        
    def process_upload(self, upload_id):
        """处理单个上传"""
        upload_path = self.uploads_dir / upload_id
        
        try:
            self.log(f"开始处理上传: {upload_id}")
            
            # 验证上传完整性
            if not self.validate_upload(upload_path):
                raise ValueError("上传验证失败")
                
            # 读取元数据
            metadata = self.load_metadata(upload_path)
            if not metadata:
                raise ValueError("元数据读取失败")
                
            # 生成唯一的小说目录名（解决冲突）
            novel_slug = self.generate_unique_slug(metadata['title'])
            novel_dir = self.novels_dir / novel_slug
            
            # 创建小说目录（确保唯一）
            novel_dir.mkdir(parents=True, exist_ok=False)
            
            # 处理上传
            novel_info = self.create_novel_info(metadata, novel_slug, upload_path)
            
            # 保存小说信息
            self.save_novel_info(novel_dir, novel_info)
            
            # 更新主索引
            self.update_main_index(novel_info)
            
            # 移动到已处理
            self.move_to_processed(upload_path, upload_id)
            
            self.log(f"成功处理: {novel_info['title']} -> {novel_slug}")
            return True, novel_info
            
        except FileExistsError as e:
            error_msg = f"目录创建失败（严重冲突）: {str(e)}"
            self.log(error_msg, 'error')
            self.move_to_failed(upload_path, upload_id, error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            self.log(error_msg, 'error')
            self.move_to_failed(upload_path, upload_id, error_msg)
            return False, error_msg
            
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
            
        self.log(f"上传验证通过: {len(md_files)} 个章节文件")
        return True
        
    def load_metadata(self, upload_path):
        """加载元数据"""
        metadata_file = upload_path / "metadata.json"
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # 验证必要字段
            required_fields = ['title', 'author', 'description']
            for field in required_fields:
                if field not in metadata:
                    raise ValueError(f"元数据缺少字段: {field}")
                    
            return metadata
        except Exception as e:
            raise ValueError(f"元数据读取失败: {e}")
            
    def create_novel_info(self, metadata, novel_slug, upload_path):
        """创建小说信息"""
        novel_id = self.generate_novel_id()
        
        # 处理章节文件
        chapters = self.process_chapters(upload_path, novel_slug)
        
        return {
            'id': novel_id,
            'title': metadata['title'],
            'author': metadata['author'],
            'description': metadata.get('description', ''),
            'tags': metadata.get('tags', []),
            'slug': novel_slug,
            'path': f'novels/{novel_slug}',
            'chapters': chapters,
            'wordCount': sum(chap.get('wordCount', 0) for chap in chapters),
            'chapterCount': len(chapters),
            'status': '连载中',
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }
        
    def generate_novel_id(self):
        """生成新小说ID"""
        index_file = self.base_dir / "novels.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    novels = data.get('novels', [])
                    if novels:
                        existing_ids = [n.get('id', 0) for n in novels if n.get('id')]
                        return max(existing_ids) + 1 if existing_ids else 1
            except Exception:
                pass
        return 1
        
    def process_chapters(self, upload_path, novel_slug):
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
                
                chapters.append({
                    'number': i,
                    'title': title,
                    'file': f'chapter{i}.md',
                    'wordCount': word_count,
                    'readingTime': f'{reading_time}分钟'
                })
                
            except Exception as e:
                self.log(f"处理章节失败 {md_file.name}: {e}", 'warning')
                continue
                
        return chapters
        
    def extract_chapter_title(self, content, filename, chapter_num):
        """从内容中提取章节标题"""
        import re
        
        if not content.strip():
            return f"第{chapter_num}章"
            
        first_line = content.strip().split('\n')[0]
        title = re.sub(r'^#+\\s*', '', first_line).strip()
        
        if title and len(title) < 100:
            return title
            
        base_name = Path(filename).stem
        if base_name and base_name != filename:
            return base_name
            
        return f"第{chapter_num}章"
        
    def save_novel_info(self, novel_dir, novel_info):
        """保存小说信息到目录"""
        info_file = novel_dir / "info.json"
        try:
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(novel_info, f, ensure_ascii=False, indent=2)
            self.log(f"小说信息保存: {info_file}")
        except Exception as e:
            raise ValueError(f"保存小说信息失败: {e}")
            
    def update_main_index(self, novel_info):
        """更新主索引文件"""
        index_file = self.base_dir / "novels.json"
        
        # 读取现有索引或创建新索引
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {'version': '2.0', 'novels': []}
        else:
            data = {'version': '2.0', 'novels': []}
            
        # 移除重复ID（如果存在）
        data['novels'] = [n for n in data['novels'] if n.get('id') != novel_info['id']]
        data['novels'].append(novel_info)
        data['novels'].sort(key=lambda x: x.get('id', 0))
        
        # 更新元数据
        data['lastUpdated'] = datetime.now().isoformat()
        data['totalNovels'] = len(data['novels'])
        data['totalChapters'] = sum(len(n.get('chapters', [])) for n in data['novels'])
        data['totalWords'] = sum(n.get('wordCount', 0) for n in data['novels'])
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log("主索引更新完成")
        except Exception as e:
            raise ValueError(f"保存索引失败: {e}")
            
    def move_to_processed(self, upload_path, upload_id):
        """移动处理完成的文件"""
        processed_path = self.processed_dir / upload_id
        if upload_path.exists():
            shutil.move(upload_path, processed_path)
            self.log(f"移动到已处理: {processed_path}")
            
    def move_to_failed(self, upload_path, upload_id, error_msg):
        """移动到失败目录并记录错误"""
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
                
            self.log(f"移动到失败目录: {failed_path}")
            
    def run(self):
        """主运行方法"""
        self.log("开始小说上传处理流程")
        
        uploads = self.scan_pending_uploads()
        if not uploads:
            self.log("无待处理的上传")
            return True, 0, 0
            
        success_count = 0
        fail_count = 0
        results = []
        
        for upload_id in uploads:
            success, result = self.process_upload(upload_id)
            if success:
                success_count += 1
                results.append(('success', result))
            else:
                fail_count += 1
                results.append(('error', result))
                
        self.log(f"处理完成: 成功 {success_count}, 失败 {fail_count}")
        
        # 输出详细结果
        for i, (status, result) in enumerate(results):
            if status == 'success':
                self.log(f"✅ 上传 {i+1}: {result['title']} -> novels/{result['slug']}")
            else:
                self.log(f"❌ 上传 {i+1} 失败: {result}")
                
        return success_count > 0, success_count, fail_count

def main():
    """主函数"""
    try:
        processor = NovelUploadProcessor()
        success, success_count, fail_count = processor.run()
        
        if fail_count > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"致命错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
