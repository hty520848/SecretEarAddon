import os
import logging

is_release = True   # 是否为发布版本
files_dir = os.path.join(os.path.dirname(__file__))
log_file_path = os.path.join(files_dir, "logfile.txt")   # log文件路径
logger = None
file_handler = None
formatter = None


def get_is_release():
    global is_release
    return is_release


def get_log_file_path():
    global log_file_path
    return log_file_path


def initial_log_file():
    global logger
    global file_handler
    global formatter

    if not os.path.exists(log_file_path):
        # 创建一个文件（如果文件不存在则会被创建）
        with open(log_file_path, 'w') as f:
            f.write('')  # 创建文件

    # 创建一个logger对象
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.INFO)

    # 创建一个文件处理器，将日志信息写入到外部txt文件
    file_handler = logging.FileHandler(log_file_path, mode='a')
    file_handler.setLevel(logging.INFO)

    # 创建一个日志格式器，并将其添加到文件处理器中
    formatter = logging.Formatter('%(asctime)s - %(lineno)d - %(message)s')
    file_handler.setFormatter(formatter)

    # 将文件处理器添加到logger对象中
    logger.addHandler(file_handler)


def write_info(message):
    global logger
    global is_release
    if not is_release:
        logger.info(message)
