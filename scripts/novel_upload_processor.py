#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_upload_processor.py
---------------------------------
自动处理上传的小说：
- 扫描 uploads/pending 目录
- 校验并生成小说目录
- 自动生成 info.json（如缺失）
- 自动生成 slug（即使上传未提供）
- 更新 novels.json 索引
- 将失败上传移至 uploads/failed
- 成功的移至 uploads/processed
"""

import os
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
import re
import unicodedata

# ===================================
# 辅助函数
# ===================================

def slugify(text: str) -> str:
    """将标题转换为安全的目录 slug"""
    if not text:
        return "untitled"
    text = unicodedata.normalize('NFKD', text)
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-_')
    return text.lower() or "untitled"

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ===================================
# 主类
# ===================================

class NovelUploadProcessor:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parents[1]
        self.uploads_dir = self.base_dir / "uploads" / "pending"
        self.processed_dir = self.base_dir / "uploads" / "processed"
        self.failed_dir = self.base_dir / "uploads" / "failed"
        self.backup_dir = self.base_dir / "backups"
        self.novels_dir = self.base_dir / "novels"
        self.index_file = self.base_dir / "novels.json"
        self.log_file = self.base_dir / "upload_processor.log"

        for d in [
            self.uploads_dir, self.processed_dir,
            self.failed_dir, self.backup_dir, self.novels_dir
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        """记录日志"""
        line = f"[{timestamp()}] {message}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    # ===================================
    # 主处理入口
    # ===================================
    def run(self):
        self.log("🎬 开始小说上传处理流程")
        uploads = list(self.uploads_dir.glob("*"))
        if not uploads:
            self.log("⚠️ 未发现待处理上传，流程结束。")
            return

        # 创建索引备份
        if self.index_file.exists():
            backup_name = f"index_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy(self.index_file, self.backup_dir / backup_name)
            self.log(f"📦 索引备份创建: {self.backup_dir / backup_name}")

        success_count = 0
        fail_count = 0

        for upload_dir in uploads:
            if not upload_dir.is_dir():
                continue
            self.log(f"🚀 开始处理: {upload_dir.name}")
            try:
                self.process_upload(upload_dir)
                success_count += 1
            except Exception as e:
                fail_count += 1
                self.handle_failure(upload_dir, e)

        self.log(f"📊 处理完成: 成功 {success_count}, 失败 {fail_count}")

    # ===================================
    # 上传处理逻辑
    # ===================================
    def process_upload(self, upload_dir: Path):
        """处理单个上传"""
        info_path = upload_dir / "info.json"
        chapters = list(upload_dir.glob("*.md"))

        if not info_path.exists():
            raise FileNotFoundError(f"缺少 info.json: {upload_dir.name}")

        with open(info_path, "r", encoding="utf-8-sig") as f:
            novel_info = json.load(f)

        # 自动生成 slug
        if not novel_info.get("slug") or not novel_info["slug"].strip():
            auto_slug = slugify(novel_info.get("title", "untitled"))
            self.log(f"⚙️ 自动生成 slug: {auto_slug}")
            novel_info["slug"] = auto_slug

        slug = novel_info["slug"]
        target_dir = self.novels_dir / slug

        # 若目录存在则自动重命名
        if target_dir.exists():
            timestamp_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_slug = f"{slug}_{timestamp_suffix}"
            self.log(f"⚠️ 目录已存在，自动重命名为: {new_slug}")
            novel_info["slug"] = new_slug
            target_dir = self.novels_dir / new_slug

        # 创建小说目录
        target_dir.mkdir(parents=True, exist_ok=True)
        self.log(f"📁 创建小说目录: {target_dir}")

        # 复制章节文件
        if not chapters:
            raise ValueError(f"未找到章节文件: {upload_dir.name}")

        for chapter in chapters:
            shutil.copy(chapter, target_dir / chapter.name)
            self.log(f"✅ 章节已复制: {chapter.name}")

        # 写入 info.json
        with open(target_dir / "info.json", "w", encoding="utf-8") as f:
            json.dump(novel_info, f, ensure_ascii=False, indent=2)

        # 更新索引
        self.update_index(novel_info)

        # 移动上传目录到 processed
        processed_target = self.processed_dir / upload_dir.name
        shutil.move(str(upload_dir), processed_target)
        self.log(f"✅ 上传处理完成，已移动至 processed: {processed_target}")

    # ===================================
    # 更新索引文件
    # ===================================
    def update_index(self, novel_info):
        """更新主索引文件 novels.json"""
        data = {"novels": [], "lastUpdated": datetime.now().isoformat()}
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                self.log("⚠️ 索引文件读取失败，重新创建")

        if "novels" not in data:
            data["novels"] = []

        data["novels"].append(novel_info)
        data["totalNovels"] = len(data["novels"])
        data["lastUpdated"] = datetime.now().isoformat()

        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.log(f"📝 索引已更新: {self.index_file}")

    # ===================================
    # 处理失败的上传
    # ===================================
    def handle_failure(self, upload_dir: Path, error: Exception):
        """将失败上传移至 failed 并记录错误日志"""
        self.log(f"❌ 处理失败 {upload_dir.name}: {error}")
        self.log(f"🔍 错误详情: {traceback.format_exc()}")

        failed_target = self.failed_dir / upload_dir.name
        if failed_target.exists():
            shutil.rmtree(failed_target)
        shutil.move(str(upload_dir), failed_target)

        # 保存失败记录 JSON
        record = {
            "upload_id": upload_dir.name,
            "error_time": datetime.now().isoformat(),
            "error_message": str(error)
        }
        record_path = failed_target / "error_record.json"
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        self.log(f"❌ 移动到失败目录: {failed_target}")

# ===================================
# 入口点
# ===================================

if __name__ == "__main__":
    processor = NovelUploadProcessor()
    processor.run()
