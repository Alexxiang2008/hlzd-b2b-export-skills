#!/usr/bin/env python3
"""
HLZD-视频生成 - B2B 闭环解析器
职责：
  1. 智能检测 HLZD-B2B工业品调研 最新报告
  2. 智能检测 HLZD-图片生成 最新PNG目录
  3. 解析报告 + 提取产品/HS编码/市场/场景
  4. 匹配视频 preset 推荐的默认参数

用法:
  py scripts/b2b_research_parser.py --auto --out entities.json
"""

import argparse
import glob
import json
import os
import re
import sys
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# Windows UTF-8 兼容（Python 3.7+ 默认 UTF-8，无需 wrapper）

# 脚本所在目录（用于动态 import imgbb_uploader）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ============ 候选目录 ============
RESEARCH_SKILL_DIRS = [
    r'D:\AI-P\skills\HLZD-B2B工业品调研',
    r'D:\AI-P\skills',
    r'C:\Users\13864\.claude\skills\HLZD-B2B工业品调研',
]

IMAGE_SKILL_DIRS = [
    r'D:\AI-P\skills\HLZD-图片生成',
    r'D:\AI-P\skills',
    r'C:\Users\13864\.claude\skills\HLZD-图片生成',
]


# ============ B2B 报告解析 ============
def find_latest_report(explicit_path=None):
    """
    智能检测最新 B2B 报告
    Returns: 报告路径 or None
    """
    if explicit_path and os.path.exists(explicit_path):
        return explicit_path

    candidates = []
    for d in RESEARCH_SKILL_DIRS:
        if os.path.exists(d):
            pattern = os.path.join(d, '*B2B*.md')
            candidates.extend(glob.glob(pattern))

    if not candidates:
        return None

    # 按 mtime 倒序
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]


