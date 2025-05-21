
# 用途
# 替换文本中的错别字；去除多余符号；删除空行

import os
import re
import logging
from datetime import datetime

# 配置日志
def setup_logger():
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 设置日志文件名（使用当前时间）
    log_filename = f"logs/lrc_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()

# 替换字典（可扩展）
REPLACEMENTS = {
    "消杀": "消砂",
    "桂山": "癸山",
    "沙": "砂",
    "不藏": "不葬",
    "寻农": "寻龙",
    "外印": "外应",
    "日科": "日课",

}
"""
REPLACEMENTS = {
    "，": "",
    "。": "",
    "？": "",
    "、": "",
    "啊": "",
    "嗯": "",
    "哎": "",
    "血心腹": "雪心赋",
    "血腥腹": "雪心赋",
    "血型腹": "雪心赋",
    "血腥赋": "雪心赋",
    "血心赋": "雪心赋",
    "催关篇": "催官篇",
    "地理五绝": "地理五诀",
    "藏书": "葬书",
    "郭普": "郭璞",
    "根茎": "庚金",
    "祭神": "忌神",
    "人子": "壬子",
    "坤照": "坤造",
    "七煞": "七杀",
    "前兆": "乾造",
    "呢": "",
    "硬性": "印星",
    "物子": "戊子",
    "年杆": "年干",
    "月杆": "月干",
    "日杆": "日干",
    "时杆": "时干",
    "三观": "食伤星",
    "嘛": "",
    "空王": "空亡",
    "七子": "妻子",
    "正硬": "正印",
    "偏硬": "偏印",
    "空网": "空亡",
    "隐幕": "寅木",
    "日食": "日时",
    "浮盈": "伏吟",
    "执服": "值符",
    "硬心": "印星",
    "极土": "己土",
    "害水": "亥水",
    "四火": "巳火",
    "正应": "正印",
    "虚土": "戌土",
    "桂丑": "癸丑",
    "贵水": "癸水",
    "原橘": "原局",
    "原举": "原局",
    "嗜火": "巳火",
    "似火": "巳火",
    "催光片": "催官篇",
    "翠光片": "催官篇",
    "吹光片": "催官篇",
    "杨工": "杨公",
    "赖工": "赖公",
    "增工": "曾公",
    "蒋工": "蒋公",
    "崔冠篇": "催官篇",
    "阳农": "阳龙",
    "亥农": "亥龙",
    "庚农": "庚龙",
    "艮农": "艮龙",
    "蒋工": "蒋公",
    "蒋工": "蒋公",
    "蒋工": "蒋公",
    "蒋工": "蒋公",
    "蒋工": "蒋公",
    "蒋工": "蒋公",
    "卵头": "峦头",
    "龙爵": "龙诀",
    "虚方": "戌方",
    "鸡胸": "吉凶",
    "鸾头": "峦头",
    "恒隆": "横龙",
    "恒隆": "横龙",
    "恒隆": "横龙",
    "恒隆": "横龙",
    "恒隆": "横龙",
    "恒隆": "横龙",
    "恒隆": "横龙",
    "恒隆": "横龙",
}
"""

# 时间戳的正则表达式模式
TIMESTAMP_PATTERN = re.compile(r'^\[\d{2}:\d{2}(.\d{2})?\]$')

def process_lrc_file(file_path, replacement_counts, empty_line_count):
    """
    处理单个LRC文件
    
    参数:
    file_path: LRC文件路径
    replacement_counts: 记录每个替换词被使用的次数
    empty_line_count: 记录删除的空行数

    返回:
    bool: 文件是否被修改
    """
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        processed_lines = []
        
        for line in lines:
            original_line = line.strip()
            
            # 跳过空行
            if not original_line:
                continue
            
            # 提取时间戳和歌词内容
            timestamp_match = re.match(r'^(\[\d{2}:\d{2}(.\d{2})?\])(.*)$', original_line)
            
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                lyrics = timestamp_match.group(3).strip()
                
                # 应用替换规则
                for old_text, new_text in REPLACEMENTS.items():
                    if old_text in lyrics:
                        # 计算替换次数
                        count = lyrics.count(old_text)
                        replacement_counts[old_text] = replacement_counts.get(old_text, 0) + count
                        
                        # 执行替换
                        lyrics = lyrics.replace(old_text, new_text)
                        modified = True
                
                # 如果替换后歌词为空，则跳过这一行（不添加到处理后的列表中）
                if not lyrics:
                    empty_line_count[0] += 1
                    modified = True
                    continue
                
                # 重新组合时间戳和处理后的歌词
                processed_line = f"{timestamp}{lyrics}\n"
                processed_lines.append(processed_line)
            else:
                # 保留不包含时间戳的行（如歌曲信息行）
                processed_lines.append(original_line + '\n')
        
        # 如果文件被修改，则写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(processed_lines)
            return True
        return False
            
    except Exception as e:
        return False

def process_directory(directory_path, logger):
    """处理指定目录下的所有LRC文件（包括子目录）"""
    
    # 统计计数器
    stats = {
        'total_files': 0,
        'modified_files': 0,
        'error_files': 0
    }
    
    # 替换词计数器
    replacement_counts = {}
    
    # 空行计数器 (使用列表以便能在函数间修改)
    empty_line_count = [0]
    
    logger.info(f"开始处理目录: {directory_path}")
    
    # 遍历目录及其子目录
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.lrc'):
                stats['total_files'] += 1
                file_path = os.path.join(root, file)
                
                try:
                    if process_lrc_file(file_path, replacement_counts, empty_line_count):
                        stats['modified_files'] += 1
                except Exception as e:
                    stats['error_files'] += 1
    
    # 输出替换词统计信息
    logger.info("替换词使用统计:")
    for word, count in sorted(replacement_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            logger.info(f"  '{word}' 被替换了 {count} 次")
    
    # 只有在有空行被删除时才输出
    if empty_line_count[0] > 0:
        logger.info(f"共删除 {empty_line_count[0]} 行空歌词行")
    
    # 输出文件处理统计信息
    logger.info(f"处理完成! 总计: {stats['total_files']} 文件, "
                f"修改: {stats['modified_files']} 文件, "
                f"处理出错: {stats['error_files']} 文件")

def main():
    # 设置日志
    logger = setup_logger()
    logger.info("LRC歌词处理程序启动")
    
    # 直接使用当前工作目录
    directory = os.getcwd()
    logger.info(f"将处理当前目录: {directory}")
    
    # 处理目录
    process_directory(directory, logger)
    
    # 处理完成后暂停，让用户查看结果
    input("处理完成，按Enter键退出...")

if __name__ == "__main__":
    main()