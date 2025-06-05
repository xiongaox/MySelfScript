# 用途
# lrc转换srt格式

import re
import sys
import os

def convert_lrc_time_to_srt(lrc_time_str):
    """将LRC时间格式转换为SRT时间格式"""
    match = re.match(r'(\d{1,3}):(\d{2})\.(\d{2})', lrc_time_str)
    if not match:
        raise ValueError(f"无效的时间格式：{lrc_time_str}")
    
    total_minutes, seconds, centiseconds = match.groups()
    total_minutes = int(total_minutes)
    seconds = int(seconds)
    centiseconds = int(centiseconds)
    
    # 将总分钟数转换为小时和分钟
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    # 将厘秒转换为毫秒（厘秒*10）
    milliseconds = centiseconds * 10
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def calculate_duration(current_time, next_time=None, default_duration=3000):
    """计算字幕显示时长（毫秒）"""
    if next_time is None:
        return default_duration
    
    # 解析当前时间
    curr_match = re.match(r'(\d{1,3}):(\d{2})\.(\d{2})', current_time)
    if not curr_match:
        return default_duration
    
    curr_total_min, curr_sec, curr_cs = map(int, curr_match.groups())
    curr_total_ms = (curr_total_min * 60 + curr_sec) * 1000 + curr_cs * 10
    
    # 解析下一时间
    next_match = re.match(r'(\d{1,3}):(\d{2})\.(\d{2})', next_time)
    if not next_match:
        return default_duration
    
    next_total_min, next_sec, next_cs = map(int, next_match.groups())
    next_total_ms = (next_total_min * 60 + next_sec) * 1000 + next_cs * 10
    
    duration = next_total_ms - curr_total_ms
    return max(duration, 500)  # 最少显示500毫秒

def ms_to_srt_time(milliseconds):
    """将毫秒转换为SRT时间格式"""
    hours = milliseconds // 3600000
    minutes = (milliseconds % 3600000) // 60000
    seconds = (milliseconds % 60000) // 1000
    ms = milliseconds % 1000
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

def lrc_to_srt(lrc_path, srt_path):
    """主转换函数"""
    try:
        with open(lrc_path, 'r', encoding='utf-8') as f:
            lrc_content = f.read()
    except FileNotFoundError:
        print(f"错误：输入文件不存在 [{lrc_path}]")
        return False
    except Exception as e:
        print(f"读取文件错误：{lrc_path} - {str(e)}")
        return False

    # 解析LRC行
    lrc_lines = lrc_content.strip().split('\n')
    entries = []
    success_count = 0

    for line_num, line in enumerate(lrc_lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # 匹配LRC格式：[mm:ss.xx]歌词内容
        match = re.match(r'\[(\d{1,3}:\d{2}\.\d{2})\](.+)', line)
        if not match:
            # 跳过不符合格式的行（如标题、艺术家等）
            if not line.startswith('[') or ':' not in line:
                continue
            print(f"警告：跳过无效格式的行 {line_num}：{line}")
            continue

        try:
            time_str, text = match.groups()
            text = text.strip()
            
            if not text:  # 跳过空文本
                continue
                
            # 转换时间格式
            srt_time = convert_lrc_time_to_srt(time_str)
            entries.append((time_str, srt_time, text))
            success_count += 1
            
        except Exception as e:
            print(f"处理第 {line_num} 行失败：{line} - {str(e)}")

    if not entries:
        print(f"警告：没有找到有效的LRC时间戳行")
        return False

    # 生成SRT格式内容
    srt_lines = []
    for i, (lrc_time, srt_start_time, text) in enumerate(entries):
        # 计算结束时间
        next_lrc_time = entries[i + 1][0] if i + 1 < len(entries) else None
        duration = calculate_duration(lrc_time, next_lrc_time)
        
        # 计算开始时间的毫秒数
        time_match = re.match(r'(\d{1,3}):(\d{2})\.(\d{2})', lrc_time)
        if time_match:
            total_min, sec, cs = map(int, time_match.groups())
            start_ms = (total_min * 60 + sec) * 1000 + cs * 10
            end_ms = start_ms + duration
            srt_end_time = ms_to_srt_time(end_ms)
        else:
            srt_end_time = srt_start_time  # 备用方案
        
        # 构建SRT条目
        srt_lines.extend([
            str(i + 1),
            f"{srt_start_time} --> {srt_end_time}",
            text,
            ""  # 空行分隔
        ])

    # 写入SRT文件
    try:
        output_dir = os.path.dirname(srt_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_lines))
        print(f"转换完成：{os.path.basename(lrc_path)} → {os.path.basename(srt_path)} ({success_count} 条)")
        return True
    except IOError as e:
        print(f"错误：无法写入输出文件 [{srt_path}] - {e}")
        return False
    except Exception as e:
        print(f"写入文件时发生未知错误：{srt_path} - {e}")
        return False

