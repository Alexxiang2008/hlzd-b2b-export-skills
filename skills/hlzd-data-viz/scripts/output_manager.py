#!/usr/bin/env python3
"""
HLZD-D3可视化 - 输出管理（HTML 保存 + JSON 历史）
"""

import argparse
import json
import os
import sys
import io
import time
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')


def _ensure_utf8_stdio():
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


SCRIPT_DIR = Path(__file__).parent
SKILL_ROOT = SCRIPT_DIR.parent
OUTPUTS_DIR = SKILL_ROOT / 'outputs'
DASHBOARDS_DIR = OUTPUTS_DIR / 'dashboards'
HISTORY_DIR = OUTPUTS_DIR / 'history'


def ensure_dirs():
    DASHBOARDS_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def get_today():
    return time.strftime('%Y-%m-%d')


def get_now():
    return time.strftime('%Y-%m-%dT%H:%M:%S')


def get_today_history():
    ensure_dirs()
    today = get_today()
    path = HISTORY_DIR / f"{today}.json"
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {'date': today, 'entries': [], 'total_count': 0}


def save_history_entry(meta, output_path=None):
    try:
        ensure_dirs()
        history = get_today_history()
        entry = {
            'timestamp': get_now(),
            'chart_type': meta.get('chart_type', 'unknown'),
            'data_source': meta.get('data_source', 'demo'),
            'language': meta.get('language', 'zh_CN'),
            'output_file': output_path or meta.get('output_file'),
            'cost': 0.0,
            'params': meta.get('params', {})
        }
        history['entries'].append(entry)
        history['total_count'] = len(history['entries'])
        path = HISTORY_DIR / f"{get_today()}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"[历史] 已追加 entry（累计 {history['total_count']} 条）", file=sys.stderr)
        return entry
    except (IOError, OSError) as e:
        raise IOError(f"历史 JSON 写入失败: {e}") from e


def save_html(html_content, suggested_name):
    ensure_dirs()
    target_dir = DASHBOARDS_DIR / get_today()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / suggested_name
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[保存] {target_path}", file=sys.stderr)
    return str(target_path)


def main():
    parser = argparse.ArgumentParser(description='HLZD-D3 输出管理')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_save = sub.add_parser('save', help='保存 HTML + 追加历史')
    p_save.add_argument('--meta', required=True, help='meta JSON')
    p_save.add_argument('--html', required=True, help='HTML 文件路径')
    p_save.add_argument('--name', help='目标文件名')

    p_hist = sub.add_parser('history', help='查看历史')
    p_hist.add_argument('--today', action='store_true')
    p_hist.add_argument('--date', help='指定日期')

    args = parser.parse_args()

    if args.cmd == 'save':
        with open(args.meta, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        html_content = Path(args.html).read_text(encoding='utf-8')
        suggested_name = args.name or Path(args.html).name
        output_path = save_html(html_content, suggested_name)
        entry = save_history_entry(meta, output_path)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
    elif args.cmd == 'history':
        if args.date:
            path = HISTORY_DIR / f"{args.date}.json"
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    print(json.dumps(json.load(f), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(get_today_history(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()