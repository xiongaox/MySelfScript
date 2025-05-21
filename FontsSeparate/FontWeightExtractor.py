#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体字重提取器与分离器 - Font Weight Extractor and Separator
支持TTF, TTC, OTF, WOFF和可变字体(VF)

用法：
1、创建虚拟环境并激活
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
2、安装依赖
# 方法1：使用pip安装（系统级安装）
pip install fonttools
# 方法2：使用Homebrew安装（系统级安装）
brew install fonttools
3、运行脚本
python3 FontWeightExtractor.py --extract 需要被转换的字体文件.ttf
4、完成后退出虚拟环境
deactivate


"""

import os
import sys
import argparse
from pathlib import Path
from fontTools import ttLib
from fontTools.ttLib.ttCollection import TTCollection
from fontTools.varLib import instancer
import re
import shutil

# 用于映射数字字重值到字重名称的字典
WEIGHT_NAMES = {
    100: "Thin",
    200: "ExtraLight",
    300: "Light",
    400: "Regular",
    500: "Medium",
    600: "SemiBold", 
    700: "Bold",
    800: "ExtraBold",
    900: "Black"
}

# 常见字重名称的正则表达式模式
WEIGHT_PATTERNS = {
    "thin": 100,
    "extralight|extra light|extra-light|ultralight|ultra light|ultra-light": 200,
    "light": 300,
    "regular|normal|book|roman|text": 400,
    "medium": 500,
    "semibold|semi bold|semi-bold|demibold|demi bold|demi-bold": 600,
    "bold": 700,
    "extrabold|extra bold|extra-bold|ultrabold|ultra bold|ultra-bold": 800,
    "black|heavy": 900
}

def extract_weight_from_name(name):
    """从字体名称中提取字重信息"""
    # 尝试从名称中匹配字重模式
    name_lower = name.lower()
    for pattern, weight in WEIGHT_PATTERNS.items():
        if re.search(r'\b(' + pattern + r')\b', name_lower):
            return weight
    
    # 尝试从名称中直接提取数值字重
    weight_match = re.search(r'\b(\d{3})\b', name)
    if weight_match:
        weight = int(weight_match.group(1))
        if weight in WEIGHT_NAMES:
            return weight

    # 可能是一些特殊缩写
    if re.search(r'\blt\b', name_lower):
        return 300  # Light
    if re.search(r'\bmd\b', name_lower):
        return 500  # Medium
    if re.search(r'\bbd\b', name_lower):
        return 700  # Bold
    if re.search(r'\beb\b', name_lower):
        return 800  # ExtraBold
    if re.search(r'\bbl\b', name_lower):
        return 900  # Black
        
    return None

def get_font_weight(font):
    """从字体对象中获取字重信息"""
    weight = None
    
    # 方法1: 从OS/2表中获取字重值
    if "OS/2" in font:
        os2_table = font["OS/2"]
        weight = os2_table.usWeightClass
    
    # 方法2: 从名称表中提取字重信息
    if "name" in font:
        name_table = font["name"]
        for record in name_table.names:
            # 尝试解码名称记录
            try:
                if record.nameID in (1, 2, 4, 6, 16, 17):  # 常见的包含字体名称的nameID
                    name_str = record.toUnicode()
                    extracted_weight = extract_weight_from_name(name_str)
                    if extracted_weight:
                        # 如果从名称中提取到字重，且未从OS/2表获取字重或者提取的字重与OS/2表中的不同
                        # 则记录这个不一致
                        if weight and weight != extracted_weight:
                            print(f"警告: 名称表字重 ({extracted_weight}/{WEIGHT_NAMES.get(extracted_weight, 'Unknown')}) "
                                  f"与OS/2表字重 ({weight}/{WEIGHT_NAMES.get(weight, 'Unknown')}) 不一致")
                        weight = weight or extracted_weight
            except UnicodeDecodeError:
                continue
    
    return weight

def process_variable_font(font):
    """处理可变字体，提取轴信息"""
    if "fvar" not in font:
        return None
    
    fvar = font["fvar"]
    axes = {}
    for axis in fvar.axes:
        axes[axis.axisTag] = {
            "name": axis.axisNameID,
            "min": axis.minValue,
            "default": axis.defaultValue,
            "max": axis.maxValue
        }
        
        # 如果包含wght轴(字重)，特别处理
        if axis.axisTag == 'wght':
            print(f"可变字体字重轴范围: {axis.minValue} - {axis.maxValue}, 默认值: {axis.defaultValue}")
            
            # 列出具体的实例
            if hasattr(fvar, 'instances') and fvar.instances:
                print("可变字体预定义实例:")
                for instance in fvar.instances:
                    # 获取实例名称
                    instance_name = '未命名实例'
                    if hasattr(instance, 'subfamilyNameID') and instance.subfamilyNameID:
                        try:
                            instance_name = font['name'].getDebugName(instance.subfamilyNameID)
                        except:
                            pass
                    
                    # 获取wght值
                    wght_value = None
                    for coord in instance.coordinates.items():
                        if coord[0] == 'wght':
                            wght_value = coord[1]
                            break
                    
                    if wght_value is not None:
                        weight_name = WEIGHT_NAMES.get(int(wght_value)) if int(wght_value) in WEIGHT_NAMES else f"Custom({wght_value})"
                        print(f"  - {instance_name}: wght={wght_value} ({weight_name})")
    
    return axes

def process_font_file(font_path, args):
    """处理单个字体文件"""
    print(f"\n处理字体文件: {font_path}")
    
    try:
        # 判断是否为TTC字体集合
        if font_path.lower().endswith('.ttc'):
            collection = TTCollection(font_path)
            print(f"TTC字体集合，包含 {len(collection)} 个字体")
            
            for i, font in enumerate(collection.fonts):
                print(f"\n字体 #{i+1} 在集合中:")
                process_single_font(font, font_path, args)
        else:
            # 处理单个字体
            font = ttLib.TTFont(font_path)
            process_single_font(font, font_path, args)
            
    except Exception as e:
        print(f"处理字体时出错: {e}")

def process_single_font(font, font_path, args):
    """处理单个字体对象"""
    try:
        # 获取字体名称
        font_family = "未知"
        font_subfamily = "未知"
        
        if "name" in font:
            name_table = font["name"]
            
            # 获取字体家族名称(nameID=1)
            for record in name_table.names:
                if record.nameID == 1:
                    try:
                        font_family = record.toUnicode()
                        break
                    except UnicodeDecodeError:
                        continue
            
            # 获取字体子族名称(nameID=2)
            for record in name_table.names:
                if record.nameID == 2:
                    try:
                        font_subfamily = record.toUnicode()
                        break
                    except UnicodeDecodeError:
                        continue
        
        print(f"字体名称: {font_family} {font_subfamily}")
        
        # 检查是否为可变字体
        is_variable = "fvar" in font
        if is_variable:
            print("字体类型: 可变字体(VF)")
            axes = process_variable_font(font)
        else:
            print("字体类型: 静态字体")
            
            # 获取字重信息
            weight = get_font_weight(font)
            if weight:
                weight_name = WEIGHT_NAMES.get(weight, "未知")
                print(f"字重: {weight} ({weight_name})")
            else:
                print("字重: 未知")
    
        if args.extract:
            extract_font_weights(font, font_path, args.output)
    
    except Exception as e:
        print(f"处理字体对象时出错: {e}")

def main():
    # 添加parser定义
    parser = argparse.ArgumentParser(description='字体字重提取工具')
    parser.add_argument('paths', nargs='+', help='字体文件或目录路径')
    parser.add_argument('--recursive', '-r', action='store_true', help='递归处理子目录')
    parser.add_argument('--extract', '-e', action='store_true', 
                       help='提取字体字重信息到单独文件')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='指定输出目录路径')
    
    args = parser.parse_args()
    
    supported_extensions = ('.ttf', '.otf', '.ttc', '.woff', '.woff2')
    for path in args.paths:
        path_obj = Path(path)
        
        if path_obj.is_file():
            if path_obj.suffix.lower() in supported_extensions:
                process_font_file(str(path_obj), args)
            else:
                print(f"跳过不支持的文件: {path}")
        
        elif path_obj.is_dir():
            if args.recursive:
                # 递归处理
                for file_path in path_obj.glob('**/*'):
                    if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                        process_font_file(str(file_path), args)
            else:
                # 只处理当前目录
                for file_path in path_obj.glob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                        process_font_file(str(file_path), args)
        
        else:
            print(f"路径不存在: {path}")

def extract_font_weights(font, font_path, output_dir=None):
    """根据字重信息分离字体文件"""
    # 确定输出目录
    if output_dir:
        output_base = Path(output_dir)
    else:
        output_base = Path(font_path).parent / "FontsOutput"
    
    output_base.mkdir(exist_ok=True)
    
    if "fvar" in font:  # 处理可变字体
        fvar = font["fvar"]
        if any(axis.axisTag == "wght" for axis in fvar.axes):
            # 获取字体名称
            font_name = Path(font_path).stem
            
            # 用于跟踪已处理的字重实例，避免重名
            processed_weights = {}
            
            # 提取所有预定义实例
            for instance in fvar.instances:
                # 获取实例名称
                instance_name = '未命名实例'
                if hasattr(instance, 'subfamilyNameID') and instance.subfamilyNameID:
                    try:
                        instance_name = font['name'].getDebugName(instance.subfamilyNameID)
                    except:
                        pass
                
                # 获取wght值
                wght_value = None
                for coord in instance.coordinates.items():
                    if coord[0] == 'wght':
                        wght_value = coord[1]
                        break
                
                if wght_value is not None and instance_name != '未命名实例':
                    # 创建实例化字体
                    instanced_font = instancer.instantiateVariableFont(font, {"wght": wght_value})
                    
                    # 使用实例的原始名称作为文件名后缀
                    file_suffix = instance_name.replace(" ", "")
                    
                    # 确保不会有重名文件
                    if file_suffix in processed_weights:
                        processed_weights[file_suffix] += 1
                        file_suffix = f"{file_suffix}_{processed_weights[file_suffix]}"
                    else:
                        processed_weights[file_suffix] = 1
                    
                    # 保存分离后的字体文件
                    output_path = output_base / f"{font_name}_{file_suffix}.ttf"
                    instanced_font.save(output_path)
                    print(f"已分离实例 {instance_name} 到文件: {output_path}")
    
    else:  # 处理静态字体
        weight = get_font_weight(font)
        if weight:
            # 获取字体名称
            font_name = Path(font_path).stem
            
            # 找到对应的字重名称
            weight_name = WEIGHT_NAMES.get(weight, str(weight))
            
            # 保存分离后的字体文件
            output_path = output_base / f"{font_name}_{weight_name}.ttf"
            shutil.copy2(font_path, output_path)
            print(f"已复制字重 {weight_name} ({weight}) 到文件: {output_path}")

if __name__ == "__main__":
    main()