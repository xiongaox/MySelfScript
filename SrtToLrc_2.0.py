
# 用途
# srt转换lrc格式

import re
import sys
import os

def convert_srt_time_to_lrc(srt_time_str):
    """将SRT时间格式转换为LRC时间格式"""
    match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', srt_time_str)
    if not match:
        raise ValueError(f"无效的时间格式：{srt_time_str}")
    
    hours, minutes, seconds, milliseconds = match.groups()
    total_minutes = int(hours) * 60 + int(minutes)
    ms_two_digits = milliseconds[:2]  # 直接取毫秒前两位
    
    return f"{total_minutes:02d}:{int(seconds):02d}.{ms_two_digits}"

def srt_to_lrc(srt_path, lrc_path):
    """主转换函数"""
    try:
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
    except FileNotFoundError:
        print(f"错误：输入文件不存在 [{srt_path}]")
        return False
    except Exception as e:
        print(f"读取文件错误：{srt_path} - {str(e)}")
        return False

    entries = srt_content.strip().split('\n\n')
    lrc_lines = []
    success_count = 0

    for entry in entries:
        entry_lines = entry.strip().split('\n')
        if len(entry_lines) < 3:
            print(f"警告：跳过无效条目（行数不足）")
            continue

        try:
            # 解析时间行
            time_line = entry_lines[1]
            start_time_str = time_line.split(' --> ')[0].strip()
            
            # 转换时间格式
            lrc_time = convert_srt_time_to_lrc(start_time_str)
            
            # 处理文本内容
            text = ' '.join(line.strip() for line in entry_lines[2:])
            lrc_lines.append(f"[{lrc_time}]{text}")
            
            success_count += 1
            
        except Exception as e:
            print(f"处理条目失败：{entry_lines[0] if entry_lines else '未知'} - {str(e)}")

    # 写入LRC文件
    try:
        output_dir = os.path.dirname(lrc_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lrc_lines))
        print(f"转换完成：{os.path.basename(srt_path)} → {os.path.basename(lrc_path)} ({success_count}/{len(entries)} 条)")
        return True
    except IOError as e:
        print(f"错误：无法写入输出文件 [{lrc_path}] - {e}")
        return False
    except Exception as e:
        print(f"写入文件时发生未知错误：{lrc_path} - {e}")
        return False

def recursive_process_directory(input_dir, output_dir, keep_structure=True):
    """递归处理目录中的所有SRT文件，包括子目录"""
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
        srt_files = [f for f in files if f.lower().endswith('.srt')]
        if not srt_files:
            continue
            
        total_files += len(srt_files)
        
        # 计算相对路径，用于保持目录结构
        rel_path = os.path.relpath(root, input_dir) if keep_structure else ""
        
        for filename in srt_files:
            input_path = os.path.join(root, filename)
            
            # 确定输出路径，保持原始目录结构
            if keep_structure and rel_path != ".":
                sub_output_dir = os.path.join(output_dir, rel_path)
                if not os.path.exists(sub_output_dir):
                    os.makedirs(sub_output_dir, exist_ok=True)
            else:
                sub_output_dir = output_dir
                
            output_filename = os.path.splitext(filename)[0] + '.lrc'
            output_path = os.path.join(sub_output_dir, output_filename)
            
            if srt_to_lrc(input_path, output_path):
                success_count += 1
    
    if total_files == 0:
        print(f"在目录中没有找到SRT文件：{input_dir}")
        return False
        
    print(f"\n目录转换完成！成功转换 {success_count}/{total_files} 个文件")
    return success_count == total_files

if __name__ == "__main__":
    print("== SRT转LRC转换工具 ==")
    print("支持递归处理子目录中的SRT文件")
    
    # 如果没有提供参数，使用当前目录作为输入和输出
    if len(sys.argv) == 1:
        input_dir = os.getcwd()
        output_dir = os.path.join(input_dir, "输出_LRC文件")
        print(f"\n未提供参数，将使用当前目录：{input_dir}")
        print(f"输出文件将保存到：{output_dir}")
        recursive_process_directory(input_dir, output_dir)
        sys.exit(0)
    
    # 处理命令行参数
    if len(sys.argv) not in [2, 3]:
        print("\n用法：")
        print("1. python srt_to_lrc.py")
        print("   - 将处理当前目录及子目录中的所有SRT文件")
        print("   - 输出到当前目录下的'输出_LRC文件'文件夹")
        print("\n2. python srt_to_lrc.py [输入目录]")
        print("   - 将处理指定目录及子目录中的所有SRT文件")
        print("   - 输出到输入目录下的'输出_LRC文件'文件夹")
        print("\n3. python srt_to_lrc.py [输入目录] [输出目录]")
        print("   - 将处理指定目录及子目录中的所有SRT文件")
        print("   - 输出到指定的输出目录，保持原目录结构")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # 确定输出路径
    if len(sys.argv) == 3:
        output_path = sys.argv[2]
    else:
        # 如果只提供一个参数，在输入目录下创建输出目录
        if os.path.isdir(input_path):
            output_path = os.path.join(input_path, "输出_LRC文件")
        else:
            # 如果输入是文件，则在同目录创建LRC文件
            output_path = os.path.splitext(input_path)[0] + '.lrc'
    
    try:
        # 处理单个文件
        if os.path.isfile(input_path):
            print(f"\n处理单个文件：{input_path}")
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            success = srt_to_lrc(input_path, output_path)
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