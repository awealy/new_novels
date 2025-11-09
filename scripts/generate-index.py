#!/usr/bin/env python3
"""
自动生成小说索引脚本
扫描novels目录，生成统一的novels.json索引文件
"""

import os
import json
from datetime import datetime

def generate_novels_index():
    novels_dir = "novels"
    index_file = "novels.json"
    
    novels_data = {
        "version": "1.0",
        "lastUpdated": datetime.now().isoformat(),
        "novels": []
    }
    
    if not os.path.exists(novels_dir):
        print(f"Novels directory '{novels_dir}' not found")
        return
        
    # 扫描novels目录
    for novel_slug in os.listdir(novels_dir):
        novel_path = os.path.join(novels_dir, novel_slug)
        info_file = os.path.join(novel_path, "info.json")
        
        if os.path.isdir(novel_path) and os.path.exists(info_file):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    novel_info = json.load(f)
                    novels_data['novels'].append(novel_info)
            except Exception as e:
                print(f"Error reading {info_file}: {str(e)}")
    
    # 按ID排序
    novels_data['novels'].sort(key=lambda x: x.get('id', 0))
    
    # 保存索引文件
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(novels_data, f, ensure_ascii=False, indent=2)
        
    print(f"Generated index with {len(novels_data['novels'])} novels")

if __name__ == "__main__":
    generate_novels_index()
