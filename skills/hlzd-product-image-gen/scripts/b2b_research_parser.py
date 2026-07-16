#!/usr/bin/env python3
"""
HLZD-图片生成 - HLZD-B2B工业品调研 报告解析器（闭环调用关键）
用法:
  # 智能检测最新报告 + 解析
  py scripts/b2b_research_parser.py --auto --out b2b_entities.json

  # 解析指定报告
  py scripts/b2b_research_parser.py --report "D:\\AI-P\\skills\\HLZD-B2B工业品调研\\石油套管B2B市场调研报告.md" --out entities.json

  # 仅检测最新报告路径（不解析）
  py scripts/b2b_research_parser.py --detect-latest
依赖: 无第三方库
"""

import argparse
import json
import os
import re
import sys
import io
import time
import warnings

warnings.filterwarnings('ignore')


def _ensure_utf8_stdio():
    """幂等地包装 stdout/stderr 为 UTF-8（避免重复包装导致状态损坏）"""
    if sys.platform != 'win32':
        return
    for _name in ('stdout', 'stderr'):
        _stream = getattr(sys, _name, None)
        if _stream is None or not hasattr(_stream, 'buffer'):
            continue
        _encoding = getattr(_stream, 'encoding', None) or ''
        if 'utf-8' in _encoding.lower():
            continue
        _wrapper = io.TextIOWrapper(_stream.buffer, encoding='utf-8', errors='replace')
        setattr(sys, _name, _wrapper)


_ensure_utf8_stdio()


# ============ 候选目录 ============
DEFAULT_CANDIDATE_DIRS = [
    r'D:\AI-P\skills\HLZD-B2B工业品调研',
    r'C:\Users\13864\.claude\skills\HLZD-B2B工业品调研',
]


# ============ 智能检测 ============
def find_latest_report(working_dir=None):
    """
    按 mtime 找最新 B2B 市场调研报告
    Returns: 报告绝对路径 or None
    """
    candidates = []
    if working_dir:
        candidates = [working_dir]
    else:
        candidates = [d for d in DEFAULT_CANDIDATE_DIRS if os.path.isdir(d)]

    if not candidates:
        print(f"[警告] 未找到候选 B2B 调研目录", file=sys.stderr)
        return None

    reports = []
    for d in candidates:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith('B2B市场调研报告.md'):
                full_path = os.path.join(d, f)
                try:
                    mtime = os.path.getmtime(full_path)
                    reports.append((full_path, mtime))
                except OSError:
                    continue

    if not reports:
        print(f"[警告] 在候选目录中未找到 B2B 市场调研报告", file=sys.stderr)
        return None

    # 按 mtime 倒序，取最新
    latest = max(reports, key=lambda x: x[1])
    return latest[0]


