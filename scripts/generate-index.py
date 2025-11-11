#!/usr/bin/env python3
"""
增强的索引生成脚本
自动扫描novels目录并生成统一的索引文件
"""

import os
import json
import shutil
from datetime import datetime
import hashlib

class EnhancedIndexGenerator:
    def __init__(self):
        self.novels_dir = "novels"
        self.index_file = "novels.json"
        self.backup_dir = "backups"
        
    def ensure_directories(self):
        """确保目录存在"""
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def create_backup(self):
        """创建索引文件备份"""
        if os.path.exists(self.index_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.backup_dir}/index_backup_{timestamp}.json"
            shutil.copy2(self.index_file, backup_file)
            print(f"📦 创建索引备份: {backup_file}")
    
    def generate_index(self):
        """生成小说索引"""
        novels_data = {
            "version": "2.0",
            "lastUpdated": datetime.now().isoformat(),
            "totalNovels": 0,
            "totalChapters": 0,
            "totalWords": 0,
            "novels": []
        }
        
        if not os.path.exists(self.novels_dir):
            print(f"⚠️ 小说目录 '{self.novels_dir}' 不存在")
            self.save_index(novels_data)
            return
            
        # 扫描novels目录
        novel_slugs = []
        for item in os.listdir(self.novels_dir):
            item_path = os.path.join(self.novels_dir, item)
            info_file = os.path.join(item_path, "info.json")
            
            if os.path.isdir(item_path) and os.path.exists(info_file):
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        novel_info = json.load(f)
                        
                    # 验证必要字段
                    if self.validate_novel_info(novel_info, item):
                        novels_data['novels'].append(novel_info)
                        novel_slugs.append(item)
                        print(f"✅ 已索引: {novel_info.get('title', '未知标题')}")
                        
                except Exception as e:
                    print(f"❌ 读取 {info_file} 失败: {e}")
        
        # 计算统计信息
        novels_data['totalNovels'] = len(novels_data['novels'])
        novels_data['totalChapters'] = sum(
            novel.get('chapterCount', 0) for novel in novels_data['novels']
        )
        novels_data['totalWords'] = sum(
            novel.get('wordCount', 0) for novel in novels_data['novels']
        )
        
        # 按ID排序
        novels_data['novels'].sort(key=lambda x: x.get('id', 0))
        
        # 保存索引
        self.save_index(novels_data)
        print(f"📊 索引生成完成: {novels_data['totalNovels']} 本小说, "
              f"{novels_data['totalChapters']} 个章节, "
              f"{novels_data['totalWords']} 字")
    
    def validate_novel_info(self, novel_info, novel_slug):
        """验证小说信息的完整性"""
        required_fields = ['id', 'title', 'author', 'chapters']
        
        for field in required_fields:
            if field not in novel_info:
                print(f"⚠️ 小说 {novel_slug} 缺少必要字段: {field}")
                return False
                
        if not isinstance(novel_info.get('chapters'), list):
            print(f"⚠️ 小说 {novel_slug} 章节格式错误")
            return False
            
        return True
    
    def save_index(self, novels_data):
        """保存索引文件"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(novels_data, f, ensure_ascii=False, indent=2)
            print(f"💾 索引已保存到: {self.index_file}")
        except Exception as e:
            print(f"❌ 保存索引失败: {e}")
            # 尝试使用备用编码
            try:
                with open(self.index_file, 'w', encoding='gbk') as f:
                    json.dump(novels_data, f, ensure_ascii=False, indent=2)
                print("💾 使用备用编码保存成功")
            except Exception as e2:
                print(f"❌ 备用编码保存也失败: {e2}")

def main():
    """主函数"""
    try:
        generator = EnhancedIndexGenerator()
        generator.ensure_directories()
        generator.create_backup()
        generator.generate_index()
        print("🎉 索引生成流程完成")
    except Exception as e:
        print(f"💥 索引生成失败: {e}")
        exit(1)

if __name__ == "__main__":
    main()