def parse_report(report_path):
    """
    解析 B2B 报告 markdown，提取 5 字段
    Returns: dict {product_name, hs_code, product_category, target_markets, scenes}
    """
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {
        'product_name': None,
        'hs_code': None,
        'product_category': None,
        'target_markets': [],
        'scenes': [],
    }

    # 1. 产品名（标题 # {产品名} B2B）
    title_match = re.search(r'^#\s+(.+?)B2B', content, re.MULTILINE)
    if title_match:
        result['product_name'] = title_match.group(1).strip()

    # 2. HS 编码
    hs_match = re.search(r'HS\s*编码[：:]\s*(\d{6,10})', content)
    if hs_match:
        result['hs_code'] = hs_match.group(1)

    # 3. 产品类别（关键词匹配）
    category_keywords = {
        'machinery': ['阀门', '套管', '轴承', '螺栓', '螺母', '齿轮', '油缸', '紧固件', '工具'],
        'equipment': ['集装箱', '挖掘机', '发电机', '起重机', '装载机', '产线', '叉车'],
        'materials': ['钢结构', '铝合金', '塑料管', '预制构件', '钢管', '钢筋', '玻璃'],
    }
    product_name = result['product_name'] or ''
    for cat, kws in category_keywords.items():
        if any(kw in product_name for kw in kws):
            result['product_category'] = cat
            break

    # 4. 目标市场（市场规模段 **国名**）
    market_section = re.search(r'##.*?市场.*?\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if market_section:
        markets = re.findall(r'\*\*([^*]+)\*\*', market_section.group(1))
        result['target_markets'] = [m.strip() for m in markets if m.strip()]

    # 5. 场景关键词（买家画像段）
    buyer_section = re.search(r'##.*?买家.*?\n(.*?)(?=##|\Z)', content, re.DOTALL)
    if buyer_section:
        scene_keywords = ['油田', '工地', '工厂', '车间', '港口', '码头', '物流', '仓库']
        for kw in scene_keywords:
            if kw in buyer_section.group(1):
                result['scenes'].append(kw)

    return result


# ============ 图片skill 历史解析 ============
def find_latest_images(product_name=None, max_count=4, explicit_dir=None):
    """
    从 HLZD-图片生成 outputs/generated/ 取最新 N 张图
    Returns: list of dict {path, mtime, capability}
    """
    # 候选目录
    candidates = []
    if explicit_dir and os.path.exists(explicit_dir):
        candidates.append(explicit_dir)

    for skill_dir in IMAGE_SKILL_DIRS:
        gen_dir = os.path.join(skill_dir, 'outputs', 'generated')
        if os.path.exists(gen_dir):
            # 取所有日期子目录
            date_dirs = sorted(
                [os.path.join(gen_dir, d) for d in os.listdir(gen_dir)
                 if os.path.isdir(os.path.join(gen_dir, d))],
                key=lambda p: os.path.getmtime(p),
                reverse=True
            )
            candidates.extend(date_dirs)

    if not candidates:
        return []

    # 收集所有 PNG/JPG，按 mtime 倒序
    images = []
    for d in candidates:
        for ext in ('*.png', '*.jpg', '*.jpeg', '*.webp'):
            for p in glob.glob(os.path.join(d, ext)):
                images.append({
                    'path': p,
                    'mtime': os.path.getmtime(p),
                    'filename': os.path.basename(p),
                })

    if not images:
        return []

    # 产品名过滤（如果提供）
    if product_name:
        # 简单匹配：文件名含产品名
        filtered = [img for img in images if product_name in img['filename']]
        if filtered:
            images = filtered

    # 按 mtime 倒序，取最新 max_count 张
    images.sort(key=lambda x: x['mtime'], reverse=True)
    return images[:max_count]


def upload_to_public_url(local_path):
    """
    把本地图片上传到公网可访问的 URL（通过 imgbb 图床）
    Agnes I2V 需要公网 URL，本地路径不支持。

    local_path: 本地图片绝对路径
    Returns: 公网 URL 字符串
    """
    # 动态 import 避免循环依赖
    sys.path.insert(0, SCRIPT_DIR)
    from imgbb_uploader import upload_image

    result = upload_image(local_path)
    return result['url']


def upload_images_to_public_urls(local_paths):
    """
    批量上传图片到公网 URL
    Returns: list of URL（与输入顺序对应）
    """
    sys.path.insert(0, SCRIPT_DIR)
    from imgbb_uploader import upload_images

    results = upload_images(local_paths)
    return [r['url'] for r in results]


# ============ 闭环输出 ============
def auto_detect_all(report_path=None, image_dir=None, max_images=4):
    """
    一站式闭环检测
    Returns: dict {
      source_report, product_name, hs_code, product_category, target_markets, scenes,
      reference_images: [{path, mtime}, ...]
    }
    """
    report_path = find_latest_report(report_path)
    entities = {}

    if report_path:
        parsed = parse_report(report_path)
        entities.update(parsed)
        entities['source_report'] = report_path

    images = find_latest_images(
        product_name=entities.get('product_name'),
        max_count=max_images,
        explicit_dir=image_dir
    )
    entities['reference_images'] = images
    entities['reference_image'] = images[0]['path'] if images else None

    return entities


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='B2B 闭环解析器')
    parser.add_argument('--auto', action='store_true', help='自动检测最新报告+图片')
    parser.add_argument('--report', help='指定 B2B 报告路径')
    parser.add_argument('--image-dir', help='指定图片目录（覆盖自动检测）')
    parser.add_argument('--max-images', type=int, default=4)
    parser.add_argument('--out', default='b2b_entities.json', help='输出 JSON 路径')
    args = parser.parse_args()

    if args.auto or args.report or args.image_dir:
        entities = auto_detect_all(args.report, args.image_dir, args.max_images)
    else:
        print("[错误] 需要 --auto / --report / --image-dir 至少一个", file=sys.stderr)
        sys.exit(1)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)

    print(f"[完成] {args.out}")
    if entities.get('product_name'):
        print(f"  产品: {entities['product_name']}")
    if entities.get('hs_code'):
        print(f"  HS: {entities['hs_code']}")
    if entities.get('product_category'):
        print(f"  类别: {entities['product_category']}")
    if entities.get('target_markets'):
        print(f"  市场: {', '.join(entities['target_markets'])}")
    print(f"  参考图: {len(entities.get('reference_images', []))} 张")


if __name__ == '__main__':
    main()