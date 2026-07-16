#!/usr/bin/env python3
"""
HLZD-图片生成 - 商品图增强（rembg 本地抠图）
用法:
  py scripts/image_enhancer.py remove-bg --input valve.jpg --output valve_no_bg.png
  py scripts/image_enhancer.py change-bg --input valve.jpg --bg-color "#ffffff" --output valve_white.png
依赖: pip install rembg pillow
"""

import argparse
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


# ============ 依赖检查 ============
try:
    from PIL import Image
except ImportError:
    print("[错误] Pillow 未安装，运行: pip install pillow", file=sys.stderr)
    sys.exit(1)

try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    print("[警告] rembg 未安装，运行: pip install rembg", file=sys.stderr)


# ============ 抠图 ============
def remove_background(input_path, output_path, model_name='u2netp'):
    """
    调用 rembg 抠图
    model_name: u2netp (轻量) / u2net (默认) / isnet-general-use (高质量)

    Raises:
        RuntimeError: rembg 未安装或模型加载失败
        FileNotFoundError: 输入文件不存在
        ValueError: 输入图损坏
    """
    if not REMBG_AVAILABLE:
        raise RuntimeError(
            "rembg 未安装。运行: pip install rembg pillow onnxruntime"
        )

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    # 先用 PIL 验证输入图是否可读
    try:
        with Image.open(input_path) as test_img:
            test_img.verify()  # 验证图片完整性
    except Exception as e:
        raise ValueError(f"输入图损坏或格式不支持: {input_path} ({type(e).__name__}: {e})")

    print(f"[rembg] 加载模型: {model_name}（首次运行需联网下载 ~170MB）", file=sys.stderr)
    try:
        session = new_session(model_name)
    except Exception as e:
        # 模型下载失败（首次运行无网络 / 磁盘满 / 权限不足）
        try:
            print(f"[警告] 模型 {model_name} 加载失败: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"[提示] 尝试默认模型 u2net...", file=sys.stderr)
            session = new_session('u2net')
        except Exception as e2:
            raise RuntimeError(
                f"rembg 模型加载失败。请检查：\n"
                f"  1) 网络连接（首次运行需下载 ~170MB 模型）\n"
                f"  2) 磁盘空间（模型缓存 ~200MB）\n"
                f"  3) 用户目录权限（%USERPROFILE%\\.u2net\\）\n"
                f"原始错误: {type(e2).__name__}: {e2}"
            ) from e2

    print(f"[rembg] 抠图中: {input_path}", file=sys.stderr)
    try:
        with open(input_path, 'rb') as f:
            input_data = f.read()
        output_data = remove(input_data, session=session)
    except Exception as e:
        raise RuntimeError(
            f"rembg 抠图失败: {type(e).__name__}: {e}\n"
            f"  输入: {input_path}\n"
            f"  模型: {model_name}\n"
            f"  建议：换一张更清晰的输入图，或试其他模型"
        ) from e

    try:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(output_data)
    except IOError as e:
        raise IOError(
            f"无法写入输出文件: {output_path} ({e})。\n"
            f"  请检查目录权限和磁盘空间。"
        ) from e

    print(f"[完成] 抠图: {output_path} ({len(output_data)} bytes)", file=sys.stderr)
    return output_path


def change_background(input_path, output_path, bg_color='#ffffff', model_name='u2netp'):
    """
    抠图 + 合成纯色背景
    """
    if not REMBG_AVAILABLE:
        print("[错误] rembg 未安装，无法执行抠图", file=sys.stderr)
        sys.exit(1)

    # Step 1: 抠图到临时文件
    tmp_no_bg = output_path + '.tmp_no_bg.png'
    remove_background(input_path, tmp_no_bg, model_name)

    # Step 2: 合成纯色背景
    fg = Image.open(tmp_no_bg).convert('RGBA')

    # 解析背景色
    bg_color = bg_color.lstrip('#')
    if len(bg_color) == 6:
        bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))
    else:
        print(f"[警告] 颜色格式错误 {bg_color}，使用白色", file=sys.stderr)
        bg_rgb = (255, 255, 255)

    bg = Image.new('RGB', fg.size, bg_rgb)
    bg.paste(fg, mask=fg.split()[3])  # 用 alpha 通道作 mask

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    bg.save(output_path)
    print(f"[完成] 换背景: {output_path} (背景色 #{bg_color})", file=sys.stderr)

    # 清理临时文件
    try:
        os.remove(tmp_no_bg)
    except OSError:
        pass

    return output_path


# ============ CLI ============
def main():
    parser = argparse.ArgumentParser(description='商品图增强（rembg 抠图）')
    sub = parser.add_subparsers(dest='cmd', required=True)

    # remove-bg 子命令
    p1 = sub.add_parser('remove-bg', help='抠图（输出透明 PNG）')
    p1.add_argument('--input', required=True, help='输入图片路径')
    p1.add_argument('--output', required=True, help='输出图片路径')
    p1.add_argument('--model', default='u2netp', choices=['u2netp', 'u2net', 'isnet-general-use'],
                    help='rembg 模型（默认 u2netp 轻量）')

    # change-bg 子命令
    p2 = sub.add_parser('change-bg', help='抠图 + 合成纯色背景')
    p2.add_argument('--input', required=True, help='输入图片路径')
    p2.add_argument('--output', required=True, help='输出图片路径')
    p2.add_argument('--bg-color', default='#ffffff', help='背景色（hex 格式，默认白色）')
    p2.add_argument('--model', default='u2netp', choices=['u2netp', 'u2net', 'isnet-general-use'],
                    help='rembg 模型')

    args = parser.parse_args()

    if args.cmd == 'remove-bg':
        remove_background(args.input, args.output, args.model)
    elif args.cmd == 'change-bg':
        change_background(args.input, args.output, args.bg_color, args.model)


if __name__ == '__main__':
    main()