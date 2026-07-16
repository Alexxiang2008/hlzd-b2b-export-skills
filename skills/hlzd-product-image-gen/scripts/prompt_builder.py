#!/usr/bin/env python3
"""
HLZD-图片生成 - Prompt 构造器（preset 拼装核心）
用法:
  py scripts/prompt_builder.py --entities entities.json --preset industrial.machinery --out prompt.json
  py scripts/prompt_builder.py --entities entities.json --out prompt.json   # 自动选 preset
依赖: pip install pyyaml
"""

import argparse
import json
import os
import sys
import io
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

try:
    import yaml
except ImportError:
    print("[错误] PyYAML 未安装，运行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ============ 路径 ============
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SCRIPT_DIR)
PRESETS_DIR = os.path.join(SKILL_ROOT, 'presets')


# ============ Preset 加载 ============
def load_preset(category, name=None):
    """
    加载 preset YAML
    category: 'industrial' 或 'common'
    name: 文件名（不含扩展名），如 'machinery' 或 'angles'
    """
    if name is None:
        name = category

    path = os.path.join(PRESETS_DIR, category, f"{name}.yaml")
    if not os.path.exists(path):
        print(f"[错误] preset 不存在: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data


def load_common_preset(preset_type, key):
    """
    加载通用 preset（angles/lighting/styles）
    preset_type: 'angles' / 'lighting' / 'styles'
    key: 选项 key
    Returns: dict {prompt_en, negative_prompt_en?}
    """
    data = load_preset('common', preset_type)
    return data.get(preset_type, {}).get(key, {})


# ============ 产品匹配 ============
def match_product(product_name, category):
    """
    在工业品 preset 中匹配产品
    Returns: (product_key, product_data) or (None, None)
    """
    preset_data = load_preset('industrial', category)
    products = preset_data.get('products', {})

    product_name_lower = product_name.lower() if product_name else ''

    # 1. 精确匹配 name_zh / name_en
    for key, prod in products.items():
        if prod.get('name_zh') == product_name or prod.get('name_en', '').lower() == product_name_lower:
            return key, prod

    # 2. 关键词匹配
    for key, prod in products.items():
        keywords_zh = prod.get('keywords_zh', [])
        keywords_en = prod.get('keywords_en', [])
        for kw in keywords_zh:
            if kw and kw in product_name:
                return key, prod
        for kw in keywords_en:
            if kw and kw.lower() in product_name_lower:
                return key, prod

    # 3. 第一个产品作为默认
    if products:
        first_key = next(iter(products))
        return first_key, products[first_key]

    return None, None


# ============ Expert Prompt 拼装 ============
def build_expert_prompt_part(product_name, expert_answers):
    """
    根据专业访谈答案生成精准的产品描述片段
    expert_answers: dict (钢级/外径/扣型/端部/长度/...)

    Returns: str (英文产品描述片段)，如果无 expert_answers 返回空字符串
    """
    ea = expert_answers or {}
    parts = []

    # 套管（OCTG）专业模板
    if ea.get('steel_grade') or ea.get('od') or ea.get('connection'):
        parts.append("OCTG oil casing pipe")
        if ea.get('od'):
            parts.append(f"OD {ea['od']}")
        if ea.get('steel_grade'):
            parts.append(f"steel grade {ea['steel_grade']}")
        if ea.get('connection'):
            parts.append(f"{ea['connection']} connection")
        if ea.get('length'):
            parts.append(f"length {ea['length']}")

        # 端部特征（视觉关键）
        end_finish = str(ea.get('end_finish', ''))
        if 'green' in end_finish.lower() or 'protect' in end_finish.lower() or '保护套' in end_finish:
            parts.append("with green plastic thread protectors on both ends")
        elif 'bare' in end_finish.lower() or '裸' in end_finish:
            parts.append("bare end, no thread protector, exposed threads")
        elif 'yellow' in end_finish.lower() or '黄漆' in end_finish:
            parts.append("with yellow paint on ends")

        return ", ".join(parts)

    # 阀门专业模板
    if ea.get('valve_type') or ea.get('pressure_class'):
        valve_type = ea.get('valve_type', 'industrial')
        # 避免 "ball valve valve" 重复词
        parts.append(valve_type if 'valve' in valve_type.lower() else f"{valve_type} valve")
        if ea.get('pressure_class'):
            parts.append(f"pressure class {ea['pressure_class']}")
        if ea.get('connection_type'):
            parts.append(f"{ea['connection_type']} connection")
        if ea.get('body_material'):
            parts.append(f"body material {ea['body_material']}")
        if ea.get('operation'):
            parts.append(f"{ea['operation']} operated")
        return ", ".join(parts)

    # 钢结构专业模板
    if ea.get('application') or ea.get('main_member'):
        parts.append("steel structure")
        if ea.get('application'):
            parts.append(f"for {ea['application']}")
        if ea.get('main_member'):
            parts.append(f"main member {ea['main_member']}")
        if ea.get('surface_treatment'):
            parts.append(f"surface treatment {ea['surface_treatment']}")
        return ", ".join(parts)

    # 默认：无 expert_answers 时返回空字符串（使用通用 preset）
    return ""


def ea_has_casing(expert_answers):
    """判断 expert_answers 是否包含套管相关字段"""
    if not expert_answers:
        return False
    casing_keys = ['steel_grade', 'od', 'connection', 'end_finish', 'length']
    return any(k in expert_answers for k in casing_keys)


def ea_has_valve(expert_answers):
    """判断 expert_answers 是否包含阀门相关字段"""
    if not expert_answers:
        return False
    valve_keys = ['valve_type', 'pressure_class', 'connection_type', 'body_material', 'operation']
    return any(k in expert_answers for k in valve_keys)


def suggest_default_scene(expert_answers, category):
    """
    根据 expert_answers 和 category 智能推荐默认场景
    Returns: str 场景描述
    """
    if ea_has_casing(expert_answers):
        return "stacked in pipe storage yard, factory setting, industrial environment"
    if ea_has_valve(expert_answers):
        return "on display at industrial trade show booth, exhibition lighting"
    if category == 'equipment':
        return "in industrial facility, professional environment"
    if category == 'materials':
        return "in warehouse, stacked materials, industrial setting"
    return "white background product shot"


# ============ Prompt 构造 ============
def build_prompt(entities):
    """
    构造最终 prompt
    entities: dict，含 product_name / product_category / scene / angle / lighting / style / size / quantity / expert_answers

    Returns: dict {prompt, negative_prompt, model, size, quantity, expert_used}
    """
    product_name = entities.get('product_name', '')
    category = entities.get('product_category', 'other')
    expert_answers = entities.get('expert_answers', {})

    # 1. 加载工业品 preset（如果 category 匹配）
    preset_data = None
    product_data = None
    if category in ('machinery', 'equipment', 'materials'):
        preset_data = load_preset('industrial', category)
        _, product_data = match_product(product_name, category)

    # 2. 拼装 prompt 主体
    prompt_parts = []

    # 2.1 如果有 expert_answers，用专业模板生成精准描述
    expert_part = build_expert_prompt_part(product_name, expert_answers)
    if expert_part:
        prompt_parts.append(expert_part)
    else:
        # 否则用 preset 默认英文名
        if product_data:
            name_en = product_data.get('name_en', product_name)
            prompt_parts.append(name_en)
        else:
            prompt_parts.append(product_name)

    # 3. 通用 preset 拼装（angle / lighting / style）
    angle_key = entities.get('angle', '45deg')
    angle_mod = load_common_preset('angles', angle_key)
    if angle_mod.get('prompt_en'):
        prompt_parts.append(angle_mod['prompt_en'])

    lighting_key = entities.get('lighting', 'studio')
    lighting_mod = load_common_preset('lighting', lighting_key)
    if lighting_mod.get('prompt_en'):
        prompt_parts.append(lighting_mod['prompt_en'])

    style_key = entities.get('style', 'catalog')
    style_mod = load_common_preset('styles', style_key)
    if style_mod.get('prompt_en'):
        prompt_parts.append(style_mod['prompt_en'])

    # 4. 场景（套管/阀门/设备/建材各有推荐默认）
    scene = entities.get('scene', '')
    if not scene:
        scene = suggest_default_scene(expert_answers, category)
    if scene:
        prompt_parts.append(scene)

    # 5. 负面 prompt
    negative_prompt = style_mod.get('negative_prompt_en', 'blurry, distorted, low quality')
    # 套管场景加强负面 prompt
    if ea_has_casing(expert_answers):
        negative_prompt = ', '.join(filter(None, [
            negative_prompt,
            'wrong proportions, unrealistic dimensions',
            'wrong steel grade color',
            'missing thread protector'
        ]))

    # 6. 拼装完整 prompt
    full_prompt = ', '.join(filter(None, prompt_parts))

    return {
        'prompt': full_prompt,
        'negative_prompt': negative_prompt,
        'model': 'agnes-image-2.1-flash',
        'size': entities.get('size', '1024x1024'),
        'quantity': entities.get('quantity', 1),
        'expert_used': bool(expert_part)
    }


def auto_select_preset(entities):
    """根据 entities 自动选择 preset"""
    category = entities.get('product_category', 'other')
    if category in ('machinery', 'equipment', 'materials'):
        return f'industrial.{category}'
    return None


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='Prompt 构造器')
    parser.add_argument('--entities', required=True, help='entities JSON 文件路径')
    parser.add_argument('--preset', help='preset 路径（格式：category.name，可省略自动推断）')
    parser.add_argument('--out', default='prompt.json', help='输出 prompt JSON 路径')
    args = parser.parse_args()

    with open(args.entities, 'r', encoding='utf-8') as f:
        entities = json.load(f)

    prompt = build_prompt(entities)

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(prompt, f, ensure_ascii=False, indent=2)

    print(f"[完成] prompt: {args.out}")
    print(f"  Prompt: {prompt['prompt']}")
    print(f"  Size: {prompt['size']}")
    print(f"  Model: {prompt['model']}")
    print(f"  Expert used: {prompt.get('expert_used', False)}")


if __name__ == '__main__':
    main()