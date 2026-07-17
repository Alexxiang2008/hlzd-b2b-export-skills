#!/usr/bin/env python3
"""
HLZD-视频生成 - 视频 Prompt 构造器
复用图片skill的preset风格，扩展视频动作/场景/镜头预设
用法:
  py scripts/prompt_builder.py --entities entities.json --out prompt.json
依赖: pip install pyyaml
"""

import argparse
import json
import os
import sys
import warnings

warnings.filterwarnings('ignore')

# Windows UTF-8 兼容（Python 3.7+ 默认 UTF-8，无需 wrapper）

try:
    import yaml
except ImportError:
    print("[错误] PyYAML 未安装，运行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
PRESETS_DIR = os.path.join(SKILL_ROOT, 'presets')


# ============ Preset 加载 ============
def load_preset(category, name):
    """加载 preset YAML"""
    path = os.path.join(PRESETS_DIR, category, f"{name}.yaml")
    if not os.path.exists(path):
        print(f"[警告] preset 不存在: {path}", file=sys.stderr)
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_common_preset(preset_type, key):
    """加载通用 preset（motions/scenes）"""
    data = load_preset('common', preset_type)
    if not data:
        return {}
    return data.get(preset_type, {}).get(key, {})


def match_product(product_name, category):
    """在工业品 preset 中匹配产品（与图片skill一致）"""
    preset_data = load_preset('industrial', category)
    if not preset_data:
        return None, None
    products = preset_data.get('products', {})

    product_name_lower = product_name.lower() if product_name else ''

    for key, prod in products.items():
        if prod.get('name_zh') == product_name or prod.get('name_en', '').lower() == product_name_lower:
            return key, prod

    for key, prod in products.items():
        keywords_zh = prod.get('keywords_zh', [])
        keywords_en = prod.get('keywords_en', [])
        for kw in keywords_zh:
            if kw and kw in product_name:
                return key, prod
        for kw in keywords_en:
            if kw and kw.lower() in product_name_lower:
                return key, prod

    if products:
        first_key = next(iter(products))
        return first_key, products[first_key]
    return None, None


# ============ Prompt 构造 ============
def build_video_prompt(entities):
    """
    构造视频 prompt
    entities: {
      product_name, product_category, capability, scene_motion, scene,
      aspect_ratio, duration, target_market, reference_images...
    }

    Returns: {
      prompt, negative_prompt, capability, duration, aspect_ratio, resolution,
      image_url/image_urls (按 capability)
    }
    """
    product_name = entities.get('product_name', '')
    category = entities.get('product_category', 'other')
    scene_motion_key = entities.get('scene_motion', 'orbit')
    scene_text = entities.get('scene', '')
    target_market = entities.get('target_market', '')

    # 1. 加载工业品 preset
    product_data = None
    if category in ('machinery', 'equipment', 'materials'):
        _, product_data = match_product(product_name, category)

    # 2. 加载通用 preset（动作 + 场景）
    motion_mod = load_common_preset('motions', scene_motion_key)
    scene_mod = load_common_preset('scenes', entities.get('scene_preset', 'studio_white'))

    # 3. 拼装 prompt
    prompt_parts = []

    # 产品英文名
    if product_data:
        name_en = product_data.get('name_en', product_name)
        prompt_parts.append(name_en)
    else:
        prompt_parts.append(product_name)

    # 动作描述
    if motion_mod.get('prompt_en'):
        prompt_parts.append(motion_mod['prompt_en'])

    # 场景描述
    scene_desc = scene_text or scene_mod.get('prompt_en', '')
    if scene_desc:
        prompt_parts.append(scene_desc)

    # 目标市场本地化（如有）
    if target_market and scene_mod.get('market_locale', {}).get(target_market):
        prompt_parts.append(scene_mod['market_locale'][target_market])

    full_prompt = ', '.join(filter(None, prompt_parts))

    # 4. negative_prompt
    # 4.1 motion 级 negative
    negative_prompt = motion_mod.get('negative_prompt_en',
                                     'blurry, distorted, low quality, watermark, text overlay')
    # 4.2 产品级 extra_negative（防行业缩写错字、防几何变形等）
    if product_data and product_data.get('extra_negative_en'):
        negative_prompt = negative_prompt + ', ' + product_data['extra_negative_en']
    # 4.3 全局通用 negative（所有产品都加）
    negative_prompt += ', no text overlay, no labels, no watermarks, no logos, no extra letters'

    # 5. 分辨率
    resolution = entities.get('resolution', '720p')
    if category in ('machinery', 'equipment') and resolution == '480p':
        resolution = '720p'  # 工业品最低 720p

    # 6. 决定 I2V 还是 T2V
    capability = entities.get('capability', 'i2v')
    image_url = entities.get('reference_image', '')
    image_urls = entities.get('reference_images', [])

    # 单图 vs 多图自动判断
    if capability == 'i2v' and image_urls and len(image_urls) >= 2:
        capability = 'multi_i2v'

    return {
        'prompt': full_prompt,
        'negative_prompt': negative_prompt,
        'capability': capability,
        'duration': entities.get('duration', 10),
        'aspect_ratio': entities.get('aspect_ratio', '16:9'),
        'resolution': resolution,
        'image_url': image_url,
        'image_urls': image_urls,
        'seed': entities.get('seed'),
    }


def auto_select_preset(entities):
    """根据 entities 推断 preset 路径"""
    category = entities.get('product_category', 'other')
    if category in ('machinery', 'equipment', 'materials'):
        return f'industrial.{category}'
    return None


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='视频 Prompt 构造器')
    parser.add_argument('--entities', required=True, help='entities JSON 文件路径')
    parser.add_argument('--out', default='prompt.json', help='输出 prompt JSON 路径')
    args = parser.parse_args()

    with open(args.entities, 'r', encoding='utf-8') as f:
        entities = json.load(f)

    prompt = build_video_prompt(entities)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(prompt, f, ensure_ascii=False, indent=2)

    print(f"[完成] prompt: {args.out}")
    print(f"  Capability: {prompt['capability']}")
    print(f"  Duration: {prompt['duration']}s")
    print(f"  Aspect: {prompt['aspect_ratio']} @ {prompt['resolution']}")
    print(f"  Prompt: {prompt['prompt']}")


if __name__ == '__main__':
    main()