def recursive_process_directory(input_dir, output_dir, keep_structure=True):
    """递归处理目录中的所有LRC文件，包括子目录"""
    if not os.path.exists(input_dir):
        print(f"输入目录不存在：{input_dir}")
        return False
    
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"创建输出目录失败：{output_dir} - {e}")
            return False
    
    total_files = 0
    success_count = 0
    
    # 遍历目录及子目录
    for root, dirs, files in os.walk(input_dir):
        lrc_files = [f for f in files if f.lower().endswith('.lrc')]
        if not lrc_files:
            continue
            
        total_files += len(lrc_files)
        
        # 计算相对路径，用于保持目录结构
        rel_path = os.path.relpath(root, input_dir) if keep_structure else ""
        
        for filename in lrc_files:
            input_path = os.path.join(root, filename)
            
            # 确定输出路径，保持原始目录结构
            if keep_structure and rel_path != ".":
                sub_output_dir = os.path.join(output_dir, rel_path)
                if not os.path.exists(sub_output_dir):
                    os.makedirs(sub_output_dir, exist_ok=True)
            else:
                sub_output_dir = output_dir
                
            output_filename = os.path.splitext(filename)[0] + '.srt'
            output_path = os.path.join(sub_output_dir, output_filename)
            
            if lrc_to_srt(input_path, output_path):
                success_count += 1
    
    if total_files == 0:
        print(f"在目录中没有找到LRC文件：{input_dir}")
        return False
        
    print(f"\n目录转换完成！成功转换 {success_count}/{total_files} 个文件")
    return success_count == total_files

if __name__ == "__main__":
    print("== LRC转SRT转换工具 ==")
    print("支持递归处理子目录中的LRC文件")
    
    # 如果没有提供参数，使用当前目录作为输入和输出
    if len(sys.argv) == 1:
        input_dir = os.getcwd()
        output_dir = os.path.join(input_dir, "输出_SRT文件")
        print(f"\n未提供参数，将使用当前目录：{input_dir}")
        print(f"输出文件将保存到：{output_dir}")
        recursive_process_directory(input_dir, output_dir)
        sys.exit(0)
    
    # 处理命令行参数
    if len(sys.argv) not in [2, 3]:
        print("\n用法：")
        print("1. python lrc_to_srt.py")
        print("   - 将处理当前目录及子目录中的所有LRC文件")
        print("   - 输出到当前目录下的'输出_SRT文件'文件夹")
        print("\n2. python lrc_to_srt.py [输入目录]")
        print("   - 将处理指定目录及子目录中的所有LRC文件")
        print("   - 输出到输入目录下的'输出_SRT文件'文件夹")
        print("\n3. python lrc_to_srt.py [输入目录] [输出目录]")
        print("   - 将处理指定目录及子目录中的所有LRC文件")
        print("   - 输出到指定的输出目录，保持原目录结构")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # 确定输出路径
    if len(sys.argv) == 3:
        output_path = sys.argv[2]
    else:
        # 如果只提供一个参数，在输入目录下创建输出目录
        if os.path.isdir(input_path):
            output_path = os.path.join(input_path, "输出_SRT文件")
        else:
            # 如果输入是文件，则在同目录创建SRT文件
            output_path = os.path.splitext(input_path)[0] + '.srt'
    
    try:
        # 处理单个文件
        if os.path.isfile(input_path):
            print(f"\n处理单个文件：{input_path}")
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            success = lrc_to_srt(input_path, output_path)
            sys.exit(0 if success else 1)
        
        # 处理目录
        elif os.path.isdir(input_path):
            print(f"\n递归处理目录：{input_path}")
            print(f"输出目录：{output_path}")
            success = recursive_process_directory(input_path, output_path)
            sys.exit(0 if success else 1)
        
        else:
            print(f"错误：无效的输入路径 {input_path}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"发生未预期的错误：{str(e)}")
        sys.exit(1)