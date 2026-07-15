#!/usr/bin/env python3
"""
HLZD-B2B工业品调研 - HS编码查询（无头浏览器）
用法: py scripts/hs_lookup.py --keyword "石油套管" [--pages 2]
依赖: pip install playwright && playwright install chromium
"""

import argparse
import json
import sys
import io
import warnings
import time

warnings.filterwarnings('ignore')

# Windows GBK 兼容 — module-level wrap 在 pytest capture 等已关闭 buffer 场景会失败，
# 加 try/except 优雅降级；真正写 main() 时再 wrap 一次更稳。
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (ValueError, AttributeError):
        pass  # buffer 可能已被 pytest 等关闭；不阻断导入


try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: playwright 未安装，运行: pip install playwright && playwright install chromium")
    sys.exit(1)


DEFAULT_TIMEOUT = 15000  # 页面加载超时（毫秒）
MAX_PAGES = 3            # 最多翻页数


def lookup_hs_code(keyword, max_pages=MAX_PAGES, timeout=DEFAULT_TIMEOUT):
    """
    通过hsbianma.com查询HS编码（无头浏览器）

    Args:
        keyword: 中文品名，如 "石油套管"
        max_pages: 最多翻页数（默认3页，每页约20条）
        timeout: 页面加载超时（毫秒）

    Returns:
        list of dict: HS编码列表
    """
    results = []

    with sync_playwright() as p:
        # 启动无头浏览器
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = browser.new_page(viewport={'width': 1280, 'height': 720})

        try:
            # 1. 打开hsbianma.com
            page.goto('https://www.hsbianma.com/', timeout=timeout)
            page.wait_for_load_state('networkidle', timeout=timeout)

            # 2. 填入搜索词并提交
            page.fill('#keywords', keyword)
            page.click('#su')

            # 3. 等待结果表格加载
            page.wait_for_selector('table tr', timeout=timeout)
            page.wait_for_load_state('networkidle', timeout=timeout)

            # 4. 逐页抓取
            page_num = 0
            while page_num < max_pages:
                page_num += 1

                # 提取当前页数据
                rows = page.query_selector_all('table tr')
                for row in rows:
                    cells = row.query_selector_all('td')
                    if len(cells) < 2:
                        continue

                    cell_texts = [c.inner_text().strip() for c in cells]
                    code = cell_texts[0]

                    # 只取数字开头的行（HS编码行）
                    if not code or not any(c.isdigit() for c in code[:4]):
                        continue

                    # 解析字段
                    is_expired = '[过期]' in code
                    code_clean = code.replace('[过期]', '').strip()
                    name = cell_texts[1] if len(cell_texts) > 1 else ''
                    unit = cell_texts[2] if len(cell_texts) > 2 else ''
                    rebate = cell_texts[3] if len(cell_texts) > 3 else ''
                    regulation = cell_texts[4] if len(cell_texts) > 4 else ''

                    results.append({
                        'hs_code': code_clean,
                        'name': name,
                        'unit': unit,
                        'rebate': rebate,
                        'regulation': regulation,
                        'expired': is_expired,
                        'page': page_num
                    })

                # 5. 翻页（找"下一页"按钮）
                if page_num >= max_pages:
                    break

                next_btn = page.query_selector('a:text("下一页")')
                if not next_btn or next_btn.get_attribute('href') == 'javascript:void(0)':
                    break

                next_btn.click()
                page.wait_for_load_state('networkidle', timeout=timeout)
                time.sleep(0.5)  # 短暂等待确保DOM渲染

        except PlaywrightTimeout:
            print(f"[警告] 页面加载超时（{timeout}ms），尝试继续...", file=sys.stderr)
        except Exception as e:
            print(f"[错误] {e}", file=sys.stderr)
        finally:
            browser.close()

    return results


def format_hs_results(results, keyword):
    """格式化输出"""
    if not results:
        return f"未找到 '{keyword}' 相关的HS编码"

    # 去重（按HS编码去重，保留第一条）
    seen = set()
    unique = []
    for r in results:
        key = r['hs_code']
        if key not in seen:
            seen.add(key)
            unique.append(r)

    lines = []
    lines.append(f"HS编码查询结果: {keyword}")
    lines.append(f"数据来源: hsbianma.com（https://www.hsbianma.com/）")
    lines.append(f"共找到 {len(unique)} 个相关HS编码（去重后）")
    lines.append("-" * 80)
    lines.append(f"{'HS编码':<16} {'品名':<25} {'单位':<6} {'退税率':<8} {'监管条件':<10} {'状态':<6}")
    lines.append("-" * 80)

    for r in unique:
        expired_mark = '[过期]' if r['expired'] else ''
        lines.append(
            f"{r['hs_code']:<16} {r['name']:<25} {r['unit']:<6} {r['rebate']:<8} "
            f"{r['regulation']:<10} {expired_mark:<6}"
        )

    lines.append("-" * 80)
    lines.append("提示：UN Comtrade API 使用HS编码前6位（如 7304291000 → 730429）")
    lines.append("      监管条件说明：4=出口许可证，x=两用物项许可证，监管条件为空=无需许可")

    return '\n'.join(lines)


def export_json(results, keyword, output_path):
    """导出JSON"""
    # 去重
    seen = set()
    unique = []
    for r in results:
        key = r['hs_code']
        if key not in seen:
            seen.add(key)
            unique.append(r)

    data = {
        'keyword': keyword,
        'query_url': 'https://www.hsbianma.com/',
        'total_results': len(unique),
        'source': 'hsbianma.com',
        'hs_codes': unique
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON已保存: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='HLZD-B2B工业品调研 - HS编码查询（无头浏览器）'
    )
    parser.add_argument('--keyword', '-k', required=True,
                        help='中文品名，如 "石油套管" "预制建筑"')
    parser.add_argument('--pages', type=int, default=MAX_PAGES,
                        help=f'最多翻页数（默认{MAX_PAGES}）')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT,
                        help=f'页面加载超时（毫秒，默认{DEFAULT_TIMEOUT}）')
    parser.add_argument('--output', '-o',
                        help='JSON输出文件路径（可选）')

    args = parser.parse_args()

    print(f"正在查询: {args.keyword}（最多{args.pages}页）...", file=sys.stderr)

    try:
        results = lookup_hs_code(args.keyword, args.pages, args.timeout)

        # 打印报告
        report = format_hs_results(results, args.keyword)
        print('\n' + report)

        # JSON导出
        if args.output:
            export_json(results, args.keyword, args.output)

    except KeyboardInterrupt:
        print("\n[中断] 用户取消查询", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
