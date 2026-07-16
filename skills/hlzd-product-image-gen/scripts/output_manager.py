#!/usr/bin/env python3
"""
HLZD-图片生成 - 输出管理（保存图片 + 历史 JSON）
用法:
  py scripts/output_manager.py save --meta meta.json --image-url https://...
  py scripts/output_manager.py save --meta meta.json --local-path /path/to/img.png
  py scripts/output_manager.py history --today
依赖: pip install requests
"""

import argparse
import json
import os
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


# ============ 路径 ============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
# outputs/ 在源仓库根目录下（与 SKILL.md 同级）
OUTPUTS_DIR = os.path.join(SKILL_ROOT, 'outputs')
GENERATED_DIR = os.path.join(OUTPUTS_DIR, 'generated')
HISTORY_DIR = os.path.join(OUTPUTS_DIR, 'history')


def ensure_dirs():
    os.makedirs(GENERATED_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)


def get_today():
    return time.strftime('%Y-%m-%d')


def get_now():
    return time.strftime('%Y-%m-%dT%H:%M:%S')


# ============ 历史 JSON ============
def get_today_history():
    """读取今日历史 JSON（不存在则返回空结构）"""
    ensure_dirs()
    today = get_today()
    path = os.path.join(HISTORY_DIR, f"{today}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        'date': today,
        'entries': [],
        'total_cost': 0.0
    }


def save_history_entry(meta, image_url=None, local_path=None):
    """
    追加一条历史记录

    Raises:
        IOError: JSON 写入失败（磁盘满 / 权限不足 / 路径不可写）
        OSError: 目录创建失败
    """
    try:
        ensure_dirs()
        history = get_today_history()

        entry = {
            'timestamp': get_now(),
            'capability': meta.get('capability', 'unknown'),
            'product_name': meta.get('product_name'),
            'product_category': meta.get('product_category'),
            'model': meta.get('model', 'agnes-image-2.1-flash'),
            'params': meta.get('params', {}),
            'image_url': image_url,
            'local_path': local_path,
            'source_report': meta.get('source_report'),
            'cost': meta.get('cost', 0.0)
        }
        history['entries'].append(entry)
        history['total_cost'] = history.get('total_cost', 0.0) + entry['cost']

        today = get_today()
        path = os.path.join(HISTORY_DIR, f"{today}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        print(f"[历史] 已追加 entry（累计 {len(history['entries'])} 条，总成本 ${history['total_cost']:.3f}）", file=sys.stderr)
        return entry
    except (IOError, OSError) as e:
        # 历史记录失败不应阻塞主流程，但必须明确报错
        raise IOError(
            f"历史 JSON 写入失败（{e}）。\n"
            f"  目录: {HISTORY_DIR}\n"
            f"  请检查磁盘空间和目录权限。"
        ) from e


# ============ 图片保存 ============
def save_image(image_source, suggested_name, subdir=None):
    """
    保存图片到 outputs/generated/YYYY-MM-DD/
    image_source: URL (http/https) 或 base64 data URI 或本地文件路径
    Returns: 本地保存路径
    """
    ensure_dirs()
    today = get_today()
    target_dir = os.path.join(GENERATED_DIR, today)
    if subdir:
        target_dir = os.path.join(target_dir, subdir)
    os.makedirs(target_dir, exist_ok=True)

    save_path = os.path.join(target_dir, suggested_name)

    if image_source.startswith('http://') or image_source.startswith('https://'):
        # URL 下载
        try:
            import requests
        except ImportError:
            print("[错误] requests 未安装", file=sys.stderr)
            sys.exit(1)
        resp = requests.get(image_source, timeout=60)
        resp.raise_for_status()
        img_data = resp.content
    elif image_source.startswith('data:image'):
        # base64 data URI
        import base64
        _, b64_data = image_source.split(',', 1)
        img_data = base64.b64decode(b64_data)
    elif os.path.exists(image_source):
        # 本地文件
        with open(image_source, 'rb') as f:
            img_data = f.read()
    else:
        print(f"[错误] 无法识别 image_source: {image_source[:100]}", file=sys.stderr)
        sys.exit(1)

    with open(save_path, 'wb') as f:
        f.write(img_data)
    print(f"[保存] {save_path} ({len(img_data)} bytes)", file=sys.stderr)
    return save_path


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='输出管理')
    sub = parser.add_subparsers(dest='cmd', required=True)

    # save 子命令
    p_save = sub.add_parser('save', help='保存图片 + 追加历史')
    p_save.add_argument('--meta', required=True, help='meta JSON 路径')
    p_save.add_argument('--image-url', help='图片 URL 或 base64 data URI')
    p_save.add_argument('--local-path', help='图片本地路径（已下载时）')
    p_save.add_argument('--suggested-name', help='建议文件名（如 product_001.png）')

    # history 子命令
    p_hist = sub.add_parser('history', help='查看历史')
    p_hist.add_argument('--today', action='store_true', help='仅今日')
    p_hist.add_argument('--date', help='指定日期 YYYY-MM-DD')

    args = parser.parse_args()

    if args.cmd == 'save':
        with open(args.meta, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        local_path = args.local_path
        image_url = args.image_url

        # 如果没有 local_path 但有 image_url，则下载
        if not local_path and image_url:
            suggested = args.suggested_name or f"{meta.get('product_name', 'image')}_{int(time.time())}.png"
            local_path = save_image(image_url, suggested)

        entry = save_history_entry(meta, image_url=image_url, local_path=local_path)
        print(json.dumps(entry, ensure_ascii=False, indent=2))

    elif args.cmd == 'history':
        if args.date:
            path = os.path.join(HISTORY_DIR, f"{args.date}.json")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    print(json.dumps(json.load(f), ensure_ascii=False, indent=2))
            else:
                print(f"[警告] {args.date} 无历史", file=sys.stderr)
        else:
            # 默认今日
            history = get_today_history()
            print(json.dumps(history, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()