"""
参照 PPT 成功转换的模板，重做 Word 转 PDF
关键差异：PowerPoint 用 Visible=1 + WithWindow=False
Word 用同样的策略
"""
import os
import time
import sys

# 关键：避免编码传递问题
src = r'D:\MCP_SERVER\HLZD-SALES\work_proof.docx'
dst = r'D:\MCP_SERVER\HLZD-SALES\work_proof.pdf'

# 用 win32com（与成功转 PPT 一样的库）
import win32com.client

# 启动 Word——参考 PPT 成功做法：Visible=1
word = win32com.client.DispatchEx('Word.Application')
word.Visible = 1
word.DisplayAlerts = 0

print(f'[INFO] Opening: {src}')
try:
    doc = word.Documents.Open(src)
    print('[INFO] Converting to PDF...')
    # 17 = wdFormatPDF
    doc.SaveAs(dst, 17)
    doc.Close()
    print('[OK] Saved')
except Exception as e:
    print(f'[FAIL] COM error: {e}')
    import traceback
    traceback.print_exc()
finally:
    word.Quit()
    time.sleep(1)

if os.path.exists(dst):
    print(f'[OK] PDF: {os.path.getsize(dst)/1024:.1f} KB at {dst}')
