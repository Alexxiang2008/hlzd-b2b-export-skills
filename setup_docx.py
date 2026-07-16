"""
一键：复制 + Word COM 转 PDF
"""
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import shutil
import time

# 源目录
src_dir = os.path.expanduser(r'~/Desktop')
# 列出所有文件
print('[*] Desktop files:')
for f in os.listdir(src_dir):
    print(f'    {f}')