# ============ 解析 markdown ============
def parse_markdown_report(report_path):
    """
    解析 B2B 调研报告 markdown，提取 5 字段
    Returns: dict {product_name, hs_code, product_category, target_markets, scenes, source_report}
    """
    if not os.path.exists(report_path):
        print(f"[错误] 报告不存在: {report_path}", file=sys.stderr)
        sys.exit(1)

    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        'product_name': None,
        'hs_code': None,
        'product_category': None,
        'target_markets': [],
        'scenes': [],
        'source_report': report_path,
        'parsed_at': time.strftime('%Y-%m-%dT%H:%M:%S')
    }

    # 1. 提取产品名（# {产品名} B2B 标题）
    title_match = re.search(r'^# (.+?)\s*B2B', content, re.MULTILINE)
    if title_match:
        result['product_name'] = title_match.group(1).strip()

    # 2. 提取 HS 编码（HS编码：730429 或 HS Code: 730429）
    hs_match = re.search(r'HS\s*(?:编码|Code)[：:]\s*(\d{6})', content)
    if hs_match:
        result['hs_code'] = hs_match.group(1)
    else:
        # 备用正则：匹配 "7304.29" 形式，取前 6 位
        hs_alt = re.search(r'\b(\d{6})\b', content)
        if hs_alt:
            result['hs_code'] = hs_alt.group(1)

    # 3. 推断产品类别（关键词匹配）
    category_map = {
        'machinery': ['套管', '钻探', '阀门', '轴承', '泵', '齿轮', '油管', '法兰', '压缩机', 'OCTG', 'casing', 'valve', 'bearing'],
        'equipment': ['集装箱', '工程机械', '发电机', '产线', '设备', 'house', 'machinery', 'generator', 'equipment'],
        'materials': ['钢', '铝', '混凝土', '塑料', '建材', '管材', '型材', 'steel', 'aluminum', 'material']
    }
    content_lower = content.lower()
    for cat, keywords in category_map.items():
        if any(kw.lower() in content_lower for kw in keywords):
            result['product_category'] = cat
            break

    # 4. 提取目标市场（**加粗**的国名）
    # 匹配 **国名** 或 **国家全称**
    markets_zh = re.findall(r'\*\*([一-龥]{2,8}(?:国|酋长国|王国|联邦|共和国|地区)?)\*\*', content)
    # 去重 + 过滤常见非国家词
    non_country_words = {'一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '百', '千'}
    markets_clean = []
    seen = set()
    for m in markets_zh:
        if m in non_country_words or m in seen:
            continue
        if len(m) < 2:
            continue
        seen.add(m)
        markets_clean.append(m)
    result['target_markets'] = markets_clean[:5]

    # 5. 提取场景关键词
    scene_keywords = ['油田', '工地', '工厂', '车间', '矿山', '港口', '营地', '施工现场', '管道',
                      'oilfield', 'construction', 'factory', 'workshop', 'mining', 'port', 'camp']
    scenes = []
    for kw in scene_keywords:
        if kw in content or kw.lower() in content_lower:
            scenes.append(kw)
    result['scenes'] = scenes

    return result


def extract_entities(report_path=None, working_dir=None):
    """
    一站式入口：智能检测 + 解析
    Returns: entities dict

    Raises:
        FileNotFoundError: 未找到 B2B 调研报告
        ValueError: 报告存在但解析后关键字段全为空（格式漂移）
    """
    if not report_path:
        report_path = find_latest_report(working_dir)
        if not report_path:
            raise FileNotFoundError(
                "未找到 HLZD-B2B工业品调研 报告。请：\n"
                "  A) 先用 HLZD-B2B工业品调研 生成报告\n"
                "  B) 提供报告完整路径（--report 参数）\n"
                "  C) 不使用 B2B 闭环，纯文字生图"
            )

    entities = parse_markdown_report(report_path)

    # 检测报告格式漂移（关键字段全为空）
    if not entities.get('product_name') and not entities.get('hs_code'):
        raise ValueError(
            f"B2B 报告解析失败（关键字段全为空）：{report_path}\n"
            "可能原因：报告格式与预期不符（新段落/标题变化）。\n"
            "请联系 HLZD-B2B工业品调研 维护者更新解析规则。"
        )

    return entities


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='B2B 调研报告解析器')
    parser.add_argument('--auto', action='store_true', help='智能检测最新报告')
    parser.add_argument('--detect-latest', action='store_true', help='仅打印最新报告路径')
    parser.add_argument('--report', help='指定报告路径')
    parser.add_argument('--working-dir', help='自定义 B2B 调研目录')
    parser.add_argument('--out', default='b2b_entities.json', help='输出 entities JSON 路径')
    args = parser.parse_args()

    if args.detect_latest:
        path = find_latest_report(args.working_dir)
        if path:
            print(path)
            sys.exit(0)
        else:
            print("[警告] 未找到 B2B 调研报告", file=sys.stderr)
            sys.exit(1)

    if not args.auto and not args.report:
        print("[错误] 请指定 --auto 或 --report", file=sys.stderr)
        sys.exit(1)

    try:
        entities = extract_entities(report_path=args.report, working_dir=args.working_dir)
    except FileNotFoundError as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"[错误] {e}", file=sys.stderr)
        sys.exit(1)

    if not entities:
        print("[错误] 解析失败，未获取 entities", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)
    except (IOError, OSError) as e:
        print(f"[错误] 无法写入输出文件 {args.out}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[完成] {args.out}")
    print(json.dumps(entities, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()