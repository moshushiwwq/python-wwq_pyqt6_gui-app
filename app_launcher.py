#!/usr/bin/env python
"""
应用程序启动器
用于启动以下应用程序：
1. 2048游戏
2. 贪吃蛇游戏
3. 小恐龙游戏
4. 俄罗斯方块游戏
5. 小说下载器

该启动器将多个应用程序集成到一个界面中，通过按钮选择启动不同的应用。
"""
import sys
import os
import random
import time
import math
import pickle
import re
import json
import threading
import webbrowser
import logging
import uuid
import subprocess
import shutil
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QGridLayout, QProgressBar, QTextEdit,
    QFileDialog, QLineEdit, QDialog, QGroupBox,
    QFormLayout, QSpinBox, QSizePolicy, QFrame, QComboBox,
    QToolButton, QSystemTrayIcon, QStyle, QMenu, QScrollArea,
    QTreeView, QCheckBox, QTableView, QHeaderView, QAbstractItemView, QButtonGroup, QRadioButton,
    QListWidget
)
# 在PyQt6中，QStandardItem和QStandardItemModel位于QtGui模块
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtGui import QAction, QTextCursor
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor , QIcon , QPixmap, QGuiApplication, QRadialGradient, QPalette, QTextDocument
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QThread, QObject, pyqtSignal, pyqtSlot, QSettings, QRectF, QPointF

# ===== 设置日志配置 =====
import os
import sys
import logging
import pickle

# ===== 加密工具和加密日志处理器 =====
import base64
import os
import logging.handlers  # 提前导入logging.handlers模块
import fnmatch
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

class CryptoUtils:
    """
    加密工具类
    提供AES加密和解密功能，用于保护日志和配置文件
    """
    def __init__(self, key=None):
        """
        初始化加密工具
        
        Args:
            key: 加密密钥，如果不提供则使用默认密钥
        """
        # 如果未提供密钥，使用默认密钥
        if key is None:
            # 使用应用程序特定的默认密钥（实际应用中应考虑更安全的密钥管理方式）
            key = "PythonBoxAppSecretKey!"  # 实际应用中应使用更安全的密钥生成方式
        
        # 确保密钥长度为16、24或32字节（AES要求）
        if len(key) < 16:
            key = key.ljust(16, '\0')
        elif len(key) < 24:
            key = key.ljust(24, '\0')
        else:
            key = key[:32]  # 截取前32字节
        
        self.key = key.encode('utf-8')
        self.backend = default_backend()
        
    def encrypt(self, data):
        """
        加密数据
        
        Args:
            data: 要加密的数据（字符串）
        
        Returns:
            加密后的base64编码字符串
        """
        # 转换数据为字节
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # 生成随机IV
        iv = os.urandom(16)
        
        # 创建填充器
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # 创建加密器和解密器
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # 组合IV和密文并进行base64编码
        result = base64.b64encode(iv + ciphertext)
        return result.decode('utf-8')
        
    def decrypt(self, encrypted_data):
        """
        解密数据
        
        Args:
            encrypted_data: 加密后的base64编码字符串
        
        Returns:
            解密后的原始字符串
        """
        # 解码base64
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        
        # 提取IV和密文
        iv = encrypted_bytes[:16]
        ciphertext = encrypted_bytes[16:]
        
        # 创建加密器和解密器
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # 去除填充
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        # 转换为字符串
        return data.decode('utf-8')

# 创建全局加密工具实例
crypto_utils = CryptoUtils()

class EncryptedLogHandler(logging.FileHandler):
    """
    加密日志处理器
    继承自FileHandler，在写入日志时自动加密
    """
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        """
        初始化加密日志处理器
        
        Args:
            filename: 日志文件路径
            mode: 文件打开模式
            encoding: 文件编码
            delay: 是否延迟创建文件
        """
        # 调用父类初始化
        super().__init__(filename, mode, encoding, delay)
        
    def emit(self, record):
        """
        重写emit方法，在写入前加密日志记录
        
        Args:
            record: 日志记录对象
        """
        try:
            # 格式化日志记录
            msg = self.format(record)
            
            # 加密日志消息
            encrypted_msg = crypto_utils.encrypt(msg)
            
            # 将加密后的消息写入文件，确保使用b模式
            self.stream.write(encrypted_msg + '\n')
            self.flush()
        except Exception:
            self.handleError(record)

class EncryptedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    加密的轮转日志处理器
    支持日志文件大小轮转，并在写入时自动加密
    """
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, delay=False):
        """
        初始化加密的轮转日志处理器
        
        Args:
            filename: 日志文件路径
            maxBytes: 单个日志文件最大字节数
            backupCount: 保留的备份文件数量
            encoding: 文件编码
            delay: 是否延迟创建文件
        """
        # 确保导入RotatingFileHandler
        import logging.handlers
        # 调用父类初始化
        super().__init__(filename, maxBytes, backupCount, encoding, delay)
    
    def emit(self, record):
        """
        重写emit方法，在写入前加密日志记录
        
        Args:
            record: 日志记录对象
        """
        try:
            # 格式化日志记录
            msg = self.format(record)
            
            # 加密日志消息
            encrypted_msg = crypto_utils.encrypt(msg)
            
            # 将加密后的消息写入文件
            self.stream.write(encrypted_msg + '\n')
            self.flush()
        except Exception:
            self.handleError(record)

# 添加一个用于解密读取日志文件的函数
def read_encrypted_logs(log_file_path):
    """
    读取并解密日志文件
    
    Args:
        log_file_path: 日志文件路径
    
    Returns:
        解密后的日志内容字符串
    """
    if not os.path.exists(log_file_path):
        return "日志文件不存在"
    
    try:
        decrypted_logs = []
        # 尝试使用不同的编码方式读取日志文件
        encodings = ['utf-8', 'gbk', 'latin-1']
        for encoding in encodings:
            try:
                with open(log_file_path, 'r', encoding=encoding) as f:
                    encrypted_lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        
        # 解密每一行日志
        for line in encrypted_lines:
            line = line.strip()
            if line:
                try:
                    decrypted_line = crypto_utils.decrypt(line)
                    decrypted_logs.append(decrypted_line)
                except Exception:
                    # 如果解密失败，保留原始内容
                    decrypted_logs.append(f"[解密失败] {line}")
        
        return '\n'.join(decrypted_logs)
    except Exception as e:
        return f"读取日志文件失败: {str(e)}"

# 获取配置文件保存目录
def get_config_dir():
    """获取配置文件保存目录，exe所在文件夹的infor子目录"""
    # 获取程序运行目录（exe所在目录）
    if getattr(sys, 'frozen', False):
        # 打包后的exe运行模式
        app_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        # 开发模式
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 创建infor文件夹
    config_dir = os.path.join(app_dir, 'infor')
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
        except Exception as e:
            # 如果创建失败，使用临时目录
            config_dir = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', r'C:\Temp')), 'app_infor')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
    
    return config_dir

# 初始化配置目录
CONFIG_DIR = get_config_dir()

# 配置文件路径
APP_LOG_FILE = os.path.join(CONFIG_DIR, 'app_log')  # 不使用.txt后缀
APP_SETTINGS_FILE = os.path.join(CONFIG_DIR, 'app_settings.pkl')
GAME2048_HIGH_SCORE_FILE = os.path.join(CONFIG_DIR, '2048_high_score')  # 不使用.txt后缀
SNAKE_HIGH_SCORE_FILE = os.path.join(CONFIG_DIR, 'snake_high_score.pickle')
DINO_GAME_SCORES_FILE = os.path.join(CONFIG_DIR, 'dino_game_scores.pkl')
TETRIS_HIGH_SCORE_FILE = os.path.join(CONFIG_DIR, 'tetris_high_score.pkl')

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False  # 阻止日志消息传播到父日志记录器

# 清除已有的处理器
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 添加加密文件处理器和控制台处理器
file_handler = EncryptedLogHandler(APP_LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# ===== 版本历史信息 =====
VERSION_HISTORY = [
    {
        "version": "1.1.0",
        "date": "2025-10-06",
        "features": [
            "统一在所有窗口标题中添加设计标识",
            "添加应用程序打包功能",
            "修复PyQt相关导入错误",
            "优化线程销毁逻辑",
            "添加所有应用程序卡片：2048游戏、贪吃蛇游戏、小恐龙游戏、俄罗斯方块、小说下载器、视频下载器、音频格式转换工具、应用程序打包工具"
        ]
    },
    {
        "version": "1.0.0",
        "date": "2025-09-25",
        "features": [
            "优化俄罗斯方块游戏性能",
            "移除俄罗斯方块游戏音效功能",
            "优化游戏界面响应速度",
            "修复若干已知bug"
        ]
    },
    {
        "version": "0.95",
        "date": "2025-05-15",
        "features": [
            "添加小恐龙游戏",
            "添加俄罗斯方块游戏",
            "优化应用程序启动速度",
            "修复小说下载器的若干bug"
        ]
    },
    {
        "version": "0.90",
        "date": "2025-01-05",
        "features": [
            "添加小说下载器功能",
            "改进2048游戏界面",
            "优化贪吃蛇游戏控制"
        ]
    },
    {
        "version": "0.85",
        "date": "2025-01-01",
        "features": [
            "添加2048游戏",
            "添加贪吃蛇游戏",
            "基础框架搭建"
        ]
    }
]

# ===== 应用程序启动器主窗口类 =====
class AppLauncher(QMainWindow):
    """
    应用程序启动器主窗口类
    提供界面让用户选择要运行的应用程序，采用卡片式布局
    """
    def __init__(self):
        super().__init__()
        # 设置中文字体支持
        self.font = QFont()
        self.font.setFamily("SimHei")
        
        # 存储子窗口的引用，用于管理
        self.child_windows = []
        
        # 状态栏显示控制
        self.status_bar_visible = True
        
        # 系统托盘图标
        self.tray_icon = None
        
        # 初始化UI
        self.init_ui()
        
        # 创建进度条相关属性
        self.progress_window = None
        self.progress_value = 0
        
        # 初始化设置和日志功能
        self.settings = self.load_settings()
        self.log_history = []
        self.log_file_path = APP_LOG_FILE
        
        # 窗口居中显示
        self.center_window()
        
    def init_ui(self):
        """初始化用户界面，采用卡片式布局设计风格"""
        # 设置窗口标题和尺寸
        self.setWindowTitle('Python Box_Designed_by_wwq')
        self.setGeometry(100, 100, 800, 700)  # 增加主窗口高度
        self.setMinimumSize(700, 600)  # 增加最小窗口高度
        
        # 设置全局样式 - 采用卡片式设计（移除PyQt不支持的CSS属性）
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #f5f5f7; 
            }
            QLabel#categoryLabel {
                color: #333333;
                font-weight: bold;
                font-size: 18px;
                margin: 15px 0 10px 10px;
            }
            QFrame#cardFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;  /* 添加1像素浅灰色边框 */
            }
            QFrame#cardFrame:hover {
                background-color: #f8f9fa;
            }
            QPushButton#cardButton {
                background-color: transparent;
                color: #2d3436;
                font-size: 16px;
                font-weight: 500;
                border: none;
                text-align: left;
                padding: 20px;
                border-radius: 12px;
            }
            QPushButton#cardButton:hover {
                background-color: rgba(0, 0, 0, 0.02);
            }
        """)
        
        # 创建主窗口部件
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #f5f5f7;")
        self.setCentralWidget(central_widget)
        
        # 创建主垂直布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 10, 40, 40)  # 减小顶部边距，保留其他边距
        main_layout.setSpacing(20)  # 减小元素间距
        
        # 创建标题区域
        title_label = QLabel('Python Box')
        title_label.setFont(QFont("SimHei", 28, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2d3436;")  # 移除底部边距
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel('多功能实用工具集')
        subtitle_label.setFont(QFont("SimHei", 14))
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #636e72;")  # 移除底部边距
        main_layout.addWidget(subtitle_label)
        
        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        # PyQt6中不需要设置阴影，使用样式表来控制外观
        line.setStyleSheet("background-color: #dfe6e9; height: 1px;")  # 移除底部边距
        main_layout.addWidget(line)
        
        # 游戏类别标签
        games_label = QLabel("游戏")
        games_label.setObjectName("categoryLabel")
        main_layout.addWidget(games_label)
        
        # 游戏卡片网格布局 - 每行2个卡片
        games_grid = QGridLayout()
        games_grid.setSpacing(45)  # 增大卡片之间的水平间距
        games_grid.setVerticalSpacing(40)  # 增大卡片之间的垂直间距
        games_grid.setContentsMargins(15, 0, 15, 0)  # 减少边距
        main_layout.addLayout(games_grid)
        
        # 创建2048游戏卡片
        self.create_card(games_grid, 0, 0, "2048游戏", 
                        "background-color: #f8f9fa; border-left: 5px solid #4CAF50;",
                        self.run_game2048)
        
        # 创建贪吃蛇游戏卡片
        self.create_card(games_grid, 0, 1, "贪吃蛇游戏", 
                        "background-color: #f8f9fa; border-left: 5px solid #2196F3;",
                        self.run_snake)
        
        # 创建小恐龙游戏卡片
        if DinoGame:
            self.create_card(games_grid, 1, 0, "小恐龙游戏", 
                            "background-color: #f8f9fa; border-left: 5px solid #9C27B0;",
                            self.run_dino_game)
        
        # 创建俄罗斯方块游戏卡片
        if TetrisGame:
            self.create_card(games_grid, 1, 1, "俄罗斯方块", 
                            "background-color: #f8f9fa; border-left: 5px solid #F44336;",
                            self.run_tetris_game)
        
        # 设置游戏网格的列拉伸
        for i in range(2):
            games_grid.setColumnStretch(i, 1)
        
        # 工具类别标签
        tools_label = QLabel("工具")
        tools_label.setObjectName("categoryLabel")
        main_layout.addWidget(tools_label)
        
        # 工具卡片网格布局 - 每行2个卡片
        tools_grid = QGridLayout()
        tools_grid.setSpacing(45)  # 增大卡片之间的水平间距
        tools_grid.setVerticalSpacing(40)  # 增大卡片之间的垂直间距
        tools_grid.setContentsMargins(15, 0, 15, 0)  # 减少边距
        main_layout.addLayout(tools_grid)
        
        # 创建小说下载器卡片
        self.create_card(tools_grid, 0, 0, "小说下载器", 
                        "background-color: #f8f9fa; border-left: 5px solid #FF9800;",
                        self.run_novel_downloader)
        
        # 创建视频下载器卡片
        self.create_card(tools_grid, 0, 1, "视频下载器", 
                        "background-color: #f8f9fa; border-left: 5px solid #9C27B0;",
                        self.run_video_downloader)
        
        # 创建音频格式转换工具卡片
        self.create_card(tools_grid, 1, 0, "音频格式转换工具", 
                        "background-color: #f8f9fa; border-left: 5px solid #009688;",
                        self.run_audio_converter)

        # 创建应用程序打包工具卡片
        self.create_card(tools_grid, 1, 1, "应用程序打包工具", 
                        "background-color: #f8f9fa; border-left: 5px solid #3F51B5;",
                        self.run_package_app)

        # 设置工具网格的列拉伸
        for i in range(2):
            tools_grid.setColumnStretch(i, 1)
        
        # 减少不必要的空白，移除多余的伸缩项
        # main_layout.addStretch()
        
        # 添加底部信息
        footer_label = QLabel('© 2023 Python Box_Designed_by_wwq 多功能实用工具集')
        footer_label.setFont(QFont("SimHei", 10))
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("color: #b2bec3; margin-top: 15px;")
        main_layout.addWidget(footer_label)
        
        # 创建设置和帮助区域（下移到底部）
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(15)
        main_layout.addLayout(settings_layout)
        
        # 创建设置按钮
        self.settings_button = QPushButton('设置')
        self.settings_button.setFont(self.font)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #636e72;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                /* PyQt6不支持transition属性，已移除 */
            }
            QPushButton:hover {
                background-color: #b2bec3;
                /* PyQt6不支持transform属性，使用背景色变化作为替代效果 */
            }
        """)
        self.settings_button.clicked.connect(self.show_settings)
        settings_layout.addWidget(self.settings_button)
        
        # 创建日志按钮
        self.log_button = QPushButton('查看日志')
        self.log_button.setFont(self.font)
        self.log_button.setStyleSheet("""
            QPushButton {
                background-color: #636e72;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                /* PyQt6不支持transition属性，已移除 */
            }
            QPushButton:hover {
                background-color: #b2bec3;
                /* PyQt6不支持transform属性，使用背景色变化作为替代效果 */
            }
        """)
        self.log_button.clicked.connect(self.show_log)
        settings_layout.addWidget(self.log_button)
        
        # 创建版本历史按钮
        self.version_button = QPushButton('版本历史')
        self.version_button.setFont(self.font)
        self.version_button.setStyleSheet("""
            QPushButton {
                background-color: #636e72;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                border: none;
                /* PyQt6不支持transition属性，已移除 */
            }
            QPushButton:hover {
                background-color: #b2bec3;
                /* PyQt6不支持transform属性，使用背景色变化作为替代效果 */
            }
        """)
        self.version_button.clicked.connect(self.show_version_history)
        settings_layout.addWidget(self.version_button)
        
        # 创建状态栏
        self.statusBar().setStyleSheet("background-color: #f5f5f7; color: #636e72; border: none;")
        self.statusBar().showMessage("欢迎使用 Python Box")
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 连接窗口关闭事件
        self.closeEvent = self.on_close_event
    
    def create_card(self, parent_layout, row, col, title, style, callback):
        """
        创建卡片组件并添加到指定布局
        
        参数:
            parent_layout: 父布局
            row: 卡片所在行
            col: 卡片所在列
            title: 卡片标题
            style: 卡片样式
            callback: 点击卡片的回调函数
        """
        # 创建卡片框架
        card_frame = QFrame()
        card_frame.setObjectName("cardFrame")
        card_frame.setMinimumHeight(80)  # 增加卡片最小高度，确保文字显示空间
        card_frame.setMinimumWidth(300)  # 增加卡片最小宽度，确保文字完整显示
        card_frame.setMaximumWidth(400)  # 增加卡片最大宽度，确保文字完整显示
        card_frame.setMaximumHeight(100)  # 增加卡片最大高度，确保文字显示空间
        # 合并基础样式和传入样式，确保边框样式被应用
        base_style = "border: 1px solid #e0e0e0;"  # 确保边框样式
        card_frame.setStyleSheet(base_style + " " + style)
        
        # 创建卡片布局
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(10, 10, 10, 10)  # 设置适当边距，确保文字不会紧贴边缘
        card_layout.setSpacing(0)  # 移除布局内间距
        
        # 创建卡片按钮
        card_button = QPushButton(title)
        card_button.setObjectName("cardButton")
        card_button.setFont(self.font)
        card_button.clicked.connect(callback)
        card_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # 让按钮填充整个卡片
        card_button.setContentsMargins(5, 5, 5, 5)  # 设置按钮边距，确保文字有足够空间显示
        
        # 添加按钮到卡片布局
        card_layout.addWidget(card_button)
        
        # 将卡片添加到父布局
        parent_layout.addWidget(card_frame, row, col)
        
    def center_window(self):
        """将窗口显示在屏幕中央偏上位置"""
        screen = self.screen().geometry()
        size = self.geometry()
        # 让窗口上移30像素，使视觉效果更好
        self.move((screen.width() - size.width()) // 2, 
                  ((screen.height() - size.height()) // 2) - 30)
    
    def create_tray_icon(self):
        """
        创建系统托盘图标
        设置托盘图标、菜单和相关行为
        """
        # 检查系统是否支持系统托盘
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 使用内置图标
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Python_box")
        
        # 创建托盘菜单
        tray_menu = QMenu(self)
        
        # 显示主窗口动作
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        # 显示设置对话框动作
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tray_menu.addAction(settings_action)
        
        # 显示日志查看器动作
        log_action = QAction("查看日志", self)
        log_action.triggered.connect(self.show_log)
        tray_menu.addAction(log_action)
        
        # 显示版本历史动作
        version_action = QAction("版本历史", self)
        version_action.triggered.connect(self.show_version_history)
        tray_menu.addAction(version_action)
        
        # 退出动作
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 连接托盘图标激活信号
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def on_tray_icon_activated(self, reason):
        """
        处理托盘图标激活事件
        当双击托盘图标时显示主窗口
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()

    def changeEvent(self, event):
        """
        处理窗口状态变化事件
        根据设置决定窗口最小化时的行为
        """
        if event.type() == event.Type.WindowStateChange:
            # 检查窗口是否最小化
            if self.isMinimized():
                # 使用AppLauncher类中已经加载的settings变量
                # 检查设置是否允许最小化到托盘
                minimize_to_tray = self.settings.get('minimize_to_tray', True)
                
                if minimize_to_tray:
                    # 如果设置允许最小化到托盘且系统托盘已启用
                    if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
                        self.hide()
                        # 显示通知
                        self.tray_icon.showMessage(
                            "应用程序最小化",
                            "应用程序已最小化到系统托盘，双击托盘图标可恢复显示。",
                            QSystemTrayIcon.MessageIcon.Information,
                            3000
                        )
                        # 记录操作日志
                        logger.info("应用程序最小化到系统托盘")
                else:
                    # 如果设置不允许最小化到托盘，让窗口正常缩小到任务栏
                    logger.info("应用程序最小化到任务栏")
                    # 不执行任何特殊操作，让窗口按照默认行为最小化到任务栏
        # 调用父类的changeEvent以确保正常的事件处理流程
        super().changeEvent(event)

    def on_close_event(self, event):
        """
        处理窗口关闭事件
        根据设置决定点击关闭按钮时的行为
        """
        # 检查设置是否允许最小化到托盘
        minimize_to_tray = self.settings.get('minimize_to_tray', True)
        
        if minimize_to_tray:
            # 如果设置允许最小化到托盘且系统托盘已启用
            if hasattr(self, 'tray_icon') and self.tray_icon and self.tray_icon.isVisible():
                # 隐藏主窗口而不是关闭
                self.hide()
                # 显示通知
                self.tray_icon.showMessage(
                    "应用程序最小化",
                    "应用程序已最小化到系统托盘，双击托盘图标可恢复显示。",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
                # 记录操作日志
                logger.info("应用程序最小化到系统托盘")
                # 忽略关闭事件
                event.ignore()
                return
        
        # 如果设置不允许最小化到托盘或系统托盘未启用，正常关闭
        logger.info("应用程序正常关闭")
        event.accept()
    
    def log_action(self, message, log_type="info"):
        """
        记录操作日志
        
        参数:
            message: 日志消息内容
            log_type: 日志类型，默认为"info"，可选值包括"info"、"error"等
        """
        # 记录到日志文件
        if log_type.lower() == "error":
            logger.error(message)
        else:
            logger.info(message)
        
        # 将日志添加到历史记录中
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{log_type.upper()}] {message}"
        
        # 保存到日志历史列表
        self.log_history.append(log_entry)
        
        # 限制日志历史记录的数量，防止内存占用过多
        if len(self.log_history) > 1000:
            self.log_history = self.log_history[-1000:]
    
    def create_progress_window(self, title):
        """创建并显示进度条窗口"""
        # 如果进度窗口已存在，先关闭
        if self.progress_window:
            self.progress_window.close()
            self.progress_window = None
            
        # 创建新的进度窗口
        self.progress_window = QDialog(self)
        self.progress_window.setWindowTitle(title)
        self.progress_window.setGeometry(100, 100, 300, 100)
        self.progress_window.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        # 创建布局
        layout = QVBoxLayout(self.progress_window)
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("加载中: %p%")
        layout.addWidget(self.progress_bar)
        
        # 居中显示进度窗口
        self.progress_window.move(
            (self.screen().geometry().width() - self.progress_window.width()) // 2,
            (self.screen().geometry().height() - self.progress_window.height()) // 2
        )
        
        # 显示进度窗口
        self.progress_window.show()
        
        # 重置进度值
        self.progress_value = 0
        
    def update_progress(self):
        """更新进度条显示"""
        if not self.progress_window or not hasattr(self, 'progress_bar'):
            return
        
        # 增加进度值
        self.progress_value += 5
        if self.progress_value > 95:
            self.progress_value = 95  # 保留最后5%用于实际加载完成
        
        self.progress_bar.setValue(self.progress_value)
        
        # 继续更新进度条
        QTimer.singleShot(50, self.update_progress)
        
    def finalize_progress(self):
        """完成进度显示并关闭进度窗口"""
        if self.progress_window and hasattr(self, 'progress_bar'):
            # 设置进度为100%
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("加载完成!")
            
            # 延迟关闭进度窗口
            QTimer.singleShot(200, self.progress_window.close)
    
    def run_game2048(self):
        """运行2048游戏，保留主窗口并显示进度条"""
        # 移除对不存在的game2048_button属性的引用
        pass
        try:
            # 创建进度条窗口
            self.create_progress_window("启动2048游戏")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建2048游戏窗口，保留主窗口可见
            self.game2048_window = Game2048()
            
            # 记录日志
            logger.info("用户启动了2048游戏")
            
            # 完成进度显示
            self.finalize_progress()
            
            # 显示游戏窗口
            self.game2048_window.show()
            # 显示后再次调用居中方法，确保窗口正确居中
            self.game2048_window.center_window()
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', f'无法运行2048游戏: {str(e)}')
            # 移除对不存在的game2048_button属性的引用
        
    def run_snake(self):
        """运行贪吃蛇游戏，保留主窗口并显示进度条"""
        # 移除对不存在的snake_button属性的引用
        pass
        try:
            # 创建进度条窗口
            self.create_progress_window("启动贪吃蛇游戏")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建贪吃蛇游戏窗口，保留主窗口可见
            self.snake_window = SnakeGame()
            
            # 记录日志
            logger.info("用户启动了贪吃蛇游戏")
            
            # 完成进度显示
            self.finalize_progress()
            
            # 显示游戏窗口
            self.snake_window.show()
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', f'无法运行贪吃蛇游戏: {str(e)}')
            # 移除对不存在的snake_button属性的引用
        
    def run_novel_downloader(self):
        """运行小说下载器，保留主窗口并显示进度条"""
        # 移除对不存在的novel_downloader_button属性的引用
        pass
        try:
            # 创建进度条窗口
            self.create_progress_window("启动小说下载器")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建小说下载器窗口，保留主窗口可见
            self.novel_window = NovelDownloadWindow()
            self.child_windows.append(self.novel_window)
            
            # 设置窗口关闭事件
            self.novel_window.destroyed.connect(self._on_child_window_close_without_event)
            
            # 完成进度显示
            self.finalize_progress()
            
            # 显示小说下载器窗口
            self.novel_window.show()
            
            # 记录操作日志
            self.log_action("启动小说下载器")
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            error_msg = f'无法运行小说下载器: {str(e)}'
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', error_msg)
            # 移除对不存在的novel_downloader_button属性的引用
            # 记录错误日志
            self.log_action(error_msg, "error")
        
    def run_video_downloader(self):
        """运行视频下载器，保留主窗口并显示进度条"""
        # 移除对不存在的video_downloader_button属性的引用
        pass
        try:
            # 创建进度条窗口
            self.create_progress_window("启动视频下载器")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建视频下载器窗口，保留主窗口可见
            self.video_window = VideoDownloaderWindow()
            self.child_windows.append(self.video_window)
            
            # 设置窗口关闭事件
            self.video_window.destroyed.connect(self._on_child_window_close_without_event)
            
            # 完成进度显示
            self.finalize_progress()
            
            # 显示视频下载器窗口
            self.video_window.show()
            
            # 记录操作日志
            self.log_action("启动视频下载器")
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            error_msg = f'无法运行视频下载器: {str(e)}'
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', error_msg)
            # 移除对不存在的video_downloader_button属性的引用
            # 记录错误日志
            self.log_action(error_msg, "error")
    
    def run_audio_converter(self):
        """运行音频格式转换工具，保留主窗口并显示进度条"""
        # 移除对不存在的audio_converter_button属性的引用
        pass
        try:
            # 创建进度条窗口
            self.create_progress_window("启动音频格式转换工具")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建音频格式转换工具窗口，保留主窗口可见
            self.audio_window = AudioFormatConverterWindow()
            self.child_windows.append(self.audio_window)
            
            # 设置窗口关闭事件
            self.audio_window.destroyed.connect(self._on_child_window_close_without_event)
            
            # 完成进度显示
            self.finalize_progress()
            
            # 显示音频格式转换工具窗口
            self.audio_window.show()
            
            # 记录操作日志
            self.log_action("启动音频格式转换工具")
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            error_msg = f'无法运行音频格式转换工具: {str(e)}'
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', error_msg)
            # 移除对不存在的audio_converter_button属性的引用
            # 记录错误日志
            self.log_action(error_msg, "error")

    def run_package_app(self):
        """运行应用程序打包工具，保留主窗口"""
        try:
            # 创建应用程序打包工具窗口，保留主窗口可见
            self.package_window = PackageAppGUI()
            self.child_windows.append(self.package_window)
            
            # 设置窗口关闭事件
            self.package_window.destroyed.connect(self._on_child_window_close_without_event)
            
            # 显示应用程序打包工具窗口
            self.package_window.show()
            
            # 记录操作日志
            self.log_action("启动应用程序打包工具")
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            error_msg = f'无法运行应用程序打包工具: {str(e)}'
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', error_msg)
            # 记录错误日志
            self.log_action(error_msg, "error")

    def run_dino_game(self):
        """运行小恐龙游戏，保留主窗口并显示进度条"""
        if not DinoGame:
            QMessageBox.warning(self, "警告", "小恐龙游戏模块不可用，请确保dino_game.py文件存在且可导入。")
            return
        
        # 移除对不存在的dino_button属性的引用
        pass
        try:
            # 创建进度条窗口
            self.create_progress_window("启动小恐龙游戏")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建小恐龙游戏窗口，保留主窗口可见
            self.dino_window = DinoGame()
            self.child_windows.append(self.dino_window)
            
            # 设置窗口关闭事件（不传递已销毁的窗口对象）
            self.dino_window.destroyed.connect(self._on_child_window_close_without_event)
            
            # 完成进度显示
            self.finalize_progress()
            
            # 显示游戏窗口
            self.dino_window.show()
            
            # 确保窗口获得焦点
            self.dino_window.activateWindow()
            self.dino_window.setFocus()
            self.dino_window.grabKeyboard()
            
            # 记录操作日志
            self.log_action("启动小恐龙游戏")
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            error_msg = f'无法运行小恐龙游戏: {str(e)}'
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', error_msg)
            # 移除对不存在的dino_button属性的引用
            # 记录错误日志
            self.log_action(error_msg, "error")
        
    def run_tetris_game(self):
        """运行俄罗斯方块游戏，保留主窗口并显示进度条"""
        if not TetrisGame:
            QMessageBox.warning(self, "警告", "俄罗斯方块游戏模块不可用，请确保tetris_game.py文件存在且可导入。")
            return
        
        # 移除对不存在的tetris_button属性的引用
        pass
        try:
            # 创建进度条窗口
            self.create_progress_window("启动俄罗斯方块游戏")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建俄罗斯方块游戏窗口，保留主窗口可见
            self.tetris_window = TetrisGame()
            self.child_windows.append(self.tetris_window)
            
            # 设置窗口关闭事件（不传递已销毁的窗口对象）
            self.tetris_window.destroyed.connect(self._on_child_window_close_without_event)
            
            # 完成进度显示
            self.finalize_progress()
            
            # 显示游戏窗口
            self.tetris_window.show()
            
            # 确保窗口获得焦点
            self.tetris_window.activateWindow()
            self.tetris_window.setFocus()
            self.tetris_window.grabKeyboard()
            
            # 记录操作日志
            self.log_action("启动俄罗斯方块游戏")
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            error_msg = f'无法运行俄罗斯方块游戏: {str(e)}'
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', error_msg)
            # 移除对不存在的tetris_button属性的引用
            # 记录错误日志
            self.log_action(error_msg, "error")
    
    def _button_clicked_feedback(self, button):
        """按钮点击反馈效果"""
        original_style = button.styleSheet()
        # 临时改变按钮样式
        button.setStyleSheet(original_style + " background-color: #777777;")
        # 立即重绘
        button.repaint()
        # 延迟一小段时间后恢复原样式
        QTimer.singleShot(150, lambda: self._reset_button_style(button, self._get_original_color(original_style)))
    
    def _reset_button_style(self, button, color):
        """重置按钮样式"""
        button.setStyleSheet(f"background-color: {color}; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
    
    def _get_original_color(self, style):
        """从样式表中提取原始颜色"""
        if "#4CAF50" in style:
            return "#4CAF50"
        elif "#2196F3" in style:
            return "#2196F3"
        elif "#FF9800" in style:
            return "#FF9800"
        elif "#9C27B0" in style:
            return "#9C27B0"  # 小恐龙游戏按钮颜色
        elif "#F44336" in style:
            return "#F44336"  # 俄罗斯方块按钮颜色
        elif "#607D8B" in style:
            return "#607D8B"  # 设置和帮助按钮颜色
        else:
            return "#4CAF50"  # 默认颜色
    
    def load_settings(self):
        """
        加载应用程序设置
        确保从infor文件夹中加载配置文件
        返回: 包含设置的字典
        """
        try:
            # 确保infor文件夹存在
            if not os.path.exists(CONFIG_DIR):
                try:
                    os.makedirs(CONFIG_DIR)
                    logging.info(f"创建配置目录: {CONFIG_DIR}")
                except Exception as e:
                    logging.error(f"创建配置目录失败: {str(e)}")
            
            # 尝试加载设置
            if os.path.exists(APP_SETTINGS_FILE):
                try:
                    with open(APP_SETTINGS_FILE, 'rb') as f:
                        settings = pickle.load(f)
                    logging.info("成功加载应用设置")
                    return settings
                except Exception as e:
                    logging.error(f"加载设置文件失败: {str(e)}")
                    # 出错时返回默认设置
                    default_settings = {
                        'show_welcome': True,
                        'auto_save': True,
                        'minimize_to_tray': True,  # 默认允许最小化到托盘
                        'log_level': 'INFO'
                    }
                    return default_settings
            else:
                # 如果设置文件不存在，返回默认设置
                default_settings = {
                    'show_welcome': True,
                    'auto_save': True,
                    'minimize_to_tray': True,  # 默认允许最小化到托盘
                    'log_level': 'INFO'
                }
                logging.info("设置文件不存在，使用默认设置")
                return default_settings
        except Exception as e:
            logging.error(f"加载设置时出错: {str(e)}")
            # 出错时返回默认设置
            return {
                'show_welcome': True,
                'auto_save': True,
                'minimize_to_tray': True,  # 默认允许最小化到托盘
                'log_level': 'INFO'
            }
    
    def show_settings(self):
        """显示应用设置对话框"""
        try:
            # 显示设置对话框
            settings_dialog = SettingsDialog(self)
            result = settings_dialog.exec()
            # 记录操作日志
            logger.info("用户打开了设置对话框")
            
            # 如果设置对话框返回接受（用户点击了保存），重新加载设置
            if result == QDialog.DialogCode.Accepted:
                self.settings = self.load_settings()
                logger.info("成功重新加载应用设置")
        except Exception as e:
            print(f"显示设置对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"显示设置对话框失败: {str(e)}")
            # 记录错误日志
            logger.error(f"显示设置对话框失败: {str(e)}")
    
    def show_log(self):
        """显示日志查看器对话框"""
        try:
            # 显示日志查看器
            log_viewer = LogViewerDialog(self)
            log_viewer.exec()
            # 记录操作日志
            logger.info("用户打开了日志查看器")
        except Exception as e:
            print(f"显示日志查看器失败: {e}")
            QMessageBox.critical(self, "错误", f"显示日志查看器失败: {str(e)}")
            # 记录错误日志
            logger.error(f"显示日志查看器失败: {str(e)}")
    
    def show_version_history(self):
        """显示版本历史对话框"""
        try:
            # 显示版本历史对话框
            version_dialog = VersionHistoryDialog(self)
            version_dialog.exec()
            # 记录操作日志
            logger.info("用户打开了版本历史对话框")
        except Exception as e:
            print(f"显示版本历史对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"显示版本历史对话框失败: {str(e)}")
            # 记录错误日志
            logger.error(f"显示版本历史对话框失败: {str(e)}")
    
    def _show_launcher(self):
        """重新显示启动器窗口"""
        # 确保所有子窗口都已关闭
        QTimer.singleShot(100, self.show)
        
    def _on_child_window_close(self, event):
        """处理子窗口关闭事件的回调函数（用于QCloseEvent事件）"""
        # 确保事件被接受，窗口可以正常关闭
        event.accept()
        # 直接显示启动器窗口
        self._show_launcher()
        
    def _on_child_window_close_without_event(self):
        """处理窗口销毁信号的回调函数（用于destroyed信号）"""
        # 直接显示启动器窗口
        self._show_launcher()


# ===== 自定义对话框类 =====            
class CustomDialog(QDialog):
    """自定义对话框类，用于显示各种消息提示"""
    def __init__(self, message, title="提示", button_text="确定", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(300, 150)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 添加消息标签
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton(button_text)
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 8px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.setLayout(layout)


# ===== 小恐龙游戏实现 =====
class DinoGame(QWidget):
    """
    小恐龙游戏主窗口类
    实现了简单的跳跃躲避游戏，玩家控制恐龙跳跃躲避障碍物，获取分数。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("小恐龙游戏_designed_by_wwq")
        self.setMinimumSize(800, 600)
        self.init_game()
        self.setup_ui()
        self.setup_styles()
        self.is_running = False
        self.center_window()
        
        # 游戏趣味性增强：添加背景音乐控制（实际使用时需添加音效文件）
        self.sound_enabled = False  # 默认禁用音效
        
        # 确保窗口获得焦点以接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def setup_ui(self):
        """初始化用户界面，包括游戏画布和控制按钮"""
        main_layout = QVBoxLayout(self)
        
        # 创建游戏画布
        self.game_canvas = DinoGameCanvas(self)
        self.game_canvas.setMinimumSize(800, 500)
        main_layout.addWidget(self.game_canvas)
        
        # 创建控制按钮区域
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        
        # 开始按钮
        self.start_button = QPushButton("开始游戏")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.clicked.connect(self.start_game)
        control_layout.addWidget(self.start_button)
        
        # 暂停按钮
        self.pause_button = QPushButton("暂停游戏")
        self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        self.pause_button.clicked.connect(self.pause_game)
        self.pause_button.setEnabled(False)
        control_layout.addWidget(self.pause_button)
        
        # 重启按钮
        self.restart_button = QPushButton("重新开始")
        self.restart_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.restart_button.clicked.connect(self.restart_game)
        self.restart_button.setEnabled(False)
        control_layout.addWidget(self.restart_button)
        
        # 移除音效按钮，游戏默认为静音状态
        
        # 分数显示
        self.score_label = QLabel("分数: 0")
        self.score_label.setFont(QFont("SimHei", 12, QFont.Weight.Bold))
        control_layout.addWidget(self.score_label)
        
        # 最高分显示
        self.high_score_label = QLabel("最高分: 0")
        self.high_score_label.setFont(QFont("SimHei", 12, QFont.Weight.Bold))
        control_layout.addWidget(self.high_score_label)
        
        main_layout.addLayout(control_layout)
        
    def setup_styles(self):
        """设置游戏界面样式"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: SimHei, Microsoft YaHei, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
        """)
        
    def init_game(self):
        """初始化游戏参数"""
        # 游戏状态变量
        self.speed = 5  # 初始速度
        self.score = 0
        self.high_score = 0
        
        # 尝试加载最高分记录
        self.load_high_score()
        
    def start_game(self):
        """开始游戏"""
        self.is_running = True
        self.game_canvas.start_game()
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.restart_button.setEnabled(True)
        
    def pause_game(self):
        """暂停游戏"""
        if self.is_running:
            self.is_running = False
            self.game_canvas.pause_game()
            self.pause_button.setText("继续游戏")
            self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.is_running = True
            self.game_canvas.resume_game()
            self.pause_button.setText("暂停游戏")
            self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            
    def restart_game(self):
        """重新开始游戏"""
        self.game_canvas.reset_game()
        self.is_running = True
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_button.setText("暂停游戏")
        self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        self.update_score(0)
        
    def game_over(self):
        """游戏结束处理"""
        self.is_running = False
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        
        # 检查是否更新最高分
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
            self.high_score_label.setText(f"最高分: {self.high_score}")
        
        # 不再显示弹窗，游戏结束后按空格键直接重来
        # 保持按键焦点，以便用户可以立即按空格键
            
    def update_score(self, points):
        """更新分数显示"""
        self.score = points
        self.score_label.setText(f"分数: {self.score}")
        
    def toggle_sound(self):
        """切换音效开关"""
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.sound_button.setText("关闭音效")
            self.sound_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        else:
            self.sound_button.setText("开启音效")
            self.sound_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolumeMuted))
            
    def load_high_score(self):
        """加载最高分记录"""
        try:
            import pickle
            save_path = DINO_GAME_SCORES_FILE
            if os.path.exists(save_path):
                with open(save_path, 'rb') as f:
                    self.high_score = pickle.load(f)
                    self.high_score_label.setText(f"最高分: {self.high_score}")
        except Exception as e:
            print(f"加载最高分失败: {e}")
            logger.error(f"加载小恐龙游戏最高分失败: {e}")
            
    def save_high_score(self):
        """保存最高分记录"""
        try:
            import pickle
            save_path = DINO_GAME_SCORES_FILE
            # 确保配置目录存在
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            with open(save_path, 'wb') as f:
                pickle.dump(self.high_score, f)
        except Exception as e:
            print(f"保存最高分失败: {e}")
            logger.error(f"保存小恐龙游戏最高分失败: {e}")
            
    def center_window(self):
        """将窗口居中显示"""
        screen = self.screen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, 
                  (screen.height() - size.height()) // 2)
        
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key.Key_Space:
            if self.is_running:
                self.game_canvas.jump()
            elif not self.start_button.isEnabled():
                # 游戏暂停状态下，空格键继续游戏
                self.pause_game()
            else:
                # 游戏未开始状态下，空格键开始游戏
                # 游戏结束状态下，空格键直接重新开始游戏
                if hasattr(self.parent, 'game_over') and not self.is_running:
                    self.restart_game()
                else:
                    self.start_game()
        elif event.key() == Qt.Key.Key_Down:
            # 下箭头键下蹲
            if self.is_running:
                self.game_canvas.crouch()
        elif event.key() == Qt.Key.Key_Up:
            # 上箭头键站立
            if self.is_running:
                self.game_canvas.stand_up()
        elif event.key() == Qt.Key.Key_Escape:
            # ESC键退出游戏
            self.close()
        elif event.key() == Qt.Key.Key_P:
            # P键暂停/继续游戏
            if self.is_running or self.pause_button.isEnabled():
                self.pause_game()
        elif event.key() == Qt.Key.Key_R:
            # R键重新开始游戏
            self.restart_game()
        
        # 不再将事件传播给父类，防止键盘事件冲突
        # super().keyPressEvent(event)
        
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 释放键盘捕获
        self.releaseKeyboard()
        # 调用父类的closeEvent以确保正常关闭流程
        super().closeEvent(event)

class DinoGameCanvas(QWidget):
    """
    游戏画布类
    负责绘制游戏场景、恐龙、障碍物等，并处理游戏逻辑。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("background-color: #ffffff;")
        
        # 初始化游戏参数
        self.dino_width = 35  # 缩小恐龙尺寸
        self.dino_height = 40
        self.dino_x = 30
        self.dino_y = 0  # 将在reset_game中设置
        self.dino_velocity = 0
        self.gravity = 0.8
        self.jump_strength = -16  # 略微增加跳跃力量，配合缩小后的尺寸
        self.is_jumping = False
        
        # 障碍物参数
        self.obstacles = []
        self.obstacle_width = 20  # 缩小障碍物尺寸
        self.obstacle_height = 40
        self.obstacle_spacing = 300  # 障碍物之间的最小间距
        self.last_obstacle_x = 0
        
        # 地面参数
        self.ground_y = 0  # 将在reset_game中设置
        
        # 背景移动参数
        self.background_x = 0
        self.background_speed = 5
        
        # 游戏状态
        self.game_speed = 6  # 增加初始速度
        self.score = 0
        self.last_score_time = time.time()
        self.obstacles_passed = 0  # 记录成功跳过的障碍物数量
        
        # 添加下蹲状态
        self.is_crouching = False
        self.original_dino_height = self.dino_height
        self.crouching_dino_height = self.dino_height // 2  # 下蹲时恐龙高度减半
        
        # 创建定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        
        # 云朵参数（增加游戏趣味性）
        self.clouds = []
        
        # 重置游戏
        self.reset_game()
        
    def reset_game(self):
        """重置游戏状态"""
        # 重新设置恐龙位置
        self.ground_y = self.height() - 100
        self.dino_y = self.ground_y - self.dino_height
        self.dino_velocity = 0
        self.is_jumping = False
        self.is_crouching = False
        self.dino_height = self.original_dino_height  # 恢复原始高度
        
        # 清空障碍物
        self.obstacles = []
        self.last_obstacle_x = 0
        self.obstacles_passed = 0
        
        # 重置背景
        self.background_x = 0
        
        # 重置分数
        self.score = 0
        self.game_speed = 5
        self.last_score_time = time.time()
        
        # 清空云朵
        self.clouds = []
        
        # 立即绘制初始画面
        self.update()
        
    def start_game(self):
        """开始游戏"""
        self.reset_game()
        self.timer.start(20)  # 50fps
        
    def pause_game(self):
        """暂停游戏"""
        self.timer.stop()
        
    def resume_game(self):
        """继续游戏"""
        self.timer.start(20)  # 50fps
        
    def jump(self):
        """恐龙跳跃"""
        if not self.is_jumping:
            # 如果正在下蹲，先恢复高度
            if self.is_crouching:
                self.stand_up()
            self.dino_velocity = self.jump_strength
            self.is_jumping = True
            
            # 播放跳跃音效
            if hasattr(self.parent, 'sound_enabled') and self.parent.sound_enabled:
                # 实际项目中可以添加音效播放代码
                pass
    
    def crouch(self):
        """恐龙下蹲"""
        if not self.is_jumping and not self.is_crouching:
            self.is_crouching = True
            self.dino_height = self.crouching_dino_height
            # 调整恐龙位置，保持底部在地面上
            self.dino_y = self.ground_y - self.dino_height
    
    def stand_up(self):
        """恐龙站立起来"""
        if self.is_crouching:
            self.is_crouching = False
            self.dino_height = self.original_dino_height
            # 调整恐龙位置，保持底部在地面上
            self.dino_y = self.ground_y - self.dino_height
        
    def update_game(self):
        """更新游戏状态"""
        # 更新恐龙位置
        self.dino_velocity += self.gravity
        self.dino_y += self.dino_velocity
        
        # 确保恐龙不会穿过地面
        if self.dino_y >= self.ground_y - self.dino_height:
            self.dino_y = self.ground_y - self.dino_height
            self.dino_velocity = 0
            self.is_jumping = False
        
        # 移动背景
        self.background_x -= self.background_speed
        if self.background_x <= -self.width():
            self.background_x = 0
        
        # 生成障碍物
        self.generate_obstacles()
        
        # 更新障碍物位置和检测是否成功跳过，同时更新障碍物动画
        obstacles_to_remove = []
        current_time = time.time()
        
        for obstacle in self.obstacles:
            # 先检查是否成功跳过障碍物
            if obstacle['x'] + obstacle['width'] < self.dino_x and not obstacle.get('passed', False):
                obstacle['passed'] = True
                self.obstacles_passed += 1
            
            # 更新障碍物动画状态
            if obstacle.get('type') == 'cactus' and 'anim_state' in obstacle:
                # 仙人掌轻微摇摆动画
                if current_time - obstacle.get('anim_time', 0) > 0.2:
                    obstacle['anim_state'] = (obstacle['anim_state'] + 1) % 2
                    obstacle['anim_time'] = current_time
            elif obstacle.get('type') == 'bird' and 'flap_state' in obstacle:
                # 飞鸟翅膀扇动动画 - 增加动画平滑度
                if current_time - obstacle.get('flap_time', 0) > 0.08:  # 减小时间间隔使动画更流畅
                    # 使用连续的角度变化代替二进制状态
                    obstacle['flap_state'] = (obstacle['flap_state'] + 0.5) % (2 * math.pi)
                    obstacle['flap_time'] = current_time
            
            # 更新障碍物位置
            obstacle['x'] -= self.game_speed
            
            # 标记超出屏幕的障碍物
            if obstacle['x'] < -self.obstacle_width:
                obstacles_to_remove.append(obstacle)
        
        # 移除超出屏幕的障碍物
        for obstacle in obstacles_to_remove:
            self.obstacles.remove(obstacle)
        
        # 生成云朵
        self.generate_clouds()
        
        # 更新云朵位置
        for cloud in self.clouds[:]:
            cloud['x'] -= cloud['speed']
            # 移除超出屏幕的云朵
            if cloud['x'] < -cloud['width']:
                self.clouds.remove(cloud)
        
        # 更新分数
        self.score += int((current_time - self.last_score_time) * 10)
        # 不重置last_score_time，而是累加时间差
        # 这样分数会随游戏进行稳定增加
        
        # 更新父窗口的分数显示
        if hasattr(self.parent, 'update_score'):
            self.parent.update_score(self.score)
        
        # 随着分数增加，增加游戏难度 - 减缓速度增加的幅度
        self.game_speed = 6 + self.score // 2000  # 每得2000分增加一点速度，减缓速度增长
        
        # 检查碰撞
        self.check_collision()
        
        # 重绘画面
        self.update()
        
    def generate_obstacles(self):
        """生成障碍物"""
        # 使用更小的间距确保障碍物能够更频繁地生成
        adjusted_spacing = max(150, 300 - self.score // 300)  # 初始间距300，随着分数增加减少间距
        
        # 当障碍物列表为空时（游戏开始时），直接生成第一个障碍物
        if len(self.obstacles) == 0:
            # 即使不生成障碍物也更新last_obstacle_x，确保障碍物持续生成
            self.last_obstacle_x = self.width()
            
            # 随机决定障碍物类型（普通障碍物或飞鸟）
            obstacle_type = random.choice(['cactus', 'bird'])
            
            if obstacle_type == 'cactus':
                # 仙人掌障碍物
                obstacle = {
                    'x': self.width(),
                    'y': self.ground_y - self.obstacle_height,
                    'width': self.obstacle_width,
                    'height': self.obstacle_height,
                    'type': 'cactus',
                    'anim_state': 0,  # 新增动画状态
                    'anim_time': 0
                }
            else:
                # 飞鸟障碍物（在不同高度飞行）
                fly_height = random.choice([self.ground_y - 100, self.ground_y - 70, self.ground_y - 40])
                obstacle = {
                    'x': self.width(),
                    'y': fly_height,
                    'width': 30,  # 缩小飞鸟尺寸
                    'height': 20,
                    'type': 'bird',
                    'flap_state': 0,  # 新增扇动翅膀状态
                    'flap_time': 0
                }
            
            self.obstacles.append(obstacle)
        elif self.width() - self.last_obstacle_x > adjusted_spacing:
            # 即使不生成障碍物也更新last_obstacle_x，确保障碍物持续生成
            self.last_obstacle_x = self.width()
            
            # 提高生成概率到95%，确保更容易生成障碍物
            if random.random() < 0.95:
                # 随机决定障碍物类型（普通障碍物或飞鸟）
                obstacle_type = random.choice(['cactus', 'bird'])
                
                if obstacle_type == 'cactus':
                    # 仙人掌障碍物
                    obstacle = {
                        'x': self.width(),
                        'y': self.ground_y - self.obstacle_height,
                        'width': self.obstacle_width,
                        'height': self.obstacle_height,
                        'type': 'cactus',
                        'anim_state': 0,  # 新增动画状态
                        'anim_time': 0
                    }
                else:
                    # 飞鸟障碍物（在不同高度飞行）
                    fly_height = random.choice([self.ground_y - 100, self.ground_y - 70, self.ground_y - 40])
                    obstacle = {
                        'x': self.width(),
                        'y': fly_height,
                        'width': 30,  # 缩小飞鸟尺寸
                        'height': 20,
                        'type': 'bird',
                        'flap_state': 0,  # 新增扇动翅膀状态
                        'flap_time': 0
                    }
                
                self.obstacles.append(obstacle)
                # 增加调试信息，查看生成的障碍物
                # print(f"Generated obstacle: {obstacle}")
                
    def generate_clouds(self):
        """生成云朵（增加游戏趣味性）"""
        # 随机生成云朵
        if random.random() < 0.005:  # 低概率生成云朵
            cloud_width = random.randint(80, 150)
            cloud_height = random.randint(40, 70)
            cloud_y = random.randint(50, 150)
            cloud_speed = random.uniform(0.5, 2.0)
            
            cloud = {
                'x': self.width(),
                'y': cloud_y,
                'width': cloud_width,
                'height': cloud_height,
                'speed': cloud_speed
            }
            
            self.clouds.append(cloud)
            
    def check_collision(self):
        """检查碰撞，包含下蹲状态的特殊处理"""
        # 简单的矩形碰撞检测，将浮点数转换为整数
        dino_rect = QRect(int(self.dino_x), int(self.dino_y), int(self.dino_width), int(self.dino_height))
        
        for obstacle in self.obstacles:
            obstacle_rect = QRect(int(obstacle['x']), int(obstacle['y']), int(obstacle['width']), int(obstacle['height']))
            
            # 检测碰撞
            # 特殊处理：当恐龙下蹲且障碍物是飞鸟时，判断是否真的发生碰撞
            if dino_rect.intersects(obstacle_rect):
                # 如果恐龙在下蹲，并且障碍物是飞鸟，且飞鸟的位置在恐龙上方足够高，则视为没有碰撞
                if self.is_crouching and obstacle['type'] == 'bird':
                    # 判断飞鸟是否在恐龙下蹲时的头部上方
                    # 下蹲时恐龙高度减半，飞鸟需要足够高才能被躲避
                    if obstacle['y'] + obstacle['height'] < self.dino_y + self.dino_height // 2:
                        continue  # 没有碰撞，继续检查下一个障碍物
                # 播放碰撞音效
                if hasattr(self.parent, 'sound_enabled') and self.parent.sound_enabled:
                    # 实际项目中可以添加音效播放代码
                    pass
                
                # 停止游戏
                self.timer.stop()
                
                # 通知父窗口游戏结束
                if hasattr(self.parent, 'game_over'):
                    self.parent.game_over()
                
                break
                
    def paintEvent(self, event):
        """绘制游戏画面"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制天空背景
        painter.fillRect(self.rect(), QColor(240, 248, 255))
        
        # 绘制云朵
        for cloud in self.clouds:
            self.draw_cloud(painter, cloud)
        
        # 绘制地面
        ground_rect = QRect(0, self.ground_y, self.width(), self.height() - self.ground_y)
        painter.fillRect(ground_rect, QColor(169, 169, 169))
        
        # 绘制地面上的线条（增加立体感）
        for i in range(0, self.width() + 50, 50):
            line_x = (i + self.background_x) % (self.width() + 50)
            painter.drawLine(line_x, self.ground_y, line_x + 20, self.ground_y)
        
        # 绘制障碍物
        for obstacle in self.obstacles:
            if obstacle['type'] == 'cactus':
                self.draw_cactus(painter, obstacle)
            else:
                self.draw_bird(painter, obstacle)
        
        # 绘制恐龙
        self.draw_dino(painter)
        
        # 如果游戏未开始或已暂停，显示提示信息
        if not self.timer.isActive():
            self.draw_game_hints(painter)
            
    def draw_dino(self, painter):
        """绘制恐龙，包含精细的动画效果"""
        
        # 根据恐龙尺寸进行比例调整
        scale_factor = 0.7  # 缩放系数
        scaled_width = int(self.dino_width * scale_factor)
        scaled_height = int(self.dino_height * scale_factor)
        
        if self.is_crouching:
            # 下蹲姿势的精细绘制
            # 绘制下蹲的身体（更矮更宽）
            body_rect = QRect(int(self.dino_x), int(self.dino_y + 5), scaled_width + 5, scaled_height - 8)
            painter.fillRect(body_rect, QColor(0, 0, 0))
            
            # 绘制下蹲的头部（位置调整）
            head_rect = QRect(int(self.dino_x + scaled_width - 10), int(self.dino_y + 3), 15, 12)
            painter.fillRect(head_rect, QColor(0, 0, 0))
            
            # 绘制眼睛（更精细的位置）
            eye_rect = QRect(int(self.dino_x + scaled_width), int(self.dino_y + 7), 4, 4)
            painter.fillRect(eye_rect, QColor(255, 255, 255))
            
            # 绘制瞳孔
            pupil_rect = QRect(int(self.dino_x + scaled_width + 1), int(self.dino_y + 8), 2, 2)
            painter.fillRect(pupil_rect, QColor(0, 0, 0))
            
            # 绘制下蹲时的腿（折叠在身体下方，更精细的形状）
            leg1_rect = QRect(int(self.dino_x + 7), int(self.dino_y + scaled_height - 12), 10, 8)
            leg2_rect = QRect(int(self.dino_x + 25), int(self.dino_y + scaled_height - 12), 10, 8)
            painter.fillRect(leg1_rect, QColor(0, 0, 0))
            painter.fillRect(leg2_rect, QColor(0, 0, 0))
        else:
            # 正常站立/跳跃姿势的绘制
            # 绘制恐龙身体
            body_rect = QRect(int(self.dino_x), int(self.dino_y + 8), scaled_width, scaled_height - 12)
            painter.fillRect(body_rect, QColor(0, 0, 0))
            
            # 绘制恐龙头部（更圆润的形状）
            head_rect = QRect(int(self.dino_x + scaled_width - 15), int(self.dino_y), 15, 15)
            painter.fillRect(head_rect, QColor(0, 0, 0))
            
            # 绘制恐龙眼睛（更精细）
            eye_rect = QRect(int(self.dino_x + scaled_width - 5), int(self.dino_y + 5), 4, 4)
            painter.fillRect(eye_rect, QColor(255, 255, 255))
            
            # 绘制瞳孔
            pupil_rect = QRect(int(self.dino_x + scaled_width - 4), int(self.dino_y + 6), 2, 2)
            painter.fillRect(pupil_rect, QColor(0, 0, 0))
            
            # 绘制恐龙腿部（更精细的动画）
            if self.is_jumping:
                # 跳跃姿势（根据跳跃高度变化腿部角度）
                jump_offset = abs(int(self.dino_y) - int(self.ground_y - scaled_height))
                leg_angle = jump_offset / 3  # 根据跳跃高度调整腿部角度
                
                leg1_rect = QRect(int(self.dino_x + 7), int(self.dino_y + scaled_height - 15 - leg_angle), 8, 15)
                leg2_rect = QRect(int(self.dino_x + 22), int(self.dino_y + scaled_height - 15 + leg_angle), 8, 15)
            else:
                # 跑步姿势（更流畅的动画效果）
                current_time = time.time()
                # 使用sin函数创建更平滑的跑步动画，增加动画幅度使腿部动作更明显
                run_phase = (current_time * 20) % (2 * math.pi)  # 增加速度使动画更流畅
                leg1_offset = int(8 * math.sin(run_phase))  # 增加幅度使动作更明显
                leg2_offset = int(8 * math.sin(run_phase + math.pi))
                
                # 使用不同的腿部宽度来模拟更自然的跑步动作
                leg1_width = 8 if leg1_offset >= 0 else 10
                leg2_width = 8 if leg2_offset >= 0 else 10
                
                leg1_rect = QRect(int(self.dino_x + 7), int(self.dino_y + scaled_height - 15 + leg1_offset), leg1_width, 15)
                leg2_rect = QRect(int(self.dino_x + 22), int(self.dino_y + scaled_height - 15 + leg2_offset), leg2_width, 15)
            
            painter.fillRect(leg1_rect, QColor(0, 0, 0))
            painter.fillRect(leg2_rect, QColor(0, 0, 0))
        
    def draw_cactus(self, painter, obstacle):
        """绘制仙人掌障碍物，包含摇摆动画效果"""
        # 确保所有参数都是整数类型
        x = int(obstacle['x'])
        y = int(obstacle['y'])
        width = int(obstacle['width'])
        height = int(obstacle['height'])
        
        # 获取动画状态参数
        anim_state = obstacle.get('anim_state', 0)
        
        # 应用摇摆动画效果
        sway_offset = int(2 * math.sin(anim_state))
        x += sway_offset
        
        # 绘制仙人掌主体（更精细的形状）
        cactus_rect = QRect(x, y, width, height)
        painter.fillRect(cactus_rect, QColor(34, 139, 34))
        
        # 绘制仙人掌的刺（根据摇摆角度调整位置）
        thorns = [
            (x - 8, y + 15, 8, 4),  # 左上刺
            (x + width, y + 12, 8, 4),  # 右上刺
            (x - 8, y + 30, 8, 4),  # 左下刺
            (x + width, y + 36, 8, 4),  # 右下刺
            (x - 6, y + 22, 6, 3),  # 中间左上刺
            (x + width, y + 28, 6, 3)   # 中间右上刺
        ]
        
        for thorn in thorns:
            thorn_rect = QRect(int(thorn[0]), int(thorn[1]), int(thorn[2]), int(thorn[3]))
            painter.fillRect(thorn_rect, QColor(34, 139, 34))
            
        # 绘制仙人掌上的装饰
        decorations = [
            (x + 5, y + 10, 3, 3),  # 顶部装饰
            (x + 5, y + 25, 3, 3)   # 中部装饰
        ]
        
        for decoration in decorations:
            deco_rect = QRect(int(decoration[0]), int(decoration[1]), int(decoration[2]), int(decoration[3]))
            painter.fillRect(deco_rect, QColor(0, 100, 0))
            
    def draw_bird(self, painter, obstacle):
        """绘制飞鸟障碍物，包含翅膀扇动动画效果"""
        # 确保所有参数都是整数类型
        x = int(obstacle['x'])
        y = int(obstacle['y'])
        width = int(obstacle['width'])
        height = int(obstacle['height'])
        
        # 获取动画状态参数
        flap_state = obstacle.get('flap_state', 0)
        
        # 绘制鸟身（更精细的形状）
        body_color = QColor(165, 42, 42)  # 棕色
        bird_body_rect = QRect(x, y + 3, width - 8, height - 6)
        painter.fillRect(bird_body_rect, body_color)
        
        # 绘制鸟头（更圆润的形状）
        bird_head_rect = QRect(x + width - 12, y + 2, 12, 16)
        painter.fillRect(bird_head_rect, body_color)
        
        # 绘制鸟喙
        beak_color = QColor(255, 165, 0)  # 橙色
        beak_rect = QRect(x + width, y + 6, 6, 4)
        painter.fillRect(beak_rect, beak_color)
        
        # 绘制鸟眼（更精细）
        bird_eye_rect = QRect(x + width - 8, y + 5, 4, 4)
        painter.fillRect(bird_eye_rect, QColor(255, 255, 255))
        
        # 绘制瞳孔
        pupil_rect = QRect(x + width - 7, y + 6, 2, 2)
        painter.fillRect(pupil_rect, QColor(0, 0, 0))
        
        # 绘制翅膀（根据flap_state实现平滑的扇动动画）
        # 增加翅膀扇动的幅度，使动画效果更明显
        wing_angle = int(15 * math.sin(flap_state))
        
        # 左翅膀 - 增大尺寸和调整位置使翅膀更明显
        left_wing_y = y + 3 + wing_angle
        left_wing_rect = QRect(x + 2, left_wing_y, 18, 4)  # 增大翅膀尺寸
        painter.fillRect(left_wing_rect, body_color)
        
        # 右翅膀 - 无论鸟的大小都显示，增大尺寸
        right_wing_y = y + 3 - wing_angle
        right_wing_rect = QRect(x + 12, right_wing_y, 18, 4)  # 增大翅膀尺寸
        painter.fillRect(right_wing_rect, body_color)
        
    def draw_cloud(self, painter, cloud):
        """绘制云朵"""
        cloud_color = QColor(255, 255, 255, 200)  # 半透明白色
        # 将浮点数转换为整数以符合painter.fillRect的要求
        x = int(cloud['x'])
        y = int(cloud['y'])
        width = int(cloud['width'])
        height = int(cloud['height'])
        painter.fillRect(x, y, width, height, cloud_color)
        
    def draw_game_hints(self, painter):
        """绘制游戏提示信息"""
        # 设置字体
        font = QFont("SimHei", 18, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 0))
        
        # 绘制提示文本
        if self.score == 0:
            # 游戏未开始
            hint_text = "按空格键开始游戏"
        else:
            # 游戏暂停
            hint_text = "游戏暂停，按空格键继续"
            
        # 计算文本位置
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(hint_text)
        text_height = metrics.height()
        x = (self.width() - text_width) // 2
        y = (self.height() - text_height) // 2
        
        painter.drawText(x, y, hint_text)
        
        # 绘制操作说明
        small_font = QFont("SimHei", 12)
        painter.setFont(small_font)
        instructions = "空格键: 跳跃  |  P键: 暂停/继续  |  R键: 重新开始"
        instructions_width = painter.fontMetrics().horizontalAdvance(instructions)
        instructions_x = (self.width() - instructions_width) // 2
        instructions_y = y + 40
        
        painter.drawText(instructions_x, instructions_y, instructions)
        
    def keyPressEvent(self, event):
        """处理键盘事件 - 直接传递给父窗口"""
        if self.parent and hasattr(self.parent, 'keyPressEvent'):
            self.parent.keyPressEvent(event)
        
    def resizeEvent(self, event):
        """处理窗口大小变化"""
        # 调整地面和恐龙位置
        self.ground_y = self.height() - 100
        if not self.is_jumping:
            self.dino_y = self.ground_y - self.dino_height
        
        # 调整障碍物位置
        for obstacle in self.obstacles:
            if obstacle['type'] == 'cactus':
                obstacle['y'] = self.ground_y - obstacle['height']
                
        super().resizeEvent(event)


# ===== 俄罗斯方块游戏实现 =====
class TetrisGame(QWidget):
    """
    俄罗斯方块游戏主窗口类
    实现了经典的俄罗斯方块游戏，玩家控制方块下落并填满行以消除得分。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("俄罗斯方块_designed_by_wwq")
        self.setMinimumSize(800, 600)
        self.setup_ui()  # 先设置UI，确保所有UI组件都已创建
        self.init_game()  # 然后再初始化游戏数据
        self.setup_styles()
        self.is_running = False
        self.center_window()
        
        # 游戏趣味性增强：添加背景音乐控制
        self.sound_enabled = True
        
        # 确保窗口获得焦点以接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # 现在所有UI组件都已创建完成，可以安全地初始化游戏
        self.game_canvas.initialize_game()
        
    def setup_ui(self):
        """初始化用户界面，包括游戏画布和控制按钮"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        
        # 创建游戏画布
        self.game_canvas = TetrisGameCanvas(self)
        self.game_canvas.setMinimumSize(300, 500)
        main_layout.addWidget(self.game_canvas)
        
        # 创建右侧信息面板
        info_panel = QWidget()
        info_panel_layout = QVBoxLayout(info_panel)
        info_panel_layout.setSpacing(15)
        
        # 下一个方块预览
        next_block_label = QLabel("下一个方块:")
        next_block_label.setFont(QFont("SimHei", 12, QFont.Weight.Bold))
        self.next_block_preview = QLabel()
        self.next_block_preview.setFixedSize(100, 100)
        self.next_block_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_block_preview.setStyleSheet("background-color: #f0f0f0;")
        
        info_panel_layout.addWidget(next_block_label)
        info_panel_layout.addWidget(self.next_block_preview)
        
        # 分数显示
        score_label = QLabel("分数:")
        score_label.setFont(QFont("SimHei", 12, QFont.Weight.Bold))
        self.score_label = QLabel("0")
        self.score_label.setFont(QFont("SimHei", 14, QFont.Weight.Bold))
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.score_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        
        info_panel_layout.addWidget(score_label)
        info_panel_layout.addWidget(self.score_label)
        
        # 最高分显示
        high_score_label = QLabel("最高分:")
        high_score_label.setFont(QFont("SimHei", 12, QFont.Weight.Bold))
        self.high_score_label = QLabel("0")
        self.high_score_label.setFont(QFont("SimHei", 14, QFont.Weight.Bold))
        self.high_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.high_score_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        
        info_panel_layout.addWidget(high_score_label)
        info_panel_layout.addWidget(self.high_score_label)
        
        # 消除行数显示
        lines_label = QLabel("消除行数:")
        lines_label.setFont(QFont("SimHei", 12, QFont.Weight.Bold))
        self.lines_label = QLabel("0")
        self.lines_label.setFont(QFont("SimHei", 14, QFont.Weight.Bold))
        self.lines_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lines_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        
        info_panel_layout.addWidget(lines_label)
        info_panel_layout.addWidget(self.lines_label)
        
        # 等级显示
        level_label = QLabel("等级:")
        level_label.setFont(QFont("SimHei", 12, QFont.Weight.Bold))
        self.level_label = QLabel("1")
        self.level_label.setFont(QFont("SimHei", 14, QFont.Weight.Bold))
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.level_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        
        info_panel_layout.addWidget(level_label)
        info_panel_layout.addWidget(self.level_label)
        
        # 控制按钮区域
        control_layout = QVBoxLayout()
        control_layout.setSpacing(10)
        
        # 开始按钮
        self.start_button = QPushButton("开始游戏")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.clicked.connect(self.start_game)
        control_layout.addWidget(self.start_button)
        
        # 暂停按钮
        self.pause_button = QPushButton("暂停游戏")
        self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        self.pause_button.clicked.connect(self.pause_game)
        self.pause_button.setEnabled(False)
        control_layout.addWidget(self.pause_button)
        
        # 重启按钮
        self.restart_button = QPushButton("重新开始")
        self.restart_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.restart_button.clicked.connect(self.restart_game)
        self.restart_button.setEnabled(False)
        control_layout.addWidget(self.restart_button)
        
        # 移除音效按钮，游戏默认为静音状态
        
        info_panel_layout.addLayout(control_layout)
        info_panel_layout.addStretch()
        
        main_layout.addWidget(info_panel)
        
    def setup_styles(self):
        """设置游戏界面样式"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: SimHei, Microsoft YaHei, sans-serif;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                font-size: 14px;
                color: #333333;
            }
        """)
        
    def init_game(self):
        """初始化游戏参数"""
        # 游戏状态变量
        self.score = 0
        self.lines = 0
        self.level = 1
        self.high_score = 0
        self.load_high_score()
        
    def start_game(self):
        """开始游戏"""
        self.is_running = True
        self.game_canvas.start_game()
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.restart_button.setEnabled(True)
        
    def pause_game(self):
        """暂停游戏"""
        if self.is_running:
            self.is_running = False
            self.game_canvas.pause_game()
            self.pause_button.setText("继续游戏")
            self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.is_running = True
            self.game_canvas.resume_game()
            self.pause_button.setText("暂停游戏")
            self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            
    def restart_game(self):
        """重新开始游戏"""
        self.game_canvas.reset_game()
        self.is_running = True
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.pause_button.setText("暂停游戏")
        self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        self.update_score(0, 0)
        
    def game_over(self):
        """游戏结束处理"""
        self.is_running = False
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        
        # 检查是否打破最高记录
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
            self.high_score_label.setText(str(self.high_score))
            message = f"游戏结束！\n你的分数: {self.score}\n消除行数: {self.lines}\n恭喜你创造了新的最高记录！\n是否重新开始？"
        else:
            message = f"游戏结束！\n你的分数: {self.score}\n消除行数: {self.lines}\n当前最高记录: {self.high_score}\n是否重新开始？"
        
        # 显示游戏结束对话框
        reply = QMessageBox.question(
            self,
            "游戏结束",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.restart_game()
    
    def load_high_score(self):
        """加载最高分记录"""
        try:
            import pickle
            if os.path.exists(TETRIS_HIGH_SCORE_FILE):
                with open(TETRIS_HIGH_SCORE_FILE, 'rb') as f:
                    self.high_score = pickle.load(f)
                    self.high_score_label.setText(str(self.high_score))
        except Exception as e:
            print(f"加载最高分失败: {e}")
            logger.error(f"加载俄罗斯方块最高分失败: {e}")
            self.high_score = 0
    
    def save_high_score(self):
        """保存最高分记录"""
        try:
            import pickle
            # 确保配置目录存在
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            with open(TETRIS_HIGH_SCORE_FILE, 'wb') as f:
                pickle.dump(self.high_score, f)
        except Exception as e:
            print(f"保存最高分失败: {e}")
            logger.error(f"保存俄罗斯方块最高分失败: {e}")
            
    def update_score(self, score, lines):
        """更新分数和消除行数显示"""
        self.score = score
        self.lines = lines
        self.level = 1 + self.lines // 10  # 每消除10行升1级
        
        self.score_label.setText(str(self.score))
        self.lines_label.setText(str(self.lines))
        self.level_label.setText(str(self.level))
        
        # 更新游戏速度
        self.game_canvas.update_speed(self.level)
        
    def update_next_block_preview(self, block_type):
        """更新下一个方块预览"""
        # 创建预览画布
        preview_pixmap = QPixmap(100, 100)
        preview_pixmap.fill(QColor(240, 240, 240))
        
        painter = QPainter(preview_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制下一个方块预览
        block_size = 20
        x_offset = 40
        y_offset = 40
        
        # 获取方块形状和颜色
        shape, color = self.game_canvas.get_block_info(block_type)
        
        # 计算方块预览位置偏移
        offset_x = (len(shape[0]) - 1) * block_size // 2
        offset_y = (len(shape) - 1) * block_size // 2
        
        # 绘制方块
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    rect = QRect(
                        x_offset + j * block_size - offset_x,
                        y_offset + i * block_size - offset_y,
                        block_size - 2,
                        block_size - 2
                    )
                    painter.fillRect(rect, color)
                    painter.drawRect(rect)
        
        painter.end()
        
        # 设置预览图像
        self.next_block_preview.setPixmap(preview_pixmap)
        
    def toggle_sound(self):
        """切换音效开关"""
        self.sound_enabled = not self.sound_enabled
        if self.sound_enabled:
            self.sound_button.setText("关闭音效")
            self.sound_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolume))
        else:
            self.sound_button.setText("开启音效")
            self.sound_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaVolumeMuted))
            
    def center_window(self):
        """将窗口居中显示"""
        screen = self.screen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, 
                  (screen.height() - size.height()) // 2)
        
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if self.is_running:
            if event.key() == Qt.Key.Key_Left:
                self.game_canvas.move_left()
            elif event.key() == Qt.Key.Key_Right:
                self.game_canvas.move_right()
            elif event.key() == Qt.Key.Key_Down:
                self.game_canvas.move_down()
            elif event.key() == Qt.Key.Key_Up:
                self.game_canvas.rotate_block()
            elif event.key() == Qt.Key.Key_Space:
                self.game_canvas.drop_block()
        elif event.key() == Qt.Key.Key_Space:
            # 游戏暂停或结束状态下，空格键开始或继续游戏
            if self.start_button.isEnabled():
                self.start_game()
            else:
                self.pause_game()
        elif event.key() == Qt.Key.Key_Escape:
            # ESC键退出游戏
            self.close()
        elif event.key() == Qt.Key.Key_P:
            # P键暂停/继续游戏
            if self.is_running or not self.start_button.isEnabled():
                self.pause_game()
        elif event.key() == Qt.Key.Key_R:
            # R键重新开始游戏
            self.restart_game()
            
        # 不再将事件传播给父类，防止键盘事件冲突
        # super().keyPressEvent(event)
        
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 释放键盘捕获
        self.releaseKeyboard()
        # 调用父类的closeEvent以确保正常关闭流程
        super().closeEvent(event)

class TetrisGameCanvas(QWidget):
    """
    游戏画布类
    负责绘制游戏场景、方块，并处理游戏逻辑。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("background-color: #ffffff;")
        
        # 游戏参数
        self.grid_width = 10  # 游戏网格宽度
        self.grid_height = 20  # 游戏网格高度
        self.cell_size = 20    # 单元格大小（已从25缩小到20）
        
        # 方块定义（7种标准俄罗斯方块）
        self.blocks = {
            'I': [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            'J': [
                [1, 0, 0],
                [1, 1, 1],
                [0, 0, 0]
            ],
            'L': [
                [0, 0, 1],
                [1, 1, 1],
                [0, 0, 0]
            ],
            'O': [
                [1, 1],
                [1, 1]
            ],
            'S': [
                [0, 1, 1],
                [1, 1, 0],
                [0, 0, 0]
            ],
            'T': [
                [0, 1, 0],
                [1, 1, 1],
                [0, 0, 0]
            ],
            'Z': [
                [1, 1, 0],
                [0, 1, 1],
                [0, 0, 0]
            ]
        }
        
        # 方块颜色
        self.block_colors = {
            'I': QColor(0, 255, 255),    # 青色
            'J': QColor(0, 0, 255),      # 蓝色
            'L': QColor(255, 165, 0),    # 橙色
            'O': QColor(255, 255, 0),    # 黄色
            'S': QColor(0, 255, 0),      # 绿色
            'T': QColor(128, 0, 128),    # 紫色
            'Z': QColor(255, 0, 0)       # 红色
        }
        
        # 创建定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        self.game_speed = 1000  # 初始速度（毫秒）
        
        # 注意：不再在__init__中调用reset_game()，而是由TetrisGame在所有UI组件创建完成后调用
    
    def initialize_game(self):
        """初始化游戏状态，由TetrisGame在所有UI组件创建完成后调用"""
        self.reset_game()
        
    def reset_game(self):
        """重置游戏状态"""
        # 初始化游戏网格（0表示空，1-7表示不同颜色的方块）
        self.grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # 初始化当前方块和下一个方块
        self.current_block = None
        self.current_block_type = None
        self.current_block_x = 0
        self.current_block_y = 0
        self.next_block_type = random.choice(list(self.blocks.keys()))
        
        # 初始化游戏状态
        self.score = 0
        self.lines_cleared = 0
        
        # 生成第一个方块
        self.generate_new_block()
        
        # 更新UI
        self.update()
        
    def start_game(self):
        """开始游戏"""
        self.reset_game()
        self.timer.start(self.game_speed)
        
    def pause_game(self):
        """暂停游戏"""
        self.timer.stop()
        
    def resume_game(self):
        """继续游戏"""
        self.timer.start(self.game_speed)
        
    def update_speed(self, level):
        """根据等级更新游戏速度"""
        # 等级越高，速度越快（最小100毫秒）
        new_speed = max(100, 1000 - (level - 1) * 100)
        if self.timer.isActive():
            self.timer.stop()
            self.timer.start(new_speed)
        self.game_speed = new_speed
        
    def generate_new_block(self):
        """生成新方块"""
        # 设置当前方块为下一个方块
        self.current_block_type = self.next_block_type
        self.current_block = self.blocks[self.current_block_type]
        
        # 生成新的下一个方块
        self.next_block_type = random.choice(list(self.blocks.keys()))
        
        # 设置方块初始位置（居中）
        self.current_block_x = (self.grid_width - len(self.current_block[0])) // 2
        self.current_block_y = 0
        
        # 更新下一个方块预览
        if hasattr(self.parent, 'update_next_block_preview'):
            self.parent.update_next_block_preview(self.next_block_type)
        
        # 检查游戏是否结束（新方块无法放置）
        if not self.is_valid_position(self.current_block, self.current_block_x, self.current_block_y):
            self.timer.stop()
            if hasattr(self.parent, 'game_over'):
                self.parent.game_over()
        
    def move_left(self):
        """向左移动方块"""
        if self.is_valid_position(self.current_block, self.current_block_x - 1, self.current_block_y):
            self.current_block_x -= 1
            self.update()
        
    def move_right(self):
        """向右移动方块"""
        if self.is_valid_position(self.current_block, self.current_block_x + 1, self.current_block_y):
            self.current_block_x += 1
            self.update()
        
    def move_down(self):
        """向下移动方块"""
        if self.is_valid_position(self.current_block, self.current_block_x, self.current_block_y + 1):
            self.current_block_y += 1
            self.score += 1  # 下移得分
            self.update_score()
            self.update()
        else:
            # 方块无法继续下移，固定到网格
            self.fix_block()
            
    def rotate_block(self):
        """旋转方块"""
        # 旋转方块（矩阵转置）
        rotated_block = list(zip(*self.current_block[::-1]))
        rotated_block = [list(row) for row in rotated_block]
        
        # 检查旋转后的位置是否有效
        if self.is_valid_position(rotated_block, self.current_block_x, self.current_block_y):
            self.current_block = rotated_block
            self.update()
        
    def drop_block(self):
        """快速下落方块"""
        drop_distance = 0
        while self.is_valid_position(self.current_block, self.current_block_x, self.current_block_y + 1):
            self.current_block_y += 1
            drop_distance += 1
        
        # 快速下落得分（每格加2分）
        self.score += drop_distance * 2
        self.update_score()
        
        # 固定方块
        self.fix_block()
        
    def is_valid_position(self, block, x, y):
        """检查方块位置是否有效"""
        for i, row in enumerate(block):
            for j, cell in enumerate(row):
                if cell:
                    # 检查是否超出边界
                    if (x + j < 0 or x + j >= self.grid_width or 
                        y + i >= self.grid_height):
                        return False
                    # 检查是否与已有方块重叠
                    if y + i >= 0 and self.grid[y + i][x + j] != 0:
                        return False
        return True
        
    def fix_block(self):
        """将方块固定到网格上"""
        # 优化：直接使用字典映射方块类型到索引，避免列表转换和索引查找
        block_type_to_index = {'I': 1, 'J': 2, 'L': 3, 'O': 4, 'S': 5, 'T': 6, 'Z': 7}
        block_index = block_type_to_index[self.current_block_type]
        
        # 优化：计算一次偏移量，避免重复计算
        block_y_offset = self.current_block_y
        block_x_offset = self.current_block_x
        
        # 将方块添加到网格
        for i, row in enumerate(self.current_block):
            grid_y = block_y_offset + i
            if grid_y < 0:
                continue  # 跳过屏幕外的行
            
            for j, cell in enumerate(row):
                if cell:
                    grid_x = block_x_offset + j
                    self.grid[grid_y][grid_x] = block_index
        
        # 检查并消除已满的行
        self.clear_full_lines()
        
        # 生成新方块
        self.generate_new_block()
        
        # 更新UI
        self.update()
        
    def clear_full_lines(self):
        """消除已满的行"""
        # 优化：直接在原列表上操作，避免创建新列表
        i = self.grid_height - 1
        lines_cleared = 0
        
        # 从底部向上检查行
        while i >= 0:
            if all(cell != 0 for cell in self.grid[i]):
                # 发现满行，移除并在顶部添加空行
                del self.grid[i]
                self.grid.insert(0, [0 for _ in range(self.grid_width)])
                lines_cleared += 1
                # 不移除i，继续检查新移动到i位置的行
            else:
                i -= 1
        
        if lines_cleared > 0:
            # 计算得分（单行100分，两行300分，三行500分，四行800分）
            if lines_cleared == 1:
                self.score += 100
            elif lines_cleared == 2:
                self.score += 300
            elif lines_cleared == 3:
                self.score += 500
            elif lines_cleared >= 4:
                self.score += 800
            
            # 更新消除行数
            self.lines_cleared += lines_cleared
            
            # 更新分数显示
            self.update_score()
            
    def update_score(self):
        """更新分数显示并根据等级调整游戏速度"""
        # 根据消除的行数计算等级（每消除10行提升一级）
        level = (self.lines_cleared // 10) + 1
        
        # 更新游戏速度
        self.update_speed(level)
        
        # 更新UI显示
        if hasattr(self.parent, 'update_score'):
            self.parent.update_score(self.score, self.lines_cleared)
            
    def get_block_info(self, block_type):
        """获取方块信息（形状和颜色）"""
        return self.blocks[block_type], self.block_colors[block_type]
        
    def update_game(self):
        """更新游戏状态"""
        self.move_down()
        
    def paintEvent(self, event):
        """绘制游戏画面"""
        painter = QPainter(self)
        # 禁用抗锯齿以提高性能
        # painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 计算游戏区域位置（居中）
        game_width = self.grid_width * self.cell_size
        game_height = self.grid_height * self.cell_size
        x_offset = (self.width() - game_width) // 2
        y_offset = (self.height() - game_height) // 2
        
        # 绘制游戏区域边框
        border_rect = QRect(x_offset - 5, y_offset - 5, game_width + 10, game_height + 10)
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawRect(border_rect)
        
        # 填充游戏区域背景
        painter.fillRect(QRect(x_offset, y_offset, game_width, game_height), QColor(250, 250, 250))
        
        # 绘制网格线
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        # 绘制垂直线
        for x in range(self.grid_width + 1):
            painter.drawLine(x_offset + x * self.cell_size, y_offset, x_offset + x * self.cell_size, y_offset + game_height)
        # 绘制水平线
        for y in range(self.grid_height + 1):
            painter.drawLine(x_offset, y_offset + y * self.cell_size, x_offset + game_width, y_offset + y * self.cell_size)
        
        # 绘制已固定的方块
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        for i, row in enumerate(self.grid):
            for j, cell in enumerate(row):
                if cell != 0:
                    # 获取方块颜色（优化：直接使用索引而不是list操作）
                    block_type = ['I', 'J', 'L', 'O', 'S', 'T', 'Z'][cell - 1]
                    color = self.block_colors[block_type]
                    
                    # 绘制方块
                    rect = QRect(
                        x_offset + j * self.cell_size + 1,
                        y_offset + i * self.cell_size + 1,
                        self.cell_size - 2,
                        self.cell_size - 2
                    )
                    painter.fillRect(rect, color)
                    painter.drawRect(rect)
        
        # 绘制当前方块
        if self.current_block:
            # 获取当前方块颜色
            color = self.block_colors[self.current_block_type]
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            
            # 优化：计算偏移量，减少重复计算
            current_x_offset = x_offset + self.current_block_x * self.cell_size + 1
            current_y_offset = y_offset + self.current_block_y * self.cell_size + 1
            
            for i, row in enumerate(self.current_block):
                if (self.current_block_y + i) < 0:
                    continue  # 跳过屏幕外的行
                
                for j, cell in enumerate(row):
                    if cell:
                        # 绘制方块
                        rect = QRect(
                            current_x_offset + j * self.cell_size,
                            current_y_offset + i * self.cell_size,
                            self.cell_size - 2,
                            self.cell_size - 2
                        )
                        painter.fillRect(rect, color)
                        painter.drawRect(rect)
        
        # 如果游戏未开始或已暂停，显示提示信息
        if not self.timer.isActive():
            self.draw_game_hints(painter)
            
    def draw_game_hints(self, painter):
        """绘制游戏提示信息"""
        # 设置字体
        font = QFont("SimHei", 18, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 0))
        
        # 绘制提示文本
        if self.score == 0:
            # 游戏未开始
            hint_text = "按空格键开始游戏"
        else:
            # 游戏暂停
            hint_text = "游戏暂停，按空格键继续"
            
        # 计算文本位置
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(hint_text)
        text_height = metrics.height()
        x = (self.width() - text_width) // 2
        y = (self.height() - text_height) // 2
        
        painter.drawText(x, y, hint_text)
        
        # 绘制操作说明
        small_font = QFont("SimHei", 10)
        painter.setFont(small_font)
        instructions = "←: 左移  |  →: 右移  |  ↓: 下移  |  ↑: 旋转  |  空格: 快速下落"
        instructions_width = painter.fontMetrics().horizontalAdvance(instructions)
        instructions_x = (self.width() - instructions_width) // 2
        instructions_y = y + 40
        
        painter.drawText(instructions_x, instructions_y, instructions)
        
    def keyPressEvent(self, event):
        """处理键盘事件 - 直接传递给父窗口"""
        if self.parent and hasattr(self.parent, 'keyPressEvent'):
            self.parent.keyPressEvent(event)
        
    def resizeEvent(self, event):
        """处理窗口大小变化"""
        # 优化：减少重绘频率，仅在单元格大小发生显著变化时才更新
        old_cell_size = self.cell_size
        
        # 重新计算单元格大小以适应窗口
        available_width = self.width() - 20  # 留出一些边距
        available_height = self.height() - 20
        
        # 计算基于宽度的单元格大小
        width_based_size = available_width // self.grid_width
        
        # 计算基于高度的单元格大小
        height_based_size = available_height // self.grid_height
        
        # 选择较小的值以确保整个网格都能显示
        new_cell_size = min(width_based_size, height_based_size)
        
        # 设置最小单元格大小
        self.cell_size = max(15, new_cell_size)
        
        # 仅在单元格大小变化时重绘
        if abs(self.cell_size - old_cell_size) > 1:
            self.update()
        
        super().resizeEvent(event)


# ===== 2048游戏集成 =====
class Game2048(QMainWindow):
    """
    2048游戏主窗口类
    负责初始化游戏界面、处理用户输入和游戏逻辑
    """
    def __init__(self):
        super().__init__()
        # 设置中文字体支持
        self.font = QFont()
        self.font.setFamily("SimHei")
        
        # 游戏参数初始化
        self.init_game_parameters()
        
        # 初始化UI
        self.init_ui()
        
        # 初始化游戏状态
        self.reset_game()
    
    def init_game_parameters(self):
        """初始化游戏的各项参数"""
        # 游戏窗口尺寸
        self.width = 500
        self.height = 600
        
        # 游戏网格大小
        self.grid_size = 4
        
        # 单元格大小和边距
        self.cell_size = 100
        self.cell_margin = 10
        
        # 游戏状态标志
        self.game_over = False
        self.game_won = False
        
        # 分数和最高分
        self.score = 0
        self.high_score = 0
        
        # 尝试加载最高分
        self.load_high_score()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和尺寸
        self.setWindowTitle('2048游戏_designed_by_wwq')
        self.setGeometry(100, 100, self.width, self.height)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建垂直布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建游戏标题和分数显示区域
        title_layout = QHBoxLayout()
        main_layout.addLayout(title_layout)
        
        # 游戏标题
        title_label = QLabel('2048')
        title_label.setFont(self.font)
        title_label.setStyleSheet("font-size: 40px; font-weight: bold;")
        title_layout.addWidget(title_label)
        
        # 分数和最高分显示框
        score_layout = QVBoxLayout()
        
        # 当前分数
        self.score_label = QLabel(f'分数\n{self.score}')
        self.score_label.setFont(self.font)
        self.score_label.setStyleSheet("background-color: #bbada0; color: white; padding: 10px; border-radius: 5px; font-weight: bold;")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.score_label)
        
        # 最高分
        self.high_score_label = QLabel(f'最高分\n{self.high_score}')
        self.high_score_label.setFont(self.font)
        self.high_score_label.setStyleSheet("background-color: #bbada0; color: white; padding: 10px; border-radius: 5px; font-weight: bold;")
        self.high_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.high_score_label)
        
        title_layout.addLayout(score_layout)
        
        # 创建控制按钮区域
        control_layout = QHBoxLayout()
        main_layout.addLayout(control_layout)
        
        # 创建新游戏按钮
        self.new_game_button = QPushButton('新游戏')
        self.new_game_button.setFont(self.font)
        self.new_game_button.setStyleSheet("background-color: #8f7a66; color: white; padding: 10px; border-radius: 5px;")
        self.new_game_button.clicked.connect(self.reset_game)
        control_layout.addWidget(self.new_game_button)
        
        # 创建撤销按钮
        self.undo_button = QPushButton('撤销')
        self.undo_button.setFont(self.font)
        self.undo_button.setStyleSheet("background-color: #8f7a66; color: white; padding: 10px; border-radius: 5px;")
        self.undo_button.clicked.connect(self.undo_move)
        self.undo_button.setEnabled(False)
        control_layout.addWidget(self.undo_button)
        
        # 创建游戏说明标签
        self.instruction_label = QLabel('使用方向键或WASD移动方块，相同数字的方块会合并。尝试得到2048！')
        self.instruction_label.setFont(self.font)
        self.instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_label.setWordWrap(True)
        main_layout.addWidget(self.instruction_label)
        
        # 创建游戏网格容器
        grid_container = QWidget()
        grid_container.setStyleSheet("background-color: #bbada0; padding: 10px; border-radius: 10px;")
        main_layout.addWidget(grid_container)
        
        # 创建游戏网格布局
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(self.cell_margin)
        
        # 创建游戏单元格
        self.cells = []
        for i in range(self.grid_size):
            row = []
            for j in range(self.grid_size):
                cell = QLabel('')
                cell.setFont(self.font)
                cell.setStyleSheet("background-color: #cdc1b4; color: #776e65; border-radius: 5px;")
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setFixedSize(self.cell_size, self.cell_size)
                self.grid_layout.addWidget(cell, i, j)
                row.append(cell)
            self.cells.append(row)
        
        # 显示窗口
        self.show()
    
    def reset_game(self):
        """重置游戏状态"""
        # 初始化游戏网格
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # 游戏历史记录，用于撤销功能
        self.history = []
        
        # 重置游戏状态标志
        self.game_over = False
        self.game_won = False
        
        # 重置分数
        self.score = 0
        self.update_score_label()
        
        # 添加两个初始数字
        self.add_new_number()
        self.add_new_number()
        
        # 更新游戏界面
        self.update_grid()
        
        # 更新撤销按钮状态
        self.undo_button.setEnabled(False)
    
    def add_new_number(self):
        """在随机位置添加新数字（2或4）"""
        # 查找所有空单元格
        empty_cells = []
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.grid[i][j] == 0:
                    empty_cells.append((i, j))
        
        # 如果有空单元格，随机选择一个位置添加数字
        if empty_cells:
            i, j = random.choice(empty_cells)
            # 90%的概率生成2，10%的概率生成4
            self.grid[i][j] = 2 if random.random() < 0.9 else 4
    
    def update_grid(self):
        """更新游戏网格的显示"""
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                value = self.grid[i][j]
                cell = self.cells[i][j]
                
                # 设置单元格文本
                if value == 0:
                    cell.setText('')
                    # 确保空单元格显示正确的背景色
                    cell.setStyleSheet("background-color: #cdc1b4; color: #776e65; border-radius: 5px;")
                else:
                    cell.setText(str(value))
                    
                    # 根据数值设置不同的字体大小
                    if value < 100:
                        cell.setStyleSheet(self.get_cell_style(value, 36))
                    elif value < 1000:
                        cell.setStyleSheet(self.get_cell_style(value, 30))
                    else:
                        cell.setStyleSheet(self.get_cell_style(value, 24))
        
        # 强制刷新UI，确保立即显示最新状态
        self.update()
        QApplication.processEvents()
        
        # 检查游戏状态
        self.check_game_state()
        
        # 更新撤销按钮状态
        self.undo_button.setEnabled(len(self.history) > 0)
    
    def get_cell_style(self, value, font_size):
        """根据数值获取单元格的样式"""
        # 根据数值设置不同的背景颜色
        colors = {
            2: "#eee4da",
            4: "#ede0c8",
            8: "#f2b179",
            16: "#f59563",
            32: "#f67c5f",
            64: "#f65e3b",
            128: "#edcf72",
            256: "#edcc61",
            512: "#edc850",
            1024: "#edc53f",
            2048: "#edc22e"
        }
        
        # 获取背景颜色，如果数值大于2048，则使用2048的颜色
        bg_color = colors.get(value, colors[2048])
        
        # 根据数值设置不同的文字颜色
        text_color = "#776e65" if value <= 4 else "white"
        
        # 返回CSS样式
        return f"background-color: {bg_color}; color: {text_color}; border-radius: 5px; font-size: {font_size}px; font-weight: bold;"
    
    def keyPressEvent(self, event):
        """处理键盘事件，控制方块移动"""
        # 如果游戏已结束，则忽略键盘事件
        if self.game_over:
            return
        
        # 保存当前游戏状态，用于撤销功能
        self.save_state()
        
        # 记录是否有移动发生
        moved = False
        
        # 处理方向键
        key = event.key()
        if key == Qt.Key.Key_Up or key == Qt.Key.Key_W:
            moved = self.move_up()
        elif key == Qt.Key.Key_Down or key == Qt.Key.Key_S:
            moved = self.move_down()
        elif key == Qt.Key.Key_Left or key == Qt.Key.Key_A:
            moved = self.move_left()
        elif key == Qt.Key.Key_Right or key == Qt.Key.Key_D:
            moved = self.move_right()
        
        # 如果有移动发生，则添加新数字并更新游戏界面
        if moved:
            self.add_new_number()
            self.update_grid()
    
    def closeEvent(self, event):
        """处理窗口关闭事件，确保正确发出destroyed信号"""
        # 调用父类的closeEvent以确保正常关闭流程
        super().closeEvent(event)
    
    def move_up(self):
        """向上移动方块"""
        moved = False
        # 创建一个临时网格来跟踪是否已经合并过
        merged = [[False for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # 遍历每一列
        for j in range(self.grid_size):
            # 遍历每一行，从第二行开始
            for i in range(1, self.grid_size):
                # 如果当前单元格有数字
                if self.grid[i][j] != 0:
                    # 向上移动直到碰到边界或有数字的单元格
                    row = i
                    while row > 0 and self.grid[row - 1][j] == 0:
                        # 移动方块
                        self.grid[row - 1][j] = self.grid[row][j]
                        self.grid[row][j] = 0
                        row -= 1
                        moved = True
                    
                    # 检查是否可以合并，确保每个方块只合并一次
                    if row > 0 and self.grid[row - 1][j] == self.grid[row][j] and not merged[row - 1][j] and not merged[row][j]:
                        # 合并方块
                        self.grid[row - 1][j] *= 2
                        self.grid[row][j] = 0
                        # 标记已合并
                        merged[row - 1][j] = True
                        # 更新分数
                        self.score += self.grid[row - 1][j]
                        moved = True
        
        return moved
    
    def move_down(self):
        """向下移动方块"""
        moved = False
        # 创建一个临时网格来跟踪是否已经合并过
        merged = [[False for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # 遍历每一列
        for j in range(self.grid_size):
            # 遍历每一行，从倒数第二行开始
            for i in range(self.grid_size - 2, -1, -1):
                # 如果当前单元格有数字
                if self.grid[i][j] != 0:
                    # 向下移动直到碰到边界或有数字的单元格
                    row = i
                    while row < self.grid_size - 1 and self.grid[row + 1][j] == 0:
                        # 移动方块
                        self.grid[row + 1][j] = self.grid[row][j]
                        self.grid[row][j] = 0
                        row += 1
                        moved = True
                    
                    # 检查是否可以合并，确保每个方块只合并一次
                    if row < self.grid_size - 1 and self.grid[row + 1][j] == self.grid[row][j] and not merged[row + 1][j] and not merged[row][j]:
                        # 合并方块
                        self.grid[row + 1][j] *= 2
                        self.grid[row][j] = 0
                        # 标记已合并
                        merged[row + 1][j] = True
                        # 更新分数
                        self.score += self.grid[row + 1][j]
                        moved = True
        
        return moved
    
    def move_left(self):
        """向左移动方块"""
        moved = False
        # 创建一个临时网格来跟踪是否已经合并过
        merged = [[False for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # 遍历每一行
        for i in range(self.grid_size):
            # 遍历每一列，从第二列开始
            for j in range(1, self.grid_size):
                # 如果当前单元格有数字
                if self.grid[i][j] != 0:
                    # 向左移动直到碰到边界或有数字的单元格
                    col = j
                    while col > 0 and self.grid[i][col - 1] == 0:
                        # 移动方块
                        self.grid[i][col - 1] = self.grid[i][col]
                        self.grid[i][col] = 0
                        col -= 1
                        moved = True
                    
                    # 检查是否可以合并，确保每个方块只合并一次
                    if col > 0 and self.grid[i][col - 1] == self.grid[i][col] and not merged[i][col - 1] and not merged[i][col]:
                        # 合并方块
                        self.grid[i][col - 1] *= 2
                        self.grid[i][col] = 0
                        # 标记已合并
                        merged[i][col - 1] = True
                        # 更新分数
                        self.score += self.grid[i][col - 1]
                        moved = True
        
        return moved
    
    def move_right(self):
        """向右移动方块"""
        moved = False
        # 创建一个临时网格来跟踪是否已经合并过
        merged = [[False for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # 遍历每一行
        for i in range(self.grid_size):
            # 遍历每一列，从倒数第二列开始
            for j in range(self.grid_size - 2, -1, -1):
                # 如果当前单元格有数字
                if self.grid[i][j] != 0:
                    # 向右移动直到碰到边界或有数字的单元格
                    col = j
                    while col < self.grid_size - 1 and self.grid[i][col + 1] == 0:
                        # 移动方块
                        self.grid[i][col + 1] = self.grid[i][col]
                        self.grid[i][col] = 0
                        col += 1
                        moved = True
                    
                    # 检查是否可以合并，确保每个方块只合并一次
                    if col < self.grid_size - 1 and self.grid[i][col + 1] == self.grid[i][col] and not merged[i][col + 1] and not merged[i][col]:
                        # 合并方块
                        self.grid[i][col + 1] *= 2
                        self.grid[i][col] = 0
                        # 标记已合并
                        merged[i][col + 1] = True
                        # 更新分数
                        self.score += self.grid[i][col + 1]
                        moved = True
        
        return moved
    
    def save_state(self):
        """保存当前游戏状态，用于撤销功能"""
        # 深拷贝当前网格
        grid_copy = [row[:] for row in self.grid]
        # 保存当前分数
        score_copy = self.score
        # 添加到历史记录
        self.history.append((grid_copy, score_copy))
        # 限制历史记录长度，避免占用过多内存
        if len(self.history) > 10:
            self.history.pop(0)
    
    def undo_move(self):
        """撤销上一步操作"""
        # 如果有历史记录
        if self.history:
            # 恢复上一步的网格和分数
            self.grid, self.score = self.history.pop()
            # 更新分数显示
            self.update_score_label()
            # 更新游戏界面
            self.update_grid()
    
    def update_score_label(self):
        """更新分数显示"""
        self.score_label.setText(f'分数\n{self.score}')
        
        # 如果当前分数大于最高分，更新最高分
        if self.score > self.high_score:
            self.high_score = self.score
            self.high_score_label.setText(f'最高分\n{self.high_score}')
            # 保存最高分
            self.save_high_score()
    
    def save_high_score(self):
        """保存最高分到文件"""
        try:
            with open(GAME2048_HIGH_SCORE_FILE, 'w') as f:
                f.write(str(self.high_score))
        except Exception as e:
            # 如果保存失败，忽略错误
            pass
    
    def load_high_score(self):
        """从文件加载最高分"""
        try:
            with open(GAME2048_HIGH_SCORE_FILE, 'r') as f:
                self.high_score = int(f.read())
        except Exception as e:
            # 如果文件不存在或读取失败，使用默认值
            self.high_score = 0
    
    def check_game_state(self):
        """检查游戏状态（胜利或失败）"""
        # 检查是否胜利（是否有方块达到2048）
        if not self.game_won:
            for i in range(self.grid_size):
                for j in range(self.grid_size):
                    if self.grid[i][j] >= 2048:
                        self.game_won = True
                        # 显示胜利消息
                        QMessageBox.information(self, '游戏胜利！', '恭喜你达到了2048！\n继续游戏挑战更高分数吧！')
                        break
                if self.game_won:
                    break
        
        # 检查是否还有空单元格
        has_empty_cell = False
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.grid[i][j] == 0:
                    has_empty_cell = True
                    break
            if has_empty_cell:
                break
        
        # 如果没有空单元格，检查是否还能移动
        if not has_empty_cell:
            can_move = False
            
            # 检查横向是否有可合并的方块
            for i in range(self.grid_size):
                for j in range(self.grid_size - 1):
                    if self.grid[i][j] == self.grid[i][j + 1]:
                        can_move = True
                        break
                if can_move:
                    break
            
            # 如果横向没有可合并的方块，检查纵向
            if not can_move:
                for j in range(self.grid_size):
                    for i in range(self.grid_size - 1):
                        if self.grid[i][j] == self.grid[i + 1][j]:
                            can_move = True
                            break
                    if can_move:
                        break
            
            # 如果既没有空单元格，也不能移动，则游戏结束
            if not can_move:
                self.game_over = True
                # 显示游戏结束消息
                QMessageBox.information(self, '游戏结束', f'游戏结束！\n你的分数是: {self.score}\n是否开始新游戏？',
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
                
                # 如果用户选择开始新游戏
                if QMessageBox.question(self, '新游戏', '是否开始新游戏？') == QMessageBox.StandardButton.Yes:
                    self.reset_game()
    
    def closeEvent(self, event):
        """处理窗口关闭事件，确保正确发出destroyed信号"""
        # 调用父类的closeEvent以确保正常关闭流程
        super().closeEvent(event)
        # 窗口关闭后会自动触发destroyed信号
        
    def center_window(self):
        """将窗口显示在屏幕中央偏上位置"""
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        # 让窗口上移30像素，使视觉效果更好
        self.move((screen.width() - size.width()) // 2, 
                  ((screen.height() - size.height()) // 2) - 30)


# ===== 贪吃蛇游戏集成 =====
class SnakeGame(QMainWindow):
    """
    贪吃蛇游戏主窗口类
    负责初始化游戏界面、处理用户输入和游戏逻辑
    """
    def __init__(self):
        super().__init__()
        # 设置中文字体支持
        self.font = QFont()
        self.font.setFamily("SimHei")
        
        # 游戏参数初始化
        self.init_game_parameters()
        
        # 初始化UI
        self.init_ui()
        
        # 初始化游戏状态
        self.reset_game()
    
    def init_game_parameters(self):
        """\初始化游戏的各项参数"""
        # 游戏区域尺寸
        self.width = 800
        self.height = 600
        
        # 网格和蛇的大小
        self.grid_size = 20
        
        # 方向控制
        self.direction = Qt.Key.Key_Right
        self.next_direction = Qt.Key.Key_Right
        
        # 游戏速度（毫秒）
        self.game_speed = 150
        
        # 游戏状态标志
        self.game_started = False
        self.game_paused = False
        
        # 最高分数文件路径
        self.high_score_file = SNAKE_HIGH_SCORE_FILE
        self.high_score = 0
        
        # 加载最高分数
        self.load_high_score()
        
        # 初始化蛇头和蛇身图像
        self.init_snake_images()
        
        # 额外食物和炸弹相关参数
        self.extra_food = None
        self.extra_food_timer = 0
        self.extra_food_spawn_interval = random.randint(5, 10)  # 5-10次得分后生成额外食物
        self.extra_food_total_time = 33  # 额外食物总时间（约5秒，150ms/帧）
        self.extra_food_blink_time = 20  # 额外食物开始闪烁的时间（约3秒前）
        self.bomb = None
        self.bomb_spawn_probability = 0.3  # 30%的概率生成炸弹
        self.score_count = 0
        self.extra_bomb_count = 0  # 额外炸弹计数
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和尺寸
        self.setWindowTitle('贪吃蛇游戏_designed_by_wwq')
        self.setGeometry(0, 0, self.width, self.height)
        
        # 将窗口显示在屏幕中央
        self.center_window()
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建垂直布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建游戏画布
        self.game_canvas = GameCanvas(self)
        self.game_canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.game_canvas.keyPressEvent = self.keyPressEvent
        main_layout.addWidget(self.game_canvas, 1)
        
        # 创建水平布局用于放置分数和控制按钮
        control_layout = QHBoxLayout()
        main_layout.addLayout(control_layout)
        
        # 创建分数显示标签
        self.score_label = QLabel('分数: 0')
        self.score_label.setFont(self.font)
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(self.score_label, 1)
        
        # 创建最高分数显示标签
        self.high_score_label = QLabel(f'最高分: {self.high_score}')
        self.high_score_label.setFont(self.font)
        self.high_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(self.high_score_label, 1)
        
        # 创建开始按钮
        self.start_button = QPushButton('开始游戏')
        self.start_button.setFont(self.font)
        self.start_button.clicked.connect(self.start_game)
        control_layout.addWidget(self.start_button)
        
        # 创建暂停按钮
        self.pause_button = QPushButton('暂停')
        self.pause_button.setFont(self.font)
        self.pause_button.clicked.connect(self.pause_game)
        self.pause_button.setEnabled(False)
        control_layout.addWidget(self.pause_button)
        
        # 创建重新开始按钮
        self.restart_button = QPushButton('重新开始')
        self.restart_button.setFont(self.font)
        self.restart_button.clicked.connect(self.reset_game)
        self.restart_button.setEnabled(False)
        control_layout.addWidget(self.restart_button)
        
        # 创建游戏计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)
        
        # 显示窗口
        self.show()
        
    def center_window(self):
        """将窗口显示在屏幕中央偏上位置"""
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        # 让窗口上移30像素，使视觉效果更好
        self.move((screen.width() - size.width()) // 2, 
                  ((screen.height() - size.height()) // 2) - 30)
    
    def reset_game(self):
        """重置游戏状态"""
        # 重置蛇的位置和长度
        self.snake = [
            QPoint(10 * self.grid_size, 10 * self.grid_size),
            QPoint(9 * self.grid_size, 10 * self.grid_size),
            QPoint(8 * self.grid_size, 10 * self.grid_size)
        ]
        
        # 重置方向
        self.direction = Qt.Key.Key_Right
        self.next_direction = Qt.Key.Key_Right
        
        # 重置分数
        self.score = 0
        self.score_count = 0
        self.score_label.setText(f'分数: {self.score}')
        
        # 重置游戏速度
        self.game_speed = 150
        
        # 重置额外食物和炸弹
        self.extra_food = None
        self.extra_food_timer = 0
        self.bomb = None
        self.extra_food_spawn_interval = random.randint(5, 10)
        
        # 生成食物
        self.generate_food()
        
        # 更新UI状态
        self.game_started = False
        self.game_paused = False
        self.start_button.setText('开始游戏')
        self.start_button.setEnabled(True)
        self.pause_button.setText('暂停')
        self.pause_button.setEnabled(False)
        self.restart_button.setEnabled(False)
        
        # 停止计时器
        self.timer.stop()
        
        # 重绘游戏画布
        self.game_canvas.update()
        
    def load_high_score(self):
        """加载保存的最高分数"""
        try:
            if os.path.exists(self.high_score_file):
                with open(self.high_score_file, 'rb') as f:
                    self.high_score = pickle.load(f)
        except Exception as e:
            print(f"加载最高分失败: {e}")
            self.high_score = 0
    
    def save_high_score(self):
        """保存最高分数"""
        try:
            with open(self.high_score_file, 'wb') as f:
                pickle.dump(self.high_score, f)
        except Exception as e:
            print(f"保存最高分失败: {e}")
    
    def init_snake_images(self):
        """初始化蛇相关图形资源
        由于我们现在使用代码绘制蛇而不是图像，这个方法保留为兼容性
        """
        # 我们现在不再使用QPixmap来表示蛇，而是在绘制时直接使用QPainter
        # 保留这些变量以保持向后兼容性
        self.head_up = QPixmap(self.grid_size, self.grid_size)
        self.head_down = QPixmap(self.grid_size, self.grid_size)
        self.head_left = QPixmap(self.grid_size, self.grid_size)
        self.head_right = QPixmap(self.grid_size, self.grid_size)
        self.body = QPixmap(self.grid_size, self.grid_size)
        
        # 填充为透明色
        self.head_up.fill(Qt.GlobalColor.transparent)
        self.head_down.fill(Qt.GlobalColor.transparent)
        self.head_left.fill(Qt.GlobalColor.transparent)
        self.head_right.fill(Qt.GlobalColor.transparent)
        self.body.fill(Qt.GlobalColor.transparent)
    
    def create_head_image(self, direction):
        """创建不同方向的蛇头图像"""
        head = QPixmap(self.grid_size, self.grid_size)
        head.fill(QColor(0, 150, 0))  # 绿色头部
        
        # 在头部画上简单的眼睛
        painter = QPainter(head)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        
        if direction == 'up':
            painter.drawEllipse(4, 4, 4, 4)
            painter.drawEllipse(12, 4, 4, 4)
        elif direction == 'down':
            painter.drawEllipse(4, 12, 4, 4)
            painter.drawEllipse(12, 12, 4, 4)
        elif direction == 'left':
            painter.drawEllipse(4, 4, 4, 4)
            painter.drawEllipse(4, 12, 4, 4)
        elif direction == 'right':
            painter.drawEllipse(12, 4, 4, 4)
            painter.drawEllipse(12, 12, 4, 4)
        
        painter.end()
        return head
    
    def start_game(self):
        """开始或继续游戏"""
        if not self.game_started:
            self.game_started = True
            self.start_button.setText('继续')
            self.pause_button.setText('暂停')
            self.pause_button.setEnabled(True)
            self.restart_button.setEnabled(True)
        elif self.game_paused:
            self.game_paused = False
            self.start_button.setText('继续')
            self.pause_button.setText('暂停')
        
        # 启动计时器
        self.timer.start(self.game_speed)
        
        # 设置画布焦点
        self.game_canvas.setFocus()
    
    def pause_game(self):
        """暂停游戏"""
        if self.game_started and not self.game_paused:
            self.game_paused = True
            self.timer.stop()
            self.start_button.setText('继续')
            self.pause_button.setText('已暂停')
            # 立即重绘以显示暂停消息
            self.game_canvas.update()
    
    def generate_food(self):
        """在随机位置生成食物"""
        # 计算可用的网格数量（考虑边界）
        border = 20  # 边界宽度
        max_x = (self.width - border * 2 - self.grid_size) // self.grid_size
        max_y = (self.height - 100 - border * 2 - self.grid_size) // self.grid_size  # 减去控制区域的高度和边界
        
        # 生成不在蛇身上的随机位置
        while True:
            food_x = border + random.randint(1, max_x - 1) * self.grid_size
            food_y = border + random.randint(1, max_y - 1) * self.grid_size
            food_point = QPoint(food_x, food_y)
            
            # 检查食物是否生成在蛇身上
            if food_point not in self.snake:
                self.food = food_point
                break
                
        # 随机决定是否生成炸弹
        if random.random() < self.bomb_spawn_probability:
            self.generate_bomb()
    
    def closeEvent(self, event):
        """处理窗口关闭事件，确保正确发出destroyed信号"""
        # 调用父类的closeEvent以确保正常关闭流程
        super().closeEvent(event)
        
    def keyPressEvent(self, event):
        """处理键盘事件，控制蛇的移动方向"""
        key = event.key()
        
        # 如果游戏未开始，可以按空格键开始
        if not self.game_started and key == Qt.Key.Key_Space:
            self.start_game()
            return
        
        # 处理暂停/继续游戏
        if self.game_started and key == Qt.Key.Key_Space:
            if self.game_paused:
                # 继续游戏
                self.game_paused = False
                self.timer.start(self.game_speed)
                self.start_button.setText('继续')
                self.pause_button.setText('暂停')
                self.game_canvas.update()
            else:
                # 暂停游戏
                self.pause_game()
            return
        
        # 只有在游戏开始且未暂停时才处理方向键
        if self.game_started and not self.game_paused:
            # 确保不能直接反向移动
            if (key == Qt.Key.Key_Up and self.direction != Qt.Key.Key_Down) or\
               (key == Qt.Key.Key_Down and self.direction != Qt.Key.Key_Up) or\
               (key == Qt.Key.Key_Left and self.direction != Qt.Key.Key_Right) or\
               (key == Qt.Key.Key_Right and self.direction != Qt.Key.Key_Left):
                self.next_direction = key
    
    def update_game(self):
        """更新游戏状态"""
        if not self.game_paused and self.game_started:
            # 更新方向
            self.direction = self.next_direction
            
            # 获取蛇头位置
            head = self.snake[0]
            new_head = QPoint(head)
            
            # 根据方向移动蛇头
            if self.direction == Qt.Key.Key_Up:
                new_head.setY(head.y() - self.grid_size)
            elif self.direction == Qt.Key.Key_Down:
                new_head.setY(head.y() + self.grid_size)
            elif self.direction == Qt.Key.Key_Left:
                new_head.setX(head.x() - self.grid_size)
            elif self.direction == Qt.Key.Key_Right:
                new_head.setX(head.x() + self.grid_size)
            
            # 检查是否撞到边界
            border_width = 20  # 边界宽度，与绘制逻辑保持一致
            
            # 获取游戏画布的实际尺寸用于边界判定
            canvas_width = self.game_canvas.width()
            canvas_height = self.game_canvas.height()
            
            # 统一边界判定逻辑，与绘制逻辑完全匹配
            # 右侧边界 = 画布宽度 - 边界宽度
            right_boundary = canvas_width - border_width
            # 底部边界 = 画布高度 - 边界宽度
            bottom_boundary = canvas_height - border_width
            
            # 检查蛇头是否完全超出边界
            # 右侧边界需要考虑蛇头的宽度，允许蛇头部分进入边界
            if (new_head.x() < border_width or new_head.x() + self.grid_size > right_boundary or
                new_head.y() < border_width or new_head.y() > bottom_boundary):
                self.game_over()
                return
            
            # 检查是否撞到自己
            if new_head in self.snake:
                self.game_over()
                return
            
            # 检查是否吃到炸弹
            if self.bomb and new_head == self.bomb:
                self.game_over()
                return
            
            # 将新的头部添加到蛇的身体
            self.snake.insert(0, new_head)
            
            # 检查是否吃到食物
            food_eaten = False
            if new_head == self.food:
                # 增加分数
                self.score += 10
                self.score_count += 1
                self.score_label.setText(f'分数: {self.score}')
                food_eaten = True
                
                # 生成新的食物
                self.generate_food()
                
                # 生成炸弹（每次得分都生成）
                self.generate_bomb()
                
                # 检查是否有额外炸弹需要生成
                if self.extra_bomb_count > 0:
                    self.generate_bomb()
                    self.extra_bomb_count -= 1
                
                # 检查是否需要生成额外食物
                if self.score_count % self.extra_food_spawn_interval == 0:
                    self.generate_extra_food()
                    # 重新随机设置下一次生成额外食物的间隔
                    self.extra_food_spawn_interval = random.randint(5, 10)
                
                # 随着分数增加，提高游戏速度
                if self.score % 50 == 0 and self.game_speed > 50:
                    self.game_speed -= 10
                    self.timer.setInterval(self.game_speed)
            # 检查是否吃到额外食物
            elif self.extra_food and new_head == self.extra_food:
                # 增加额外分数
                self.score += 50
                self.score_count += 1
                self.score_label.setText(f'分数: {self.score}')
                self.extra_food = None
                self.extra_food_timer = 0
                food_eaten = True
                
                # 吃了额外食物后额外增加一个炸弹，直到下次得分
                self.extra_bomb_count += 1
                
                # 生成炸弹
                self.generate_bomb()
            
            # 如果没有吃到任何食物，移除尾部
            if not food_eaten:
                self.snake.pop()
            
            # 更新额外食物计时器
            if self.extra_food:
                self.extra_food_timer += 1
                # 5秒后（假设150ms每帧，约33帧）移除额外食物
                if self.extra_food_timer >= self.extra_food_total_time:
                    self.extra_food = None
                    self.extra_food_timer = 0
            
            # 重绘游戏画布
            self.game_canvas.update()
            
    def generate_extra_food(self):
        """生成额外食物"""
        # 计算可用的网格数量（考虑边界）
        border = 20  # 边界宽度
        max_x = (self.width - border * 2 - self.grid_size) // self.grid_size
        max_y = (self.height - 100 - border * 2 - self.grid_size) // self.grid_size
        
        # 生成不在蛇身上且不在普通食物位置的随机位置
        while True:
            food_x = border + random.randint(1, max_x - 1) * self.grid_size
            food_y = border + random.randint(1, max_y - 1) * self.grid_size
            food_point = QPoint(food_x, food_y)
            
            # 检查额外食物是否生成在蛇身上或普通食物位置
            if (food_point not in self.snake and 
                food_point != self.food and 
                (not self.bomb or food_point != self.bomb)):
                self.extra_food = food_point
                self.extra_food_timer = 0
                break
                
    def generate_bomb(self):
        """生成炸弹"""
        # 计算可用的网格数量（考虑边界）
        border = 20  # 边界宽度
        max_x = (self.width - border * 2 - self.grid_size) // self.grid_size
        max_y = (self.height - 100 - border * 2 - self.grid_size) // self.grid_size
        
        # 生成不在蛇身上、不在食物位置且不出现在蛇头周围的随机位置
        attempts = 0
        max_attempts = 100  # 防止无限循环
        
        while attempts < max_attempts:
            attempts += 1
            bomb_x = border + random.randint(1, max_x - 1) * self.grid_size
            bomb_y = border + random.randint(1, max_y - 1) * self.grid_size
            bomb_point = QPoint(bomb_x, bomb_y)
            
            # 检查炸弹是否生成在蛇身上或食物位置
            if (bomb_point not in self.snake and 
                bomb_point != self.food and 
                (not self.extra_food or bomb_point != self.extra_food)):
                
                # 检查炸弹是否出现在蛇头周围（2个网格范围内）
                head = self.snake[0]
                head_area = QRect(head.x() - self.grid_size * 2, head.y() - self.grid_size * 2, 
                                self.grid_size * 5, self.grid_size * 5)
                
                if not head_area.contains(bomb_point):
                    self.bomb = bomb_point
                    return
        
        # 如果尝试了多次都没找到合适的位置，就找一个不在蛇身上的位置
        if self.bomb is None or attempts >= max_attempts:
            while True:
                bomb_x = border + random.randint(1, max_x - 1) * self.grid_size
                bomb_y = border + random.randint(1, max_y - 1) * self.grid_size
                bomb_point = QPoint(bomb_x, bomb_y)
                
                if bomb_point not in self.snake:
                    self.bomb = bomb_point
                    break
    
    def game_over(self):
        """游戏结束处理"""
        # 停止计时器
        self.timer.stop()
        
        # 检查是否打破最高记录
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
            self.high_score_label.setText(f'最高分: {self.high_score}')
            message = f'游戏结束！\n你的分数是: {self.score}\n恭喜你创造了新的最高记录！'
        else:
            message = f'游戏结束！\n你的分数是: {self.score}\n当前最高记录是: {self.high_score}'
        
        # 显示游戏结束消息
        QMessageBox.information(self, '游戏结束', message)
        
        # 重置游戏状态
        self.reset_game()

class GameCanvas(QWidget):
    """
    游戏画布类
    负责绘制游戏元素（蛇、食物、网格等）
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("background-color: #e0f7fa;")  # 使用浅蓝色背景
    
    def paintEvent(self, event):
        """绘制游戏元素"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # 启用抗锯齿，使图形更圆润
        
        # 绘制游戏边界
        self.draw_border(painter)
        
        # 绘制蛇
        self.draw_snake(painter)
        
        # 绘制食物
        self.draw_food(painter)
        
        # 绘制额外食物（如果存在）
        if self.parent.extra_food:
            self.draw_extra_food(painter)
        
        # 绘制炸弹（如果存在）
        if self.parent.bomb:
            self.draw_bomb(painter)
        
        # 如果游戏未开始，显示提示信息
        if not self.parent.game_started:
            self.draw_start_message(painter)
        elif self.parent.game_paused:
            self.draw_pause_message(painter)
    
    def draw_border(self, painter):
        """绘制游戏边界，再次微微下调底边位置"""
        border_width = 20
        pen = QPen(QColor(0, 150, 136), 4, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        # 绘制外层边界线，再次微微下调底边
        adjusted_height = self.height() - border_width * 2 + 8
        rect = QRect(border_width, border_width, 
                    self.width() - border_width * 2, 
                    adjusted_height)
        painter.drawRect(rect)
    
    def draw_grid(self, painter):
        """绘制游戏网格（未使用）"""
        pen = QPen(QColor(200, 200, 200), 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        # 绘制垂直线
        for x in range(0, self.width(), self.parent.grid_size):
            painter.drawLine(x, 0, x, self.height())
        
        # 绘制水平线
        for y in range(0, self.height(), self.parent.grid_size):
            painter.drawLine(0, y, self.width(), y)
    
    def draw_snake(self, painter):
        """绘制蛇（圆润的蛇身）"""
        # 绘制蛇身
        for i in range(1, len(self.parent.snake)):
            body_part = self.parent.snake[i]
            
            # 创建渐变画笔，使蛇身更有立体感
            gradient = QRadialGradient(
                QPointF(body_part.x() + self.parent.grid_size / 2, 
                        body_part.y() + self.parent.grid_size / 2),
                self.parent.grid_size / 2,
                QPointF(body_part.x() + self.parent.grid_size / 3, 
                        body_part.y() + self.parent.grid_size / 3)
            )
            gradient.setColorAt(0, QColor(76, 175, 80))  # 浅绿色
            gradient.setColorAt(1, QColor(56, 142, 60))  # 深绿色
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(27, 94, 32), 1))  # 更深的绿色边框
            
            # 绘制圆角矩形，使蛇身变圆润
            rect = QRectF(body_part.x(), body_part.y(), 
                          self.parent.grid_size, self.parent.grid_size)
            painter.drawRoundedRect(rect, 5, 5)
            
        # 绘制蛇头（放在最后，确保在最上层）
        head = self.parent.snake[0]
        
        # 创建蛇头渐变
        head_gradient = QRadialGradient(
            QPointF(head.x() + self.parent.grid_size / 2, 
                    head.y() + self.parent.grid_size / 2),
            self.parent.grid_size / 2,
            QPointF(head.x() + self.parent.grid_size / 3, 
                    head.y() + self.parent.grid_size / 3)
        )
        head_gradient.setColorAt(0, QColor(139, 195, 74))  # 更亮的绿色
        head_gradient.setColorAt(1, QColor(76, 175, 80))  # 标准绿色
        painter.setBrush(QBrush(head_gradient))
        painter.setPen(QPen(QColor(27, 94, 32), 2))  # 粗边框
        
        # 绘制圆角矩形作为蛇头
        head_rect = QRectF(head.x(), head.y(), 
                          self.parent.grid_size, self.parent.grid_size)
        painter.drawRoundedRect(head_rect, 6, 6)
        
        # 根据方向绘制蛇的眼睛
        eye_size = 3
        if self.parent.direction == Qt.Key.Key_Up:
            # 向上方向的眼睛
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            painter.drawEllipse(head.x() + 4, head.y() + 4, eye_size, eye_size)
            painter.drawEllipse(head.x() + self.parent.grid_size - 7, head.y() + 4, eye_size, eye_size)
        elif self.parent.direction == Qt.Key.Key_Down:
            # 向下方向的眼睛
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            painter.drawEllipse(head.x() + 4, head.y() + self.parent.grid_size - 7, eye_size, eye_size)
            painter.drawEllipse(head.x() + self.parent.grid_size - 7, head.y() + self.parent.grid_size - 7, eye_size, eye_size)
        elif self.parent.direction == Qt.Key.Key_Left:
            # 向左方向的眼睛
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            painter.drawEllipse(head.x() + 4, head.y() + 4, eye_size, eye_size)
            painter.drawEllipse(head.x() + 4, head.y() + self.parent.grid_size - 7, eye_size, eye_size)
        else:  # Key_Right
            # 向右方向的眼睛
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            painter.drawEllipse(head.x() + self.parent.grid_size - 7, head.y() + 4, eye_size, eye_size)
            painter.drawEllipse(head.x() + self.parent.grid_size - 7, head.y() + self.parent.grid_size - 7, eye_size, eye_size)
            
    def draw_food(self, painter):
        """绘制美化的食物"""
        # 创建食物的渐变效果
        food_gradient = QRadialGradient(
            QPointF(self.parent.food.x() + self.parent.grid_size / 2, 
                    self.parent.food.y() + self.parent.grid_size / 2),
            self.parent.grid_size / 2,
            QPointF(self.parent.food.x() + self.parent.grid_size / 3, 
                    self.parent.food.y() + self.parent.grid_size / 3)
        )
        food_gradient.setColorAt(0, QColor(255, 152, 0))  # 橙色
        food_gradient.setColorAt(1, QColor(255, 87, 34))  # 深橙色
        
        painter.setBrush(QBrush(food_gradient))
        painter.setPen(QPen(QColor(191, 54, 12), 1))  # 边框颜色
        
        # 绘制圆形食物（比蛇身小一些）- 转换为整数
        food_size = int(self.parent.grid_size * 0.8)
        offset = int(self.parent.grid_size * 0.1)
        painter.drawEllipse(
            int(self.parent.food.x() + offset),
            int(self.parent.food.y() + offset),
            food_size,
            food_size
        )
        
    def draw_extra_food(self, painter):
        """绘制额外食物"""
        # 检查是否应该闪烁（还剩3秒时开始闪烁）
        should_blink = self.parent.extra_food_timer >= self.parent.extra_food_blink_time
        is_white = should_blink and (self.parent.extra_food_timer // 1) % 2 == 0  # 缩短闪烁间隔，每帧交替
        
        # 绘制圆形额外食物 - 转换为整数
        extra_food_size = int(self.parent.grid_size * 0.9)
        offset = int(self.parent.grid_size * 0.05)
        rect = QRectF(
            int(self.parent.extra_food.x() + offset),
            int(self.parent.extra_food.y() + offset),
            extra_food_size,
            extra_food_size
        )
        
        if is_white:
            # 闪烁时显示为白色
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            painter.setPen(QPen(Qt.GlobalColor.white, 2))  # 白色边框
        else:
            # 正常状态下显示为紫色
            # 创建额外食物的渐变效果
            extra_food_gradient = QRadialGradient(
                QPointF(self.parent.extra_food.x() + self.parent.grid_size / 2, 
                        self.parent.extra_food.y() + self.parent.grid_size / 2),
                self.parent.grid_size / 2,
                QPointF(self.parent.extra_food.x() + self.parent.grid_size / 3, 
                        self.parent.extra_food.y() + self.parent.grid_size / 3)
            )
            extra_food_gradient.setColorAt(0, QColor(156, 39, 176))  # 紫色
            extra_food_gradient.setColorAt(1, QColor(103, 58, 183))  # 深紫色
            
            painter.setBrush(QBrush(extra_food_gradient))
            painter.setPen(QPen(QColor(76, 17, 84), 2))  # 粗边框
        
        painter.drawEllipse(rect)
        
        # 添加固定的白点 - 转换为整数
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.drawEllipse(
            int(self.parent.extra_food.x() + offset * 3),
            int(self.parent.extra_food.y() + offset * 3),
            int(extra_food_size * 0.2),
            int(extra_food_size * 0.2)
        )
        
        # 如果在闪烁阶段，添加额外的白色高亮效果
        if should_blink and (self.parent.extra_food_timer // 1) % 2 == 0:
            # 添加更强的白色闪烁效果
            painter.setBrush(QBrush(QColor(255, 255, 255, 150)))
            painter.drawEllipse(
                int(self.parent.extra_food.x() + offset * 1.5),
                int(self.parent.extra_food.y() + offset * 1.5),
                int(extra_food_size * 0.7),
                int(extra_food_size * 0.7)
            )
        
    def draw_bomb(self, painter):
        """绘制炸弹"""
        # 创建炸弹的渐变效果
        bomb_gradient = QRadialGradient(
            QPointF(self.parent.bomb.x() + self.parent.grid_size / 2, 
                    self.parent.bomb.y() + self.parent.grid_size / 2),
            self.parent.grid_size / 2,
            QPointF(self.parent.bomb.x() + self.parent.grid_size / 3, 
                    self.parent.bomb.y() + self.parent.grid_size / 3)
        )
        bomb_gradient.setColorAt(0, QColor(244, 67, 54))  # 红色
        bomb_gradient.setColorAt(1, QColor(183, 28, 28))  # 深红色
        
        painter.setBrush(QBrush(bomb_gradient))
        painter.setPen(QPen(QColor(136, 14, 79), 2))  # 边框颜色
        
        # 绘制圆形炸弹 - 转换为整数
        bomb_size = int(self.parent.grid_size * 0.8)
        offset = int(self.parent.grid_size * 0.1)
        painter.drawEllipse(
            int(self.parent.bomb.x() + offset),
            int(self.parent.bomb.y() + offset),
            bomb_size,
            bomb_size
        )
        
        # 添加炸弹的导火索 - 转换为整数
        painter.setPen(QPen(QColor(255, 235, 59), 3))  # 黄色导火索
        painter.drawLine(
            int(self.parent.bomb.x() + self.parent.grid_size / 2),
            int(self.parent.bomb.y() + offset),
            int(self.parent.bomb.x() + self.parent.grid_size / 2 + 10),
            int(self.parent.bomb.y() + offset - 15)
        )
        
        # 添加导火索的火花 - 转换为整数
        painter.setBrush(QBrush(Qt.GlobalColor.red))
        painter.drawEllipse(
            int(self.parent.bomb.x() + self.parent.grid_size / 2 + 10 - 3),
            int(self.parent.bomb.y() + offset - 15 - 3),
            6,
            6
        )
    
    def draw_start_message(self, painter):
        """绘制开始游戏消息"""
        # 设置字体
        font = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font)
        
        # 设置文本颜色
        painter.setPen(QColor(0, 150, 136))
        
        # 绘制开始游戏消息
        message = "按空格键开始游戏\n使用方向键控制蛇移动\n\n普通食物(橙色): +10分\n额外食物(紫色): +50分\n炸弹(红色带导火索): 游戏结束"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, message)
    
    def draw_pause_message(self, painter):
        """绘制暂停消息"""
        # 设置主标题字体
        title_font = QFont("SimHei", 28, QFont.Weight.Bold)
        painter.setFont(title_font)
        
        # 设置主标题文本颜色
        painter.setPen(QColor(255, 152, 0))
        
        # 创建半透明背景
        background_rect = QRectF(self.width() / 4, self.height() / 3, 
                               self.width() / 2, self.height() / 3)
        painter.fillRect(background_rect, QColor(0, 0, 0, 150))
        
        # 设置副标题字体
        subtitle_font = QFont("SimHei", 16, QFont.Weight.Normal)
        
        # 保存当前绘制状态
        painter.save()
        
        # 创建文本矩形
        text_rect = QRect(0, 0, self.width(), self.height())
        
        # 绘制主标题
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "游戏暂停")
        
        # 调整字体和颜色，绘制副标题
        painter.setFont(subtitle_font)
        painter.setPen(QColor(255, 255, 255))
        
        # 计算副标题的Y位置，使其显示在主标题下方
        metrics = painter.fontMetrics()
        title_height = metrics.height()
        subtitle_y = (self.height() + title_height) // 2 + 20
        
        # 创建副标题的矩形
        subtitle_rect = QRect(0, subtitle_y, self.width(), metrics.height())
        
        # 绘制副标题
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignCenter, "按空格键或点击'继续'按钮恢复游戏")
        
        # 恢复之前的绘制状态
        painter.restore()


# ===== 小说下载器集成 =====
# 多线程下载管理器，用于管理多个下载任务
class DownloadManager:
    """
    下载管理器类，负责管理多个下载线程，协调并行下载任务
    提供任务添加、状态跟踪、进度汇总等功能
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.download_threads = []  # 存储所有下载线程
        self.active_downloads = 0   # 当前活跃的下载任务数
        self.completed_downloads = 0  # 已完成的下载任务数
        self.total_downloads = 0    # 总下载任务数
        self.is_all_complete = False  # 是否所有下载都已完成
        self.is_batch_download = False  # 是否为批量下载模式
    
    def add_download(self, url, tag, attr_dict, choose_dict, file_path, total_chapters=None):
        """
        添加一个新的下载任务
        Args:
            url (str): 小说起始URL
            tag (str): HTML标签
            attr_dict (dict): 属性字典
            choose_dict (list): 选择器列表
            file_path (str): 保存文件路径
            total_chapters (int, optional): 总章节数
        """
        # 创建下载线程
        thread = DownloadThread(url, tag, attr_dict, choose_dict, file_path, total_chapters)
        # 设置线程属性，便于跟踪
        thread.url = url
        thread.file_path = file_path
        # 连接信号
        thread.progress_updated.connect(lambda progress, t=thread: self._update_thread_progress(progress, t))
        thread.message_received.connect(lambda msg, t=thread: self._forward_message(msg, t))
        thread.download_completed.connect(lambda success, msg, t=thread: self._thread_completed(success, msg, t))
        thread.download_timing.connect(lambda elapsed, estimated, t=thread: self._forward_timing(elapsed, estimated, t))
        
        # 添加到管理列表
        self.download_threads.append(thread)
        self.total_downloads += 1
        return thread
    
    def start_all(self, batch_mode=False):
        """
        启动所有下载任务
        Args:
            batch_mode (bool): 是否为批量下载模式
        """
        self.is_batch_download = batch_mode
        self.active_downloads = 0
        self.completed_downloads = 0
        self.is_all_complete = False
        
        for thread in self.download_threads:
            if not thread.isRunning():
                thread.start()
                self.active_downloads += 1
        
        # 批量下载时发送开始通知
        if batch_mode and hasattr(self.parent, 'append_log'):
            self.parent.append_log(f"批量下载开始，共{self.total_downloads}个任务")
    
    def stop_all(self):
        """
        停止所有下载任务
        """
        for thread in self.download_threads:
            if thread.isRunning():
                thread.stop()
        
        # 停止后重置状态
        self.is_batch_download = False
        if hasattr(self.parent, 'append_log'):
            self.parent.append_log("所有下载任务已停止")
    
    def _update_thread_progress(self, progress, thread):
        """
        更新单个线程的进度
        """
        if hasattr(self.parent, 'update_progress'):
            # 如果是单任务下载，更新主进度条
            if self.total_downloads == 1:
                self.parent.update_progress(progress)
    
    def _forward_message(self, message, thread):
        """
        转发线程的消息，并添加任务标识
        """
        if hasattr(self.parent, 'append_log'):
            # 从URL中提取网站标识
            site_identifier = self._get_site_identifier(thread.url)
            # 从文件路径提取文件名
            import os
            filename = os.path.basename(thread.file_path)
            self.parent.append_log(f"[{site_identifier}] [{filename}] {message}")
    
    def _thread_completed(self, success, message, thread):
        """
        处理线程完成事件
        """
        self.active_downloads -= 1
        self.completed_downloads += 1
        
        if hasattr(self.parent, 'append_log'):
            # 从URL中提取网站标识
            site_identifier = self._get_site_identifier(thread.url)
            # 从文件路径提取文件名
            import os
            filename = os.path.basename(thread.file_path)
            status = "成功" if success else "失败"
            self.parent.append_log(f"[{site_identifier}] [{filename}] 下载{status}: {message}")
        
        # 检查是否所有下载都已完成
        if self.active_downloads == 0 and self.completed_downloads == self.total_downloads:
            self.is_all_complete = True
            self.is_batch_download = False
            
            # 通知主界面所有下载完成
            if hasattr(self.parent, 'on_all_downloads_completed'):
                self.parent.on_all_downloads_completed()
            
            # 显示完成消息
            if hasattr(self.parent, 'append_log'):
                self.parent.append_log(f"所有下载任务已完成，总计{self.completed_downloads}个文件")
    
    def _forward_timing(self, elapsed, estimated, thread):
        """
        转发计时信息
        """
        # 仅在批量下载模式下显示详细计时信息
        if self.is_batch_download and hasattr(self.parent, 'append_log'):
            # 从URL中提取网站标识
            site_identifier = self._get_site_identifier(thread.url)
            # 从文件路径提取文件名
            import os
            filename = os.path.basename(thread.file_path)
            self.parent.append_log(f"[{site_identifier}] [{filename}] 已用时间: {elapsed}, 预计剩余: {estimated}")
        elif not self.is_batch_download and hasattr(self.parent, 'update_timing_info'):
            # 单任务模式更新主界面计时信息
            self.parent.update_timing_info(elapsed, estimated)
    
    def _get_site_identifier(self, url):
        """
        从URL中提取网站标识
        """
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            # 返回域名的主部分作为标识
            return parsed_url.netloc.split('.')[-2] if '.' in parsed_url.netloc else parsed_url.netloc
        except:
            return "未知站点"
    
    def is_any_running(self):
        """
        检查是否有任何下载任务正在运行
        """
        for thread in self.download_threads:
            if thread.isRunning():
                return True
        return False
    
    def clear_tasks(self):
        """
        清空所有下载任务
        """
        self.download_threads = []
        self.active_downloads = 0
        self.completed_downloads = 0
        self.total_downloads = 0
        self.is_all_complete = False
        self.is_batch_download = False

# 小说下载线程，处理耗时的下载操作
class DownloadThread(QThread) :
    """
    小说下载线程类，继承自QThread，用于在后台处理小说章节的下载操作，
    避免阻塞主线程UI响应。通过信号与主线程通信，传递进度、日志和完成状态。
    """
    # 定义信号：进度更新（传递进度百分比）
    progress_updated = pyqtSignal(int)
    # 定义信号：消息更新（传递日志文本）
    message_received = pyqtSignal(str)
    # 定义信号：下载完成（传递成功状态和结果消息）
    download_completed = pyqtSignal(bool , str)
    # 定义信号：下载计时（传递已用时间和预估时间，字符串格式）
    download_timing = pyqtSignal(str, str)
    """
        初始化下载线程
        Args:
            start_url (str): 小说起始章节的URL
            tag (str): 用于定位章节内容的HTML标签（如'div'、'p'等）
            attr_dict (dict): 章节内容标签的属性字典（如{'class': 'content'}）
            file_path (str): 小说保存的完整文件路径
            total_chapters (int, optional): 总章节数，用于精确计算进度。默认None（自动估算）
        """
    def __init__(self , start_url , tag , attr_dict ,choose_dict, file_path , total_chapters=None) :
        super().__init__()
        self.start_url = start_url  # 起始下载URL
        self.tag = tag  # 章节内容HTML标签
        self.attr_dict = attr_dict  # attr标签属性字典
        self.choose_dict = choose_dict  # choose标签属性字典
        self.file_path = file_path  # 保存文件路径
        self.total_chapters = total_chapters  # 总章节数（可选）
        self.stop_requested = False  # 停止请求标志（控制线程退出）
        self.current_chapter = 0  # 当前下载的章节数
        # 断点续传相关属性
        self.resume_info_path = self.file_path + '.progress'  # 进度文件路径
        self.resume_info = {  # 进度信息
            'last_url': start_url,
            'downloaded_chapters': 0,
            'chapter_urls': []
        }
        # 下载计时相关属性
        self.start_time = 0  # 开始时间
        self.chapter_times = []  # 各章节下载时间记录
    """
     线程执行入口函数，实现小说章节的循环下载逻辑：
     1. 从起始URL开始，依次下载每个章节内容
     2. 解析页面找到章节内容并写入文件
     3. 自动查找下一章链接，继续下载直到完成或被停止
     4. 通过信号实时反馈进度和状态
     """
    def run(self) :
        """
        线程执行入口函数，实现小说章节的循环下载逻辑：
        1. 从起始URL开始，依次下载每个章节内容，支持断点续传
        2. 解析页面找到章节内容并写入文件
        3. 自动查找下一章链接，继续下载直到完成或被停止
        4. 通过信号实时反馈进度、状态和下载计时信息
        """
        try :
            self.start_time = time.time()  # 记录开始时间
            self.message_received.emit("开始下载小说...")
            
            # 检查断点文件，实现断点续传
            resume_enabled = False
            url = self.start_url
            mode = 'w'  # 默认覆盖模式
            
            # 检查是否存在断点文件
            if os.path.exists(self.resume_info_path):
                try:
                    with open(self.resume_info_path, 'r', encoding='utf-8') as resume_file:
                        resume_data = json.load(resume_file)
                        # 验证断点数据是否有效
                        if (resume_data.get('file_path') == self.file_path and 
                            resume_data.get('last_url') and 
                            resume_data.get('downloaded_chapters', 0) > 0):
                            # 存在有效断点，准备续传
                            self.current_chapter = resume_data.get('downloaded_chapters', 0)
                            url = resume_data.get('last_url')
                            self.resume_info = resume_data
                            resume_enabled = True
                            mode = 'a'  # 追加模式
                            self.message_received.emit(f"发现断点，准备从第{self.current_chapter + 1}章继续下载")
                except Exception as e:
                    self.message_received.emit(f"加载断点文件失败: {str(e)}")
            
            if not resume_enabled:
                # 无断点，从头开始下载
                self.current_chapter = 0
                self.resume_info = {
                    'file_path': self.file_path,
                    'last_url': self.start_url,
                    'downloaded_chapters': 0,
                    'chapter_urls': []
                }
            
            # 打开文件准备写入（使用utf-8编码避免中文乱码）
            with open(self.file_path, mode, encoding='utf-8') as f:
                # 循环下载：当前URL有效且未收到停止请求时继续
                while url and not self.stop_requested:
                    chapter_start_time = time.time()  # 记录章节开始下载时间
                    wait_time = random.randint(10, 20) / 10
                    self.current_chapter += 1  # 章节计数递增
                    # 计算并发送进度
                    if self.total_chapters:
                        # 已知总章节数时，按实际比例计算进度（0-100）
                        progress = min(100, int(self.current_chapter / self.total_chapters * 100))
                    else:
                        # 未知总章节数时，用当前章节数估算进度（最高99%，避免提前显示完成）
                        progress = min(99, int(self.current_chapter / max(1, self.current_chapter) * 100))
                    self.progress_updated.emit(progress)
                    
                    # 发送当前下载状态日志
                    self.message_received.emit(f"正在下载第 {self.current_chapter} 章: {url}")
                    
                    # 发送HTTP请求获取章节页面
                    try:
                        response = requests.get(url, timeout=30)
                        # 自动识别页面编码，避免中文乱码
                        response.encoding = response.apparent_encoding
                        # 解析HTML内容
                        soup = BeautifulSoup(response.text, 'html.parser')
                    except Exception as e:
                        self.message_received.emit(f"下载章节失败: {str(e)}")
                        # 保存断点信息后退出
                        self._save_resume_info(url)
                        self.download_completed.emit(False, f"下载失败（已保存断点）: {str(e)}")
                        return
                    # 定位章节内容（根据指定的标签和属性）
                    content = soup.find(self.tag, self.attr_dict)
                    if content:
                        # 提取文本内容并写入文件，章节间添加空行分隔
                        chapter_text = content.get_text()
                        f.write(chapter_text + '\n\n')
                        self.message_received.emit(f"成功下载第 {self.current_chapter} 章")
                    else:
                        # 未找到内容时记录警告日志
                        self.message_received.emit(f"未找到第 {self.current_chapter} 章内容: {url}")
                    
                    # 记录章节下载完成时间
                    chapter_time = time.time() - chapter_start_time
                    self.chapter_times.append(chapter_time)
                    
                    # 更新并保存断点信息
                    self.resume_info['last_url'] = url
                    self.resume_info['downloaded_chapters'] = self.current_chapter
                    if url not in self.resume_info['chapter_urls']:
                        self.resume_info['chapter_urls'].append(url)
                    self._save_resume_info(url)
                    # 查找下一章链接
                    next_link = None
                    # 可能的"下一章"文本集合（支持多语言和符号）
                    next_texts = self.choose_dict
                    for next_text in next_texts:
                        # 精确匹配链接文本
                        next_link_element = soup.find('a', string=next_text)
                        if next_link_element:
                            # 拼接相对URL为绝对URL
                            next_link = urljoin(url, next_link_element.get('href'))
                            break
                    # 如果未找到精确匹配的下一章链接，尝试模糊匹配
                    if not next_link:
                        # 获取所有<a>标签逐一检查
                        next_link_elements = soup.find_all('a')
                        for element in next_link_elements:
                            # 模糊匹配包含"下一章"或"next"的链接
                            if '下一章' in element.get_text() or 'next' in element.get_text().lower():
                                next_link = urljoin(url, element.get('href'))
                                break
                    # 更新下一章URL，准备下一轮循环
                    url = next_link
                    
                    # 计算下载计时信息并发送信号
                    elapsed_time = time.time() - self.start_time
                    avg_chapter_time = sum(self.chapter_times) / len(self.chapter_times) if self.chapter_times else 0
                    
                    if self.total_chapters > 0:
                        remaining_chapters = max(0, self.total_chapters - self.current_chapter)
                        estimated_total_time = elapsed_time + (remaining_chapters * avg_chapter_time)
                    else:
                        # 未知总章节数时，根据已下载章节估算
                        estimated_total_time = elapsed_time * 2  # 简单估算为已用时的2倍
                    
                    # 格式化时间信息
                    elapsed_str = self._format_time(elapsed_time)
                    estimated_str = self._format_time(estimated_total_time)
                    
                    # 发送计时信号
                    self.download_timing.emit(elapsed_str, estimated_str)
                    
                    # 延迟1-2秒，避免请求过于频繁被服务器拦截
                    self.message_received.emit(f"正在延迟请求{wait_time}秒")
                    time.sleep(wait_time)
            # 循环结束后判断退出原因
            if not self.stop_requested:
                # 正常完成下载，删除断点文件
                if os.path.exists(self.resume_info_path):
                    try:
                        os.remove(self.resume_info_path)
                        self.message_received.emit("下载完成，已删除断点文件")
                    except:
                        pass
                # 正常完成下载
                self.download_completed.emit(True, f"小说下载完成！共下载 {self.current_chapter} 章")
            else:
                # 被用户停止下载，保存断点
                if url:
                    self._save_resume_info(url)
                self.download_completed.emit(False, "下载已取消（断点已保存）")
        except Exception as e:
            # 下载过程中发生异常，发送失败信号
            if url:
                self._save_resume_info(url)
            self.download_completed.emit(False, f"下载失败（断点已保存）: {str(e)}")
        
    def _save_resume_info(self, last_url):
        """\保存断点信息到文件"""
        try:
            self.resume_info['last_url'] = last_url
            self.resume_info['downloaded_chapters'] = self.current_chapter
            with open(self.resume_info_path, 'w', encoding='utf-8') as resume_file:
                json.dump(self.resume_info, resume_file, ensure_ascii=False, indent=2)
        except Exception as e:
            self.message_received.emit(f"保存断点失败: {str(e)}")
    
    def _format_time(self, seconds):
        """将秒数格式化为时:分:秒格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}小时{minutes}分{secs}秒"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"
    """
    请求停止下载操作。
    通过设置停止标志位，让run()方法中的循环正常退出，避免线程强制终止导致的资源泄露。
    """
    def stop(self) :
        self.stop_requested = True

# 文件打开线程类，负责在后台打开文件并通过信号反馈结果
class FileOpenThread(QThread):
    file_opened = pyqtSignal(bool, str, str)
    message_received = pyqtSignal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.stop_requested = False
    
    def run(self):
        try:
            self.message_received.emit(f"开始打开文件: {self.file_path}")
            
            # 打开文件并读取内容
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as file:
                if self.stop_requested:
                    self.file_opened.emit(False, "用户取消了文件打开操作", "")
                    return
                content = file.read()
            
            self.file_opened.emit(True, "文件打开成功", content)
            
        except Exception as e:
            error_msg = f"打开文件时出错: {str(e)}"
            self.message_received.emit(error_msg)
            self.file_opened.emit(False, error_msg, "")
    
    def stop(self):
        self.stop_requested = True

# 小说阅读器窗口类，负责显示小说内容并提供翻页和章节跳转功能
class NovelReader(QWidget):
    """小说阅读器窗口"""
    def __init__(self, file_path, content, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.file_path = file_path
        self.content = content
        self.current_page = 0
        self.paragraphs = []
        self.pages = []
        self.chapters = []
        self.chapter_indices = []
        
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle(f"小说阅读器 - {os.path.basename(file_path)}")
        self.resize(800, 600)
        
        # 初始化UI
        self.init_ui()
        
        # 处理文件内容
        self.process_content()
        
        # 显示第一页
        self.update_display()
        
        # 设置样式
        self.setup_styles()
    
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建章节选择下拉框
        self.chapter_combo = QComboBox()
        self.chapter_combo.currentIndexChanged.connect(self.on_chapter_changed)
        self.chapter_combo.setMinimumHeight(30)
        main_layout.addWidget(self.chapter_combo)
        
        # 创建内容显示区域
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.content_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content_display.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        main_layout.addWidget(self.content_display, 1)
        
        # 创建页码显示和翻页按钮
        bottom_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("上一页")
        self.prev_button.clicked.connect(self.prev_page)
        bottom_layout.addWidget(self.prev_button)
        
        self.page_label = QLabel("第 0 页，共 0 页")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.page_label, 1)
        
        self.next_button = QPushButton("下一页")
        self.next_button.clicked.connect(self.next_page)
        bottom_layout.addWidget(self.next_button)
        
        main_layout.addLayout(bottom_layout)
        
        self.setLayout(main_layout)
    
    def setup_styles(self):
        """设置窗口样式"""
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei";
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 16px;
                line-height: 1.6;
                font-family: "SimSun", "NSimSun", serif;
            }
        """)
    
    def process_content(self):
        """处理小说内容，分割段落和章节"""
        import re  # 重新导入re模块以解决作用域问题
        # 分割段落（按换行符）
        self.paragraphs = self.content.split('\n')
        self.paragraphs = [p.strip() for p in self.paragraphs if p.strip()]
        
        # 识别章节
        self.chapters = []
        self.chapter_indices = []
        
        # 常见章节格式正则表达式
        chapter_patterns = [
            r'第[\d一二三四五六七八九十百千]+章',  # 第X章
            r'第[\d一二三四五六七八九十百千]+回',  # 第X回
            r'第[\d一二三四五六七八九十百千]+节',  # 第X节
            r'第[\d一二三四五六七八九十百千]+卷',  # 第X卷
            r'卷[\d一二三四五六七八九十百千]+',     # 卷X
            r'章[\d一二三四五六七八九十百千]+',     # 章X
            r'第[\d]+话'                           # 第X话
        ]
        
        # 遍历段落，寻找章节标题
        current_chapter = ""
        chapter_start = 0
        
        for i, para in enumerate(self.paragraphs):
            is_chapter = False
            
            # 检查是否匹配任一章节格式
            for pattern in chapter_patterns:
                if re.match(pattern, para):
                    is_chapter = True
                    break
            
            # 如果找到章节标题，保存当前章节并开始新章节
            if is_chapter:
                if current_chapter:
                    self.chapters.append(current_chapter)
                    self.chapter_indices.append(chapter_start)
                
                current_chapter = para
                chapter_start = i
        
        # 添加最后一个章节
        if current_chapter:
            self.chapters.append(current_chapter)
            self.chapter_indices.append(chapter_start)
        
        # 如果没有识别到章节，添加一个默认章节
        if not self.chapters:
            self.chapters.append("全部内容")
            self.chapter_indices.append(0)
        
        # 填充章节下拉框
        self.chapter_combo.addItems(self.chapters)
        
        # 分页处理
        self.paginate_content()
    
    def paginate_content(self):
        """根据当前窗口大小分页显示内容"""
        # 获取当前内容显示区域的大小
        viewport_width = self.content_display.viewport().width()
        viewport_height = self.content_display.viewport().height()
        
        # 如果视图还未初始化，使用默认值
        if viewport_width < 10 or viewport_height < 10:
            viewport_width = 780
            viewport_height = 500
        
        # 创建临时QTextDocument来测量文本高度
        doc = QTextDocument()
        doc.setDefaultFont(self.content_display.font())
        
        self.pages = []
        current_page = []
        current_height = 0
        
        # 获取当前章节的起始和结束索引
        chapter_idx = self.chapter_combo.currentIndex()
        start_idx = self.chapter_indices[chapter_idx]
        end_idx = len(self.paragraphs) if chapter_idx == len(self.chapter_indices) - 1 else self.chapter_indices[chapter_idx + 1]
        
        # 遍历当前章节的所有段落，进行分页
        for i in range(start_idx, end_idx):
            para = self.paragraphs[i]
            
            # 测量段落高度
            doc.setPlainText(para)
            para_height = doc.size().height() + 10  # 额外添加行间距
            
            # 如果添加当前段落会超出页面高度，则创建新页面
            if current_height + para_height > viewport_height:
                if current_page:
                    self.pages.append('\n\n'.join(current_page))
                    current_page = []
                    current_height = 0
            
            # 添加段落
            current_page.append(para)
            current_height += para_height
        
        # 添加最后一页
        if current_page:
            self.pages.append('\n\n'.join(current_page))
        
        # 重置当前页码
        self.current_page = 0
    
    def update_display(self):
        """更新显示内容和页码信息"""
        if not self.pages:
            return
        
        # 确保当前页码有效
        if self.current_page < 0:
            self.current_page = 0
        elif self.current_page >= len(self.pages):
            self.current_page = len(self.pages) - 1
        
        # 显示当前页内容
        self.content_display.setPlainText(self.pages[self.current_page])
        
        # 更新页码标签
        self.page_label.setText(f"第 {self.current_page + 1} 页，共 {len(self.pages)} 页")
        
        # 更新翻页按钮状态
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < len(self.pages) - 1)
    
    def prev_page(self):
        """显示上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()
    
    def next_page(self):
        """显示下一页"""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_display()
    
    def on_chapter_changed(self, index):
        """章节选择变化时的处理函数"""
        self.paginate_content()
        self.update_display()
    
    def resizeEvent(self, event):
        """窗口大小变化时重新分页"""
        super().resizeEvent(event)
        # 延迟重新分页，确保视图大小已更新
        QTimer.singleShot(100, self.on_resize)
    
    def on_resize(self):
        """处理窗口大小变化"""
        current_page_num = self.current_page + 1
        self.paginate_content()
        # 尽量保持在相近的页面位置
        if self.pages:
            self.current_page = min(int(current_page_num * len(self.pages) / (current_page_num + 1)), len(self.pages) - 1)
        self.update_display()

# 小说下载器的主窗口类，负责提供用户界面和控制下载流程
class NovelDownloadWindow(QWidget) :
    """初始化小说下载窗口"""
    def __init__(self , parent=None) :
        super().__init__(parent)
        self.parent = parent
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("小说下载器_designed_by_wwq")
        # 修改最小尺寸为更宽的横向布局
        self.setMinimumSize(1200 , 600)
        self.init_ui()
        # 设置窗口位置在上一个窗口的左上角
        if parent and parent.isVisible() :
            parent_pos = parent.pos()
            self.move(parent_pos)
        # 加载保存的设置
        self.load_settings()
        self.download_thread = None
        self.file_open_thread = None
        # 美化UI
        self.setup_styles()
        # 窗口显示时自动最大化
        self.showMaximized()
    """设置美化的UI样式，使用Qt样式表设置各控件的外观"""
    def setup_styles(self) :
       # 设置应用整体样式
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei";
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QProgressBar {
                border: 1px solid #aaa;
                border-radius: 4px;
                text-align: center;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 1px;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
                color: #333;
            }
        """)
        # 设置进度条颜色为绿色
        palette = self.progress_bar.palette()
        palette.setColor(QPalette.ColorRole.Highlight , QColor(76 , 175 , 80))  # 绿色
        self.progress_bar.setPalette(palette)
    """初始化用户界面，创建并布局所有UI控件"""
    def init_ui(self) :
        # 创建下载管理器
        self.download_manager = DownloadManager(self)
        # 存储下载任务的列表
        self.download_tasks = []
        
        # 创建主布局 - 修改为横向布局以适应全屏横向显示
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(15)
        
        # 左侧控制面板区域
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 批量下载设置组
        batch_group = QGroupBox("批量下载设置")
        batch_layout = QVBoxLayout()
        batch_group.setLayout(batch_layout)
        
        # 批量URL输入区域
        batch_url_layout = QVBoxLayout()
        batch_url_label = QLabel("多个网站URL（每行一个）:")
        self.batch_url_input = QTextEdit()
        self.batch_url_input.setPlaceholderText("在此处粘贴多个小说网站URL，每行一个")
        self.batch_url_input.setMinimumHeight(100)
        batch_url_layout.addWidget(batch_url_label)
        batch_url_layout.addWidget(self.batch_url_input)
        
        # 添加任务按钮
        add_task_btn = QPushButton("添加到下载任务")
        add_task_btn.clicked.connect(self.add_download_task)
        batch_url_layout.addWidget(add_task_btn)
        
        batch_layout.addLayout(batch_url_layout)
        left_layout.addWidget(batch_group)
        
        # 章节识别设置组
        chapter_group = QGroupBox("章节识别设置")
        chapter_layout = QVBoxLayout()
        chapter_group.setLayout(chapter_layout)
        
        # 章节识别表单布局 - 横向两列布局
        chapter_form = QGridLayout()
        chapter_form.setHorizontalSpacing(15)
        chapter_form.setVerticalSpacing(8)
        
        # URL 输入框 - 用于输入小说起始页URL
        chapter_form.addWidget(QLabel("起始 URL:"), 0, 0)
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setToolTip("输入小说章节的起始URL")
        url_layout.addWidget(self.url_input)
        url_clear_btn = QPushButton()
        url_clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        url_clear_btn.setFixedSize(24, 24)
        url_clear_btn.clicked.connect(self.url_input.clear)
        url_layout.addWidget(url_clear_btn)
        chapter_form.addLayout(url_layout, 0, 1)
        
        # 标签输入框 - 用于指定小说章节内容的HTML标签
        chapter_form.addWidget(QLabel("内容标签:"), 0, 2)
        tag_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setToolTip("输入包含章节内容的HTML标签名称")
        tag_layout.addWidget(self.tag_input)
        tag_clear_btn = QPushButton()
        tag_clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        tag_clear_btn.setFixedSize(24, 24)
        tag_clear_btn.clicked.connect(self.tag_input.clear)
        tag_layout.addWidget(tag_clear_btn)
        chapter_form.addLayout(tag_layout, 0, 3)
        
        # 属性输入框 - 用于指定章节内容标签的属性
        chapter_form.addWidget(QLabel("内容属性:"), 1, 0)
        attr_layout = QHBoxLayout()
        self.attr_input = QLineEdit()
        self.attr_input.setToolTip("输入内容标签的属性，格式为：属性名=属性值")
        attr_layout.addWidget(self.attr_input)
        attr_clear_btn = QPushButton()
        attr_clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        attr_clear_btn.setFixedSize(24, 24)
        attr_clear_btn.clicked.connect(self.attr_input.clear)
        attr_layout.addWidget(attr_clear_btn)
        chapter_form.addLayout(attr_layout, 1, 1)
        
        # 选择器输入框 - 用于指定章节下一章按钮标签
        chapter_form.addWidget(QLabel("下一章按钮文字:"), 1, 2)
        choose_layout = QHBoxLayout()
        self.choose_input = QLineEdit()
        self.choose_input.setToolTip("输入下一章按钮的文本内容，多个用逗号分隔")
        choose_layout.addWidget(self.choose_input)
        choose_clear_btn = QPushButton()
        choose_clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        choose_clear_btn.setFixedSize(24, 24)
        choose_clear_btn.clicked.connect(self.choose_input.clear)
        choose_layout.addWidget(choose_clear_btn)
        chapter_form.addLayout(choose_layout, 1, 3)
        
        # 自动检测属性区域
        detect_layout = QHBoxLayout()
        detect_layout.setSpacing(8)
        
        # 关键词输入框 - 用于自动检测属性的关键词
        keyword_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入章节中的部分文字")
        self.keyword_input.setToolTip("输入章节内容中包含的文字，用于自动检测属性")
        keyword_layout.addWidget(self.keyword_input)
        keyword_clear_btn = QPushButton()
        keyword_clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        keyword_clear_btn.setFixedSize(24, 24)
        keyword_clear_btn.clicked.connect(self.keyword_input.clear)
        keyword_layout.addWidget(keyword_clear_btn)
        detect_layout.addWidget(QLabel("检测关键词:"), 0)
        detect_layout.addLayout(keyword_layout, 1)  # 让输入框占据更多空间
        
        # 自动检测属性按钮
        self.detect_button = QPushButton("自动检测属性")
        self.detect_button.setIcon(QIcon.fromTheme("search"))
        self.detect_button.setMinimumWidth(100)
        self.detect_button.clicked.connect(self.detect_attributes)
        detect_layout.addWidget(self.detect_button)
        
        chapter_layout.addLayout(chapter_form)
        chapter_layout.addLayout(detect_layout)
        left_layout.addWidget(chapter_group)
        
        # 下载设置组
        download_group = QGroupBox("下载设置")
        download_layout = QVBoxLayout()
        download_group.setLayout(download_layout)
        
        # 下载设置表单布局
        download_form = QVBoxLayout()
        download_form.setSpacing(8)
        
        # 保存路径选择
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)
        path_layout.addWidget(QLabel("保存路径:"), 0)
        path_input_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        path_clear_btn = QPushButton()
        path_clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        path_clear_btn.setFixedSize(24, 24)
        path_clear_btn.clicked.connect(self.path_input.clear)
        path_input_layout.addWidget(self.path_input)
        path_input_layout.addWidget(path_clear_btn)
        browse_button = QPushButton("浏览...")
        browse_button.setMinimumWidth(80)
        browse_button.clicked.connect(self.browse_path)
        path_layout.addLayout(path_input_layout, 1)  # 让输入框占据更多空间
        path_layout.addWidget(browse_button)
        download_form.addLayout(path_layout)
        
        # 文件名和章节数横向排列
        file_chapter_layout = QHBoxLayout()
        file_chapter_layout.setSpacing(15)
        
        # 文件名设置
        filename_sub_layout = QHBoxLayout()
        filename_sub_layout.addWidget(QLabel("保存文件名:"))
        filename_input_layout = QHBoxLayout()
        self.filename_input = QLineEdit()
        self.filename_input.setText("小说.txt")
        self.filename_input.setToolTip("设置保存的小说文件名")
        self.filename_input.setMinimumWidth(150)
        filename_input_layout.addWidget(self.filename_input)
        filename_clear_btn = QPushButton()
        filename_clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        filename_clear_btn.setFixedSize(24, 24)
        filename_clear_btn.clicked.connect(self.filename_input.clear)
        filename_input_layout.addWidget(filename_clear_btn)
        filename_sub_layout.addLayout(filename_input_layout)
        file_chapter_layout.addLayout(filename_sub_layout)
        
        # 总章节数设置 - 设置为0表示自动估算总章节数
        chapters_sub_layout = QHBoxLayout()
        chapters_sub_layout.addWidget(QLabel("总章节数:"))
        self.total_chapters_input = QSpinBox()
        self.total_chapters_input.setRange(0, 9999)
        self.total_chapters_input.setSuffix(" 章")
        self.total_chapters_input.setToolTip("设置为0表示自动估算总章节数")
        self.total_chapters_input.setMinimumWidth(100)
        chapters_sub_layout.addWidget(self.total_chapters_input)
        file_chapter_layout.addLayout(chapters_sub_layout)
        
        download_form.addLayout(file_chapter_layout)
        
        # 保存设置按钮
        save_settings_button = QPushButton("保存设置")
        save_settings_button.setIcon(QIcon.fromTheme("document-save"))
        save_settings_button.clicked.connect(self.save_settings)
        
        download_layout.addLayout(download_form)
        download_layout.addWidget(save_settings_button)
        left_layout.addWidget(download_group)
        
        # 下载任务列表
        task_group = QGroupBox("下载任务列表")
        task_layout = QVBoxLayout()
        task_group.setLayout(task_layout)
        
        # 任务列表视图
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.task_list.setAlternatingRowColors(True)
        # 设置任务列表高度，使其在左侧面板中占据适当空间
        self.task_list.setMaximumHeight(200)
        task_layout.addWidget(self.task_list)
        
        # 任务控制按钮
        task_control_layout = QHBoxLayout()
        
        # 删除选中任务按钮
        delete_task_btn = QPushButton("删除选中任务")
        delete_task_btn.clicked.connect(self.delete_selected_tasks)
        task_control_layout.addWidget(delete_task_btn)
        
        # 清空任务列表按钮
        clear_tasks_btn = QPushButton("清空任务列表")
        clear_tasks_btn.clicked.connect(self.clear_all_tasks)
        task_control_layout.addWidget(clear_tasks_btn)
        
        task_layout.addLayout(task_control_layout)
        left_layout.addWidget(task_group)
        
        # 设置左侧面板最小宽度
        left_panel.setMinimumWidth(600)
        
        # 右侧状态和日志区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 单任务下载按钮（兼容原功能）
        self.download_button = QPushButton("下载当前设置")
        self.download_button.setIcon(QIcon.fromTheme("download"))
        self.download_button.setMinimumHeight(36)
        self.download_button.clicked.connect(self.start_single_download)
        
        # 批量下载按钮
        self.batch_download_button = QPushButton("批量下载所有任务")
        self.batch_download_button.setIcon(QIcon.fromTheme("download"))
        self.batch_download_button.setMinimumHeight(36)
        self.batch_download_button.clicked.connect(self.start_batch_download)
        
        # 停止按钮（现在停止所有下载）
        self.stop_button = QPushButton("停止所有下载")
        self.stop_button.setIcon(QIcon.fromTheme("process-stop"))
        self.stop_button.setMinimumHeight(36)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_all_downloads)
        
        self.open_file_button = QPushButton("打开已下载文件")
        self.open_file_button.setIcon(QIcon.fromTheme("document-open"))
        self.open_file_button.setMinimumHeight(36)
        self.open_file_button.clicked.connect(self.open_downloaded_file)
        
        button_layout.addWidget(self.download_button, 1)  # 均分空间
        button_layout.addWidget(self.batch_download_button, 1)  # 均分空间
        button_layout.addWidget(self.stop_button, 1)      # 均分空间
        button_layout.addWidget(self.open_file_button, 1) # 均分空间
        right_layout.addLayout(button_layout)
        
        # 进度条 - 显示下载进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("准备中...")
        right_layout.addWidget(self.progress_bar)
        
        # 下载计时信息
        timing_layout = QHBoxLayout()
        timing_layout.setSpacing(20)
        self.elapsed_time_label = QLabel("已用时间: --")
        self.estimated_time_label = QLabel("预估时间: --")
        timing_layout.addWidget(self.elapsed_time_label)
        timing_layout.addWidget(self.estimated_time_label)
        right_layout.addLayout(timing_layout)
        
        # 日志显示框 - 显示下载过程中的信息和错误
        log_group = QGroupBox("下载日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("下载日志将显示在这里...")
        
        # 设置较小的字体
        font = QFont()
        font.setPointSize(9)
        self.log_display.setFont(font)
        # 设置日志区域为可拉伸
        self.log_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        log_layout.addWidget(self.log_display)
        
        right_layout.addWidget(log_group)
        
        # 文件内容显示窗口
        content_group = QGroupBox("文件内容")
        content_layout = QVBoxLayout(content_group)
        
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.setPlaceholderText("已打开的文件内容将显示在这里...")
        self.content_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.content_display.setVisible(False)  # 初始隐藏
        content_layout.addWidget(self.content_display)
        
        right_layout.addWidget(content_group)
        
        # 设置右侧面板为可伸缩，占据更多空间
        right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 将左右面板添加到主布局
        main_layout.addWidget(left_panel, 1)  # 左侧面板占用较小比例
        main_layout.addWidget(right_panel, 2)  # 右侧面板占用较大比例
        
        self.setLayout(main_layout)
    
    def update_progress(self, progress):
        """
        更新下载进度条
        Args:
            progress (int): 下载进度百分比 (0-100)
        """
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"下载进度: {progress}%")
    
    def update_timing_info(self, elapsed, estimated):
        """
        更新下载计时信息
        Args:
            elapsed (str): 已用时间
            estimated (str): 预估剩余时间
        """
        self.elapsed_time_label.setText(f"已用时间: {elapsed}")
        self.estimated_time_label.setText(f"预估时间: {estimated}")
    
    """浏览并选择保存路径，打开文件对话框让用户选择保存目录"""
    def browse_path(self) :
        path = QFileDialog.getExistingDirectory(self , "选择保存目录")
        if path :
            self.path_input.setText(path)
    """保存用户设置到本地配置文件，包括URL、标签、属性等下载参数"""
    def save_settings(self) :
        settings = QSettings("MyCompany" , "NovelDownloader")
        settings.setValue("url" , self.url_input.text())
        settings.setValue("tag" , self.tag_input.text())
        settings.setValue("attr" , self.attr_input.text())
        settings.setValue("choose" , self.choose_input.text())
        settings.setValue("save_path" , self.path_input.text())
        settings.setValue("filename" , self.filename_input.text())
        settings.setValue("total_chapters" , self.total_chapters_input.value())
        dialog = CustomDialog("设置已保存" , title = "成功" , button_text = "OK" , parent = self)
        dialog.exec()
    """从本地配置文件加载保存的用户设置"""
    def load_settings(self) :
        settings = QSettings("MyCompany" , "NovelDownloader")
        self.url_input.setText(settings.value("url" , ""))
        self.tag_input.setText(settings.value("tag" , ""))
        self.attr_input.setText(settings.value("attr" , ""))
        self.choose_input.setText(settings.value("choose" , ""))
        self.path_input.setText(settings.value("save_path" , os.getcwd()))
        self.filename_input.setText(settings.value("filename" , "小说.txt"))
        self.total_chapters_input.setValue(int(settings.value("total_chapters" , 0)))
    """
    开始下载小说，验证用户输入，初始化下载参数，创建并启动下载线程
    步骤：
    1. 获取并验证用户输入的参数
    2. 准备保存路径和文件
    3. 解析HTML属性
    4. 禁用下载按钮，启用停止按钮
    5. 创建并启动下载线程
    """
    def start_download(self) :
        url = self.url_input.text()
        tag = self.tag_input.text()
        attr = self.attr_input.text()
        choose = self.choose_input.text()
        save_path = self.path_input.text()
        filename = self.filename_input.text()
        total_chapters = self.total_chapters_input.value()
        total_chapters = total_chapters if total_chapters > 0 else None
        if not url or not tag or not attr :
            dialog = CustomDialog("请输入完整的 URL、标签和属性信息" , title = "警告" , button_text = "知道了" ,
                                  parent = self)
            dialog.exec()
            return
        if not save_path or not filename :
            dialog = CustomDialog("请设置保存路径和文件名" , title = "警告" , button_text = "知道了" , parent = self)
            dialog.exec()
            return
        try :
            # 确保保存路径存在
            if not os.path.exists(save_path) :
                os.makedirs(save_path)
            # 完整文件路径
            self.full_file_path = os.path.join(save_path , filename)
            # 解析attr属性为字典
            attr_dict = {}
            if '=' in attr :
                parts = attr.split('=')
                attr_dict[parts[0].strip()] = parts[1].strip()
            # 解析choose属性为列表
            choose_dict = []
            # 先处理英文逗号，若存在则拆分
            if ',' in choose :
                parts = choose.split(',')
            # 再处理中文逗号，若存在则拆分
            elif '，' in choose :
                parts = choose.split('，')
            else :
                # 若没有逗号，将整个字符串作为单个元素
                parts = [choose]
            # 去除每个元素的前后空格，添加到列表
            choose_list = [part.strip() for part in parts]
            # 禁用下载按钮，启用停止按钮，重置进度条和日志
            self.download_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("准备下载...")
            self.log_display.clear()
            # 创建并启动下载线程
            self.download_thread = DownloadThread(url , tag , attr_dict ,choose_dict, self.full_file_path , total_chapters)
            self.download_thread.progress_updated.connect(self.update_progress)
            self.download_thread.message_received.connect(self.append_log)
            self.download_thread.download_completed.connect(self.download_finished)
            self.download_thread.download_timing.connect(self.update_timing_info)
            # 启动线程
            self.download_thread.start()
            self.append_log("开始准备下载...")
            if total_chapters :
                self.append_log(f"已设置总章节数: {total_chapters}")
            else :
                self.append_log("未设置总章节数，将使用估算进度")
            self.append_log(f"文件将保存至: {self.full_file_path}")
        except Exception as e :
            self.append_log(f"初始化下载时出错: {str(e)}")
            self.download_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    """停止下载操作，向下载线程发送停止信号并禁用停止按钮"""
    def stop_download(self) :
        if self.download_thread and self.download_thread.isRunning() :
            self.append_log("正在停止下载...")
            self.download_thread.stop()
            # 禁用停止按钮，防止重复点击
            self.stop_button.setEnabled(False)
    
    """添加下载任务到任务列表
    从批量URL输入框中读取URLs，并使用当前设置的标签、属性等信息创建下载任务
    """
    def add_download_task(self):
        # 获取批量URL
        batch_urls = self.batch_url_input.toPlainText().strip().split('\n')
        # 过滤空行
        batch_urls = [url.strip() for url in batch_urls if url.strip()]
        
        if not batch_urls:
            dialog = CustomDialog("请输入至少一个有效的URL" , title = "警告" , button_text = "知道了" , parent = self)
            dialog.exec()
            return
        
        # 获取共同的设置参数
        tag = self.tag_input.text()
        attr = self.attr_input.text()
        choose = self.choose_input.text()
        save_path = self.path_input.text()
        base_filename = self.filename_input.text()
        total_chapters = self.total_chapters_input.value()
        total_chapters = total_chapters if total_chapters > 0 else None
        
        # 验证必要的设置
        if not tag or not attr or not save_path:
            dialog = CustomDialog("请确保已设置标签、属性和保存路径" , title = "警告" , button_text = "知道了" , parent = self)
            dialog.exec()
            return
        
        # 确保保存路径存在
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                dialog = CustomDialog(f"创建保存路径失败: {str(e)}" , title = "错误" , button_text = "知道了" , parent = self)
                dialog.exec()
                return
        
        # 解析属性
        attr_dict = {}
        if '=' in attr:
            parts = attr.split('=')
            attr_dict[parts[0].strip()] = parts[1].strip()
            
        # 解析选择器
        choose_list = []
        if ',' in choose:
            parts = choose.split(',')
        elif '，' in choose:
            parts = choose.split('，')
        else:
            parts = [choose]
        choose_list = [part.strip() for part in parts]
        
        # 为每个URL创建任务
        added_count = 0
        for i, url in enumerate(batch_urls):
            # 生成唯一的文件名
            if len(batch_urls) > 1:
                # 如果有多个URL，在文件名中添加序号
                name, ext = os.path.splitext(base_filename)
                filename = f"{name}_{i+1}{ext}"
            else:
                filename = base_filename
            
            file_path = os.path.join(save_path, filename)
            
            # 创建任务对象
            task = {
                'url': url,
                'tag': tag,
                'attr_dict': attr_dict,
                'choose_dict': choose_list,
                'file_path': file_path,
                'total_chapters': total_chapters
            }
            
            # 添加到任务列表
            self.download_tasks.append(task)
            
            # 添加到UI列表
            from urllib.parse import urlparse
            try:
                parsed = urlparse(url)
                site_info = f"[{parsed.netloc.split('.')[-2]}] " if '.' in parsed.netloc else ""
            except:
                site_info = "[未知站点] "
            
            display_text = f"{site_info}{os.path.basename(file_path)}"
            self.task_list.addItem(display_text)
            added_count += 1
        
        self.append_log(f"已成功添加 {added_count} 个下载任务")
        # 清空URL输入框
        self.batch_url_input.clear()
    
    """单任务下载（兼容原功能）
    使用当前设置下载单个小说
    """
    def start_single_download(self):
        """
        开始单任务下载（兼容原功能）
        """
        try:
            url = self.url_input.text()
            tag = self.tag_input.text()
            attr = self.attr_input.text()
            choose = self.choose_input.text()
            save_path = self.path_input.text()
            filename = self.filename_input.text()
            total_chapters = self.total_chapters_input.value()
            total_chapters = total_chapters if total_chapters > 0 else None
            
            if not url or not tag or not attr:
                dialog = CustomDialog("请输入完整的 URL、标签和属性信息" , title = "警告" , button_text = "知道了" , parent = self)
                dialog.exec()
                return
            
            if not save_path or not filename:
                dialog = CustomDialog("请设置保存路径和文件名" , title = "警告" , button_text = "知道了" , parent = self)
                dialog.exec()
                return
            
            # 确保保存路径存在
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            
            # 完整文件路径
            self.full_file_path = os.path.join(save_path, filename)
            
            # 解析attr属性为字典
            attr_dict = {}
            if '=' in attr:
                parts = attr.split('=')
                attr_dict[parts[0].strip()] = parts[1].strip()
                
            # 解析choose属性为列表
            choose_list = []
            if ',' in choose:
                parts = choose.split(',')
            elif '，' in choose:
                parts = choose.split('，')
            else:
                parts = [choose]
            choose_list = [part.strip() for part in parts]
            
            # 更新按钮状态
            self.download_button.setEnabled(False)
            self.batch_download_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("准备下载...")
            
            # 通过下载管理器添加任务
            thread = self.download_manager.add_download(url, tag, attr_dict, choose_list, self.full_file_path, total_chapters)
            
            # 特殊连接进度信号到主进度条
            thread.progress_updated.connect(self.update_progress)
            thread.download_completed.connect(self.download_finished)
            thread.download_timing.connect(self.update_timing_info)
            
            # 启动下载
            thread.start()
            self.download_manager.active_downloads += 1
            
            self.append_log("开始准备下载...")
            if total_chapters:
                self.append_log(f"已设置总章节数: {total_chapters}")
            else:
                self.append_log("未设置总章节数，将使用估算进度")
            self.append_log(f"文件将保存至: {self.full_file_path}")
            
        except Exception as e:
            import traceback
            self.append_log(f"初始化下载时出错: {str(e)}")
            self.append_log(f"详细错误: {traceback.format_exc()}")
            # 恢复按钮状态
            self.download_button.setEnabled(True)
            self.batch_download_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.stop_button.setEnabled(False)
    
    """批量下载所有任务
    启动任务列表中的所有下载任务
    """
    def start_batch_download(self):
        """
        批量下载所有任务
        """
        try:
            if not self.download_tasks:
                dialog = CustomDialog("下载任务列表为空，请先添加任务" , title = "提示" , button_text = "知道了" , parent = self)
                dialog.exec()
                return
            
            # 更新按钮状态
            self.download_button.setEnabled(False)
            self.batch_download_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("开始批量下载...")
            
            self.append_log(f"开始批量下载 {len(self.download_tasks)} 个任务...")
            
            # 清空之前的任务
            self.download_manager.clear_tasks()
            
            # 启动所有任务
            task_count = 0
            for task in self.download_tasks:
                try:
                    thread = self.download_manager.add_download(
                        task['url'],
                        task['tag'],
                        task['attr_dict'],
                        task['choose_dict'],
                        task['file_path'],
                        task['total_chapters']
                    )
                    task_count += 1
                except Exception as e:
                    self.append_log(f"添加任务失败: {str(e)}")
            
            if task_count > 0:
                # 统一启动所有线程，设置为批量下载模式
                self.download_manager.start_all(batch_mode=True)
            else:
                self.append_log("错误: 没有成功添加任何下载任务")
                # 恢复按钮状态
                self.download_button.setEnabled(True)
                self.batch_download_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                
        except Exception as e:
            import traceback
            self.append_log(f"批量下载错误: {str(e)}")
            self.append_log(f"详细错误: {traceback.format_exc()}")
            # 恢复按钮状态
            self.download_button.setEnabled(True)
            self.batch_download_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    """停止所有下载任务"""
    def stop_all_downloads(self):
        if self.download_manager.is_any_running():
            self.append_log("正在停止所有下载任务...")
            self.download_manager.stop_all()
            # 禁用停止按钮，防止重复点击
            self.stop_button.setEnabled(False)
    
    """删除选中的下载任务"""
    def delete_selected_tasks(self):
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return
        
        # 获取选中项的索引
        selected_indices = []
        for item in selected_items:
            index = self.task_list.row(item)
            selected_indices.append(index)
        
        # 按倒序删除，避免索引错乱
        for index in sorted(selected_indices, reverse=True):
            # 从数据列表中删除
            del self.download_tasks[index]
            # 从UI列表中删除
            self.task_list.takeItem(index)
        
        self.append_log(f"已删除 {len(selected_indices)} 个选中任务")
    
    """清空所有下载任务"""
    def clear_all_tasks(self):
        if self.download_tasks:
            dialog = CustomDialog("确定要清空所有下载任务吗？" , title = "确认" , button_text = "确定" , cancel_text = "取消" , parent = self)
            if dialog.exec():
                self.download_tasks.clear()
                self.task_list.clear()
                self.append_log("已清空所有下载任务")
    
    """所有下载任务完成后的回调函数"""
    def on_all_downloads_completed(self):
        self.append_log("所有下载任务已完成！")
        # 重置按钮状态
        self.download_button.setEnabled(True)
        self.batch_download_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        # 重置进度条
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("所有下载已完成")
        # 重置计时信息
        self.elapsed_time_label.setText("已用时间: --")
        self.estimated_time_label.setText("预估时间: --")
            
    """
    自动检测网页属性功能，根据用户输入的关键词在网页中查找包含该关键词的元素，
    并自动填充章节内容标签和属性到对应的输入框中。
    """
    def detect_attributes(self) :
        url = self.url_input.text().strip()
        keyword = self.keyword_input.text().strip()
        
        if not url :
            dialog = CustomDialog("请先输入小说起始URL" , title = "警告" , button_text = "知道了" , parent = self)
            dialog.exec()
            return
        
        if not keyword :
            dialog = CustomDialog("请输入章节中包含的文字，用于自动检测属性" , title = "警告" , button_text = "知道了" , parent = self)
            dialog.exec()
            return
        
        try :
            # 禁用检测按钮，防止重复点击
            self.detect_button.setEnabled(False)
            self.append_log(f"正在尝试自动检测 {url} 的属性...")
            
            # 发送HTTP请求获取网页内容
            response = requests.get(url)
            response.encoding = response.apparent_encoding
            
            # 解析HTML内容
            soup = BeautifulSoup(response.text , 'html.parser')
            
            # 查找包含关键词的所有文本节点
            text_nodes = soup.find_all(text=lambda text: text and keyword in text)
            
            if not text_nodes :
                self.append_log(f"未在网页中找到包含关键词 '{keyword}' 的内容")
                dialog = CustomDialog(f"未在网页中找到包含关键词 '{keyword}' 的内容" , title = "提示" , button_text = "确定" , parent = self)
                dialog.exec()
                return
            
            # 找到最近的非文本父元素
            found_elements = []
            for node in text_nodes:
                # 找到包含该文本节点的最接近的有意义的父元素
                parent = node.parent
                while parent and parent.name in ['p', 'span', 'strong', 'em', 'b', 'i']:
                    parent = parent.parent
                
                # 将找到的元素添加到列表中
                if parent and parent.name:
                    found_elements.append(parent)
            
            if not found_elements :
                self.append_log(f"找到包含关键词的内容，但无法确定对应的HTML标签")
                dialog = CustomDialog("找到包含关键词的内容，但无法确定对应的HTML标签" , title = "提示" , button_text = "确定" , parent = self)
                dialog.exec()
                return
            
            # 统计各元素标签的出现次数，找出最可能的内容容器
            tag_counts = {}
            for element in found_elements:
                tag_name = element.name
                if tag_name in tag_counts:
                    tag_counts[tag_name] += 1
                else:
                    tag_counts[tag_name] = 1
            
            # 找出出现次数最多的标签
            most_common_tag = max(tag_counts, key=tag_counts.get)
            
            # 收集该标签的所有元素
            candidate_elements = [e for e in found_elements if e.name == most_common_tag]
            
            # 找出属性最多的元素（通常内容容器会有标识性的class或id）
            best_element = None
            max_attrs = 0
            for element in candidate_elements:
                if len(element.attrs) > max_attrs:
                    max_attrs = len(element.attrs)
                    best_element = element
            
            # 如果找不到属性丰富的元素，就用第一个
            if not best_element and candidate_elements:
                best_element = candidate_elements[0]
            
            if not best_element:
                self.append_log(f"未找到合适的内容容器元素")
                dialog = CustomDialog("未找到合适的内容容器元素" , title = "提示" , button_text = "确定" , parent = self)
                dialog.exec()
                return
            
            # 提取标签名
            tag_name = best_element.name
            
            # 提取属性（优先选择class和id）
            attr_str = ""
            if 'class' in best_element.attrs:
                classes = best_element.attrs['class']
                if isinstance(classes, list):
                    attr_str = f"class={classes[0]}"
                else:
                    attr_str = f"class={classes}"
            elif 'id' in best_element.attrs:
                attr_str = f"id={best_element.attrs['id']}"
            # 如果没有class或id，尝试其他属性
            elif best_element.attrs:
                first_attr = next(iter(best_element.attrs.items()))
                attr_str = f"{first_attr[0]}={first_attr[1]}"
            
            # 填充到输入框
            self.tag_input.setText(tag_name)
            self.attr_input.setText(attr_str)
            
            self.append_log(f"自动检测成功！已填充标签: {tag_name}，属性: {attr_str}")
            dialog = CustomDialog(f"自动检测成功！\n标签: {tag_name}\n属性: {attr_str}" , title = "成功" , button_text = "确定" , parent = self)
            dialog.exec()
            
        except Exception as e:
            self.append_log(f"自动检测属性时出错: {str(e)}")
            dialog = CustomDialog(f"自动检测属性时出错: {str(e)}" , title = "错误" , button_text = "确定" , parent = self)
            dialog.exec()
        finally:
            # 重新启用检测按钮
            self.detect_button.setEnabled(True)
    """
    更新进度条显示
    Args:
        value: 进度值(0-100)
    """
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if hasattr(self, 'file_open_thread') and self.file_open_thread and self.file_open_thread.isRunning():
            if value < 100:
                self.progress_bar.setFormat(f"打开文件中: {value}%")
            else:
                self.progress_bar.setFormat("文件打开完成!")
        else:
            if value < 100:
                self.progress_bar.setFormat(f"下载中: {value}%")
            else:
                self.progress_bar.setFormat("下载完成!")
    
    def update_timing_info(self, elapsed_time, estimated_time):
        """更新下载计时信息的显示"""
        self.elapsed_time_label.setText(f"已用时间: {elapsed_time}")
        self.estimated_time_label.setText(f"预估时间: {estimated_time}")
    """
     添加日志信息到日志显示框，并自动滚动到底部
      Args:
         message: 要添加的日志消息
     """
    def append_log(self, message):
        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        # 自动滚动到底部
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )
    """
    下载完成后的处理函数，重置UI状态并显示结果对话框
    Args:
        success: 下载是否成功的布尔值
        message: 下载完成消息
    """
    def download_finished(self, success, message):
        self.download_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(100 if success else 0)
        # 重置计时信息
        if hasattr(self, 'elapsed_time_label'):
            self.elapsed_time_label.setText("已用时间: --")
        if hasattr(self, 'estimated_time_label'):
            self.estimated_time_label.setText("预估时间: --")
        self.append_log(message)
        if success:
            dialog = CustomDialog(f"{message}\n文件已保存至: {self.full_file_path}", title="成功",
                                  button_text="OK", parent=self)
            dialog.exec()
        else:
            dialog = CustomDialog(message, title="失败", button_text="知道了", parent=self)
            dialog.exec()
    
    """打开已下载的小说文件"""
    def open_downloaded_file(self):
        # 获取保存路径和文件名
        save_path = self.path_input.text()
        filename = self.filename_input.text()
        
        # 如果没有设置路径或文件名，让用户选择文件
        if not save_path or not filename:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", os.getcwd(), "文本文件 (*.txt);;所有文件 (*.*)"
            )
            if not file_path:
                return
        else:
            # 使用设置的路径和文件名
            file_path = os.path.join(save_path, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                # 如果文件不存在，让用户选择文件
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "选择文件", save_path, "文本文件 (*.txt);;所有文件 (*.*)"
                )
                if not file_path:
                    return
        
        # 禁用打开文件按钮，防止重复点击
        self.open_file_button.setEnabled(False)
        self.download_button.setEnabled(False)
        
        # 创建并启动文件打开线程
        self.file_open_thread = FileOpenThread(file_path)
        self.file_open_thread.message_received.connect(self.append_log)
        self.file_open_thread.file_opened.connect(self.file_opened_finished)
        self.file_open_thread.start()
        
    """文件打开完成后的处理函数"""
    def file_opened_finished(self, success, message, content):
        self.open_file_button.setEnabled(True)
        self.download_button.setEnabled(True)
        
        if success:
            # 打开小说阅读器窗口
            self.novel_reader = NovelReader(self.file_open_thread.file_path, content, self)
            self.novel_reader.show()
        
        self.append_log(message)
        
        # 清理线程引用
        self.file_open_thread = None
    
    def closeEvent(self, event):
        """处理窗口关闭事件，确保正确发出destroyed信号"""
        # 调用父类的closeEvent以确保正常关闭流程
        super().closeEvent(event)
        # 窗口关闭后会自动触发destroyed信号


# ===== 下载相关类 =====
# 自定义ComboBox，可精确控制下拉列表高度
class FixedHeightComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setView(QTreeView())  # 使用树状视图
    def showPopup(self):
        """重写显示下拉列表的方法，设置固定高度"""
        super().showPopup()
        tree_view = self.view()
        tree_view.setFixedHeight(400)  # 强制设置为400px高度
        tree_view.setMinimumHeight(400)  # 确保至少400px
        tree_view.setMaximumHeight(400)  # 确保不超过400px

# 基础下载线程类
class VideoDownloadThread(QThread):
    """基础下载线程类"""
    progress_updated = pyqtSignal(int)
    message_received = pyqtSignal(str)
    download_completed = pyqtSignal(bool, str)
    def __init__(self):
        super().__init__()
        self.stop_requested = False

    def stop(self):
        self.stop_requested = True
        self.message_received.emit("正在停止下载...")

# M3U8 下载线程类
class M3U8VideoDownloadThread(VideoDownloadThread):
    """m3u8下载线程"""

    def __init__(self, url, save_path, ffmpeg_path, convert_to_mp4=True, file_name=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.ffmpeg_path = ffmpeg_path
        self.convert_to_mp4 = convert_to_mp4
        self.file_name = file_name
        self.total_segments = 0
        self.downloaded_segments = 0
        self.process = None  # 存储子进程引用

    @staticmethod
    def find_ffmpeg():
        """自动查找系统中的ffmpeg"""
        try:
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                return os.path.abspath(ffmpeg_path)

            if sys.platform.startswith('win'):
                paths = os.environ['PATH'].split(';')
                for path in paths:
                    ffmpeg_exe = os.path.join(path, 'ffmpeg.exe')
                    if os.path.exists(ffmpeg_exe) and os.path.isfile(ffmpeg_exe):
                        return os.path.abspath(ffmpeg_exe)
                return "ffmpeg.exe"
            else:
                common_paths = [
                    '/usr/bin/ffmpeg',
                    '/usr/local/bin/ffmpeg',
                    '/opt/homebrew/bin/ffmpeg',
                    '/usr/local/Cellar/ffmpeg/*/bin/ffmpeg'
                ]
                for path in common_paths:
                    if os.path.exists(path) and os.path.isfile(path):
                        return os.path.abspath(path)
                return "ffmpeg"
        except Exception as e:
            return "ffmpeg"

    def parse_m3u8(self, m3u8_content, base_url):
        """解析m3u8内容获取TS片段"""
        lines = m3u8_content.split('\n')
        segments = []

        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#EXTINF:') or line.startswith('#EXT-X-KEY:'):
                try:
                    if i + 1 < len(lines):
                        ts_url = lines[i + 1].strip()
                        if not ts_url.startswith('http') and not ts_url.startswith('#'):
                            ts_url = urljoin(base_url, ts_url)
                        segments.append(ts_url)
                except Exception as e:
                    self.message_received.emit(f"解析m3u8出错: {str(e)}")

        return segments
        
    def parse_m3u8_file(self, url):
        """下载并解析M3U8文件获取TS片段列表"""
        try:
            self.message_received.emit(f"正在解析M3U8文件: {url}")
            
            # 发送请求获取M3U8内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 处理可能的编码问题
            m3u8_content = response.text
            
            # 解析M3U8内容获取TS片段
            segments = self.parse_m3u8(m3u8_content, url)
            
            return segments
        except Exception as e:
            self.message_received.emit(f"下载或解析M3U8文件失败: {str(e)}")
            return []
            
    def download_ts_segments(self, segments, temp_dir):
        """下载所有TS片段"""
        downloaded_files = []
        
        if not segments:
            return downloaded_files
            
        # 设置请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
        session = requests.Session()
        
        for i, segment_url in enumerate(segments):
            if self.stop_requested:
                break
                
            try:
                # 生成文件名
                segment_filename = f"segment_{i:05d}.ts"
                segment_path = os.path.join(temp_dir, segment_filename)
                
                # 下载片段
                self.message_received.emit(f"下载片段 {i+1}/{self.total_segments}: {segment_url}")
                
                response = session.get(segment_url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()
                
                # 写入文件
                with open(segment_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                downloaded_files.append(segment_path)
                self.downloaded_segments += 1
                
                # 更新进度
                progress = int((self.downloaded_segments / self.total_segments) * 90)  # 留10%给合并
                self.progress_updated.emit(progress)
                
            except Exception as e:
                self.message_received.emit(f"下载片段 {i+1} 失败: {str(e)}")
                # 继续尝试下载其他片段
                continue
                
        return downloaded_files

    def merge_ts_files(self, ts_files, output_path):
        """合并TS文件"""
        if not ts_files:
            return False

        # 限制列表文件路径长度，防止过长路径导致问题
        max_path_length = 255
        if len(output_path) > max_path_length:
            self.message_received.emit(f"警告: 输出路径过长，可能导致合并失败")

        list_file = os.path.splitext(output_path)[0] + ".txt"

        # 确保列表文件路径有效
        try:
            with open(list_file, 'w', encoding='utf-8') as f:
                for ts_file in ts_files:
                    # 检查每个片段路径长度
                    if len(ts_file) > max_path_length:
                        self.message_received.emit(f"警告: 片段路径过长: {ts_file[:50]}...")
                    f.write(f"file '{ts_file}'\n")
        except Exception as e:
            self.message_received.emit(f"创建列表文件失败: {str(e)}")
            return False

        self.message_received.emit("开始合并视频片段...")
        cmd = [
            self.ffmpeg_path,
            '-y', '-f', 'concat', '-safe', '0', '-i', list_file,
        ]

        if self.convert_to_mp4:
            cmd.extend(['-c:v', 'copy', '-c:a', 'copy', output_path])
        else:
            cmd.extend(['-c', 'copy', output_path])

        try:
            self.progress_updated.emit(95)

            # 使用更安全的方式启动子进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
            )

            for line in self.process.stdout:
                if self.stop_requested:
                    self.terminate_process()  # 使用安全的进程终止方法
                    return False
                if "frame=" in line:
                    self.message_received.emit(f"合并中: {line.strip()}")

            self.process.wait()

            if os.path.exists(list_file):
                os.remove(list_file)

            return self.process.returncode == 0

        except Exception as e:
            self.message_received.emit(f"合并出错: {str(e)}")
            return False
        finally:
            if os.path.exists(list_file):
                os.remove(list_file)
            self.process = None  # 清理进程引用

    def terminate_process(self):
        """安全终止子进程"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)  # 等待5秒
            except Exception as e:
                self.message_received.emit(f"终止进程失败: {str(e)}")
                try:
                    self.process.kill()  # 强制终止
                except:
                    pass
            finally:
                self.process = None

    def run(self):
        """线程主执行函数"""
        try:
            # 生成随机临时目录
            temp_dir = os.path.join(os.getenv('TEMP', '/tmp'), f"m3u8_temp_{uuid.uuid4().hex}")
            os.makedirs(temp_dir, exist_ok=True)

            # 生成输出文件名
            if not self.file_name:
                # 从URL中提取文件名或生成随机名称
                base_name = urlparse(self.url).path.split('/')[-1]
                if not base_name or len(base_name) < 3:
                    base_name = f"video_{int(time.time())}"
                file_name = f"{os.path.splitext(base_name)[0]}.mp4" if self.convert_to_mp4 else base_name
            else:
                file_name = self.file_name
                # 确保文件名有正确的扩展名
                if self.convert_to_mp4 and not file_name.lower().endswith('.mp4'):
                    file_name += '.mp4'

            output_path = os.path.join(self.save_path, file_name)

            # 确保保存目录存在
            os.makedirs(self.save_path, exist_ok=True)

            # 解析M3U8文件获取片段列表
            segments = self.parse_m3u8_file(self.url)
            if not segments:
                self.download_completed.emit(False, "无法解析M3U8文件或没有可用片段")
                return

            self.total_segments = len(segments)
            self.message_received.emit(f"找到 {self.total_segments} 个视频片段")

            # 下载所有片段
            files = self.download_ts_segments(segments, temp_dir)

            if not files or self.stop_requested:
                if self.stop_requested:
                    self.download_completed.emit(False, "下载已取消")
                else:
                    self.download_completed.emit(False, "片段下载失败")
                return

            success = self.merge_ts_files(files, output_path)

            if success:
                self.progress_updated.emit(100)
                self.download_completed.emit(True, f"下载完成，保存至: {output_path}")
            else:
                self.download_completed.emit(False, "合并失败")

        except Exception as e:
            self.message_received.emit(f"致命错误: {str(e)}")
            self.download_completed.emit(False, f"处理出错: {str(e)}")
        finally:
            # 确保临时文件清理，无论成功或失败
            if os.path.exists(temp_dir):
                self.cleanup_temp_dir(temp_dir)

    def cleanup_temp_dir(self, temp_dir):
        """安全清理临时目录"""
        try:
            # 先尝试删除文件
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    self.message_received.emit(f"删除临时文件失败: {file} - {str(e)}")

            # 然后删除目录
            try:
                os.rmdir(temp_dir)
            except Exception as e:
                self.message_received.emit(f"删除临时目录失败: {str(e)}")
        except Exception as e:
            self.message_received.emit(f"清理临时文件时出错: {str(e)}")

# 直接下载线程 - 用于MP4、FLV、F4V、WebM等格式
class DirectVideoDownloadThread(VideoDownloadThread):
    """直接下载线程 - 用于MP4、FLV、F4V、WebM等格式"""

    def __init__(self, url, save_path, file_name=None, expected_ext=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.file_name = file_name
        self.expected_ext = expected_ext

    def run(self):
        """线程主执行函数"""
        try:
            self.message_received.emit(f"开始处理地址: {self.url}")

            # 确保保存目录存在
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)

            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # 尝试从URL提取文件名和扩展名
            url_basename = os.path.basename(urlparse(self.url).path).split('?')[0].split('#')[0]
            if '.' in url_basename:
                url_name, url_ext = os.path.splitext(url_basename)
                url_ext = url_ext[1:].lower()  # 移除点并转为小写
            else:
                url_name = url_basename
                url_ext = ""

            # 确定最终扩展名
            ext = self.expected_ext or url_ext or "mp4"

            # 确定最终文件名
            output_filename = self.file_name or f"video_{timestamp}.{ext}"
            output_path = os.path.join(self.save_path, output_filename)

            # 检查文件是否已存在
            counter = 1
            while os.path.exists(output_path):
                name, ext = os.path.splitext(output_filename)
                output_filename = f"{name}_{counter}{ext}"
                output_path = os.path.join(self.save_path, output_filename)
                counter += 1

            # 开始下载
            self.message_received.emit(f"开始下载至: {output_path}")
            session = requests.Session()
            session.max_redirects = 30

            try:
                # 获取文件大小
                head_response = session.head(self.url, allow_redirects=True, timeout=15)
                head_response.raise_for_status()
                file_size = int(head_response.headers.get('content-length', 0))
                final_url = head_response.url
            except Exception as e:
                self.message_received.emit(f"HEAD请求失败，尝试直接下载: {str(e)}")
                get_response = session.get(self.url, stream=True, allow_redirects=True, timeout=15)
                get_response.raise_for_status()
                file_size = int(get_response.headers.get('content-length', 0))
                final_url = get_response.url
                get_response.close()

            # 检查断点续传
            resume_pos = 0
            if os.path.exists(output_path):
                resume_pos = os.path.getsize(output_path)
                if file_size > 0 and resume_pos >= file_size:
                    self.download_completed.emit(True, f"文件已存在: {output_path}")
                    return
                elif file_size > 0:
                    self.message_received.emit(f"检测到部分文件，将从 {resume_pos} 字节继续下载")

            # 开始下载
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'

            response = session.get(final_url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()

            mode = 'ab' if resume_pos > 0 else 'wb'
            downloaded_size = resume_pos
            chunk_size = 8192

            with open(output_path, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.stop_requested:
                        response.close()
                        self.download_completed.emit(False, "下载已取消")
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if file_size > 0:
                            progress = int((downloaded_size / file_size) * 100)
                            self.progress_updated.emit(progress)
                            if progress % 10 == 0:
                                self.message_received.emit(f"已下载 {downloaded_size}/{file_size} 字节 ({progress}%)")
                        else:
                            self.message_received.emit(f"已下载 {downloaded_size} 字节")

            # 验证文件大小
            if file_size > 0 and os.path.getsize(output_path) != file_size:
                self.message_received.emit(f"警告: 下载文件大小与预期不符 ({os.path.getsize(output_path)}/{file_size})")

            self.progress_updated.emit(100)
            self.download_completed.emit(True, f"下载完成，保存至: {output_path}")

        except Exception as e:
            self.download_completed.emit(False, f"下载失败: {str(e)}")

# 音频下载线程 - 用于MP3、WMA、WAV、M4A等格式
class AudioVideoDownloadThread(VideoDownloadThread):
    """音频下载线程 - 用于MP3、WMA、WAV、M4A等格式"""

    def __init__(self, url, save_path, ffmpeg_path, file_name=None, expected_ext=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.ffmpeg_path = ffmpeg_path
        self.file_name = file_name
        self.expected_ext = expected_ext

    def run(self):
        """线程主执行函数"""
        try:
            self.message_received.emit(f"开始处理音频地址: {self.url}")

            # 确保保存目录存在
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)

            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # 尝试从URL提取文件名和扩展名
            url_basename = os.path.basename(urlparse(self.url).path).split('?')[0].split('#')[0]
            if '.' in url_basename:
                url_name, url_ext = os.path.splitext(url_basename)
                url_ext = url_ext[1:].lower()  # 移除点并转为小写
            else:
                url_name = url_basename
                url_ext = ""

            # 确定最终扩展名
            ext = self.expected_ext or url_ext or "mp3"

            # 确定最终文件名
            output_filename = self.file_name or f"audio_{timestamp}.{ext}"
            output_path = os.path.join(self.save_path, output_filename)

            # 检查文件是否已存在
            counter = 1
            while os.path.exists(output_path):
                name, ext = os.path.splitext(output_filename)
                output_filename = f"{name}_{counter}{ext}"
                output_path = os.path.join(self.save_path, output_filename)
                counter += 1

            # 开始下载
            self.message_received.emit(f"开始下载至: {output_path}")
            session = requests.Session()
            session.max_redirects = 30

            try:
                # 获取文件大小
                head_response = session.head(self.url, allow_redirects=True, timeout=15)
                head_response.raise_for_status()
                file_size = int(head_response.headers.get('content-length', 0))
                final_url = head_response.url
            except Exception as e:
                self.message_received.emit(f"HEAD请求失败，尝试直接下载: {str(e)}")
                get_response = session.get(self.url, stream=True, allow_redirects=True, timeout=15)
                get_response.raise_for_status()
                file_size = int(get_response.headers.get('content-length', 0))
                final_url = get_response.url
                get_response.close()

            # 检查断点续传
            resume_pos = 0
            if os.path.exists(output_path):
                resume_pos = os.path.getsize(output_path)
                if file_size > 0 and resume_pos >= file_size:
                    self.download_completed.emit(True, f"文件已存在: {output_path}")
                    return
                elif file_size > 0:
                    self.message_received.emit(f"检测到部分文件，将从 {resume_pos} 字节继续下载")

            # 开始下载
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'

            response = session.get(final_url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()

            mode = 'ab' if resume_pos > 0 else 'wb'
            downloaded_size = resume_pos
            chunk_size = 8192

            with open(output_path, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.stop_requested:
                        response.close()
                        self.download_completed.emit(False, "下载已取消")
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if file_size > 0:
                            progress = int((downloaded_size / file_size) * 100)
                            self.progress_updated.emit(progress)
                            if progress % 10 == 0:
                                self.message_received.emit(f"已下载 {downloaded_size}/{file_size} 字节 ({progress}%)")
                        else:
                            self.message_received.emit(f"已下载 {downloaded_size} 字节")

            # 验证文件大小
            if file_size > 0 and os.path.getsize(output_path) != file_size:
                self.message_received.emit(f"警告: 下载文件大小与预期不符 ({os.path.getsize(output_path)}/{file_size})")

            # 优化的音频转换逻辑，支持更多格式
            if self.ffmpeg_path:
                # 定义支持的输入格式列表
                supported_input_formats = ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'opus', 'weba', 'flac', 'alac', 'wma']
                
                # 定义输出格式优先级，优先保持原有格式，否则转换为mp3
                output_format = ext if ext in supported_input_formats else 'mp3'
                converted_path = os.path.splitext(output_path)[0] + f".{output_format}"
                
                # 无论原始格式是什么，都尝试使用FFmpeg进行处理，确保兼容性
                self.message_received.emit(f"开始处理音频格式: {ext} -> {output_format}")
                
                # 构建针对不同格式优化的FFmpeg命令
                cmd = [
                    self.ffmpeg_path,
                    '-y',  # 覆盖现有文件
                    '-i', output_path,  # 输入文件
                    '-vn',  # 禁用视频流
                ]
                
                # 根据目标格式设置不同的编码参数
                if output_format == 'mp3':
                    cmd.extend(['-c:a', 'libmp3lame', '-q:a', '2'])  # MP3高质量设置
                elif output_format == 'wav':
                    cmd.extend(['-c:a', 'pcm_s16le', '-ar', '44100'])  # WAV无损格式
                elif output_format == 'm4a':
                    cmd.extend(['-c:a', 'aac', '-b:a', '256k'])  # AAC高质量设置
                elif output_format in ['ogg', 'opus']:
                    cmd.extend(['-c:a', 'libopus', '-b:a', '192k'])  # Opus高质量设置
                elif output_format == 'flac':
                    cmd.extend(['-c:a', 'flac', '-compression_level', '8'])  # FLAC无损压缩
                else:
                    cmd.extend(['-c:a', 'copy'])  # 对于其他支持的格式，直接复制音频流
                
                # 添加输出路径
                cmd.append(converted_path)

                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True
                    )

                    # 捕获FFmpeg输出，以便更好地调试和显示进度
                    error_output = []
                    for line in process.stdout:
                        if self.stop_requested:
                            process.terminate()
                            self.download_completed.emit(False, "转换已取消")
                            return
                        # 收集错误信息
                        if 'error' in line.lower() or 'failed' in line.lower():
                            error_output.append(line.strip())

                    process.wait()

                    if process.returncode == 0:
                        # 转换成功，删除原始文件（如果路径不同）
                        if output_path != converted_path:
                            os.remove(output_path)
                            output_path = converted_path
                        self.message_received.emit(f"音频处理完成，格式: {output_format}")
                    else:
                        error_msg = "\n".join(error_output) if error_output else "未知错误"
                        self.message_received.emit(f"格式处理失败，错误: {error_msg}\n保留原始文件")

                except Exception as e:
                    self.message_received.emit(f"格式处理出错: {str(e)}")

            self.progress_updated.emit(100)
            self.download_completed.emit(True, f"下载完成，保存至: {output_path}")

        except Exception as e:
            self.download_completed.emit(False, f"下载失败: {str(e)}")

# 自适应下载线程 - 用于HLS、DASH等格式
class AdaptiveVideoDownloadThread(VideoDownloadThread):
    """自适应下载线程 - 用于HLS、DASH等格式"""

    def __init__(self, url, save_path, ffmpeg_path, file_name=None, format_type=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.ffmpeg_path = ffmpeg_path
        self.file_name = file_name
        self.format_type = format_type or "mp4"

    def run(self):
        """线程主执行函数"""
        try:
            self.message_received.emit(f"开始处理自适应流地址: {self.url}")

            # 验证FFmpeg
            try:
                subprocess.run(
                    [self.ffmpeg_path, '-version'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            except Exception as e:
                self.download_completed.emit(False, f"FFmpeg不可用: {str(e)}")
                return

            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = self.file_name or f"video_{timestamp}.{self.format_type}"
            output_path = os.path.join(self.save_path, output_filename)

            self.message_received.emit(f"开始使用FFmpeg下载...")

            # 使用FFmpeg直接下载自适应流
            cmd = [
                self.ffmpeg_path,
                '-y',
                '-i', self.url,
                '-c', 'copy',
                output_path
            ]

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )

                while process.poll() is None:
                    if self.stop_requested:
                        process.terminate()
                        self.download_completed.emit(False, "下载已取消")
                        return
                    time.sleep(0.5)

                if process.returncode == 0:
                    self.progress_updated.emit(100)
                    self.download_completed.emit(True, f"下载完成，保存至: {output_path}")
                else:
                    self.download_completed.emit(False, f"下载失败，FFmpeg返回代码: {process.returncode}")

            except Exception as e:
                self.download_completed.emit(False, f"下载出错: {str(e)}")

        except Exception as e:
            self.download_completed.emit(False, f"处理出错: {str(e)}")

# 新增：图片下载线程类
class ImageDownloadThread(VideoDownloadThread):
    """图片下载线程"""

    def __init__(self, url, save_path, file_name=None, expected_ext=None):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.file_name = file_name
        self.expected_ext = expected_ext

    def run(self):
        """线程主执行函数"""
        try:
            self.message_received.emit(f"开始处理图片地址: {self.url}")

            # 确保保存目录存在
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)

            # 生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")

            # 尝试从URL提取文件名和扩展名
            url_basename = os.path.basename(urlparse(self.url).path).split('?')[0].split('#')[0]
            if '.' in url_basename:
                url_name, url_ext = os.path.splitext(url_basename)
                url_ext = url_ext[1:].lower()  # 移除点并转为小写
            else:
                url_name = url_basename
                url_ext = ""

            # 确定最终扩展名
            ext = self.expected_ext or url_ext or "jpg"

            # 常见图片格式映射
            image_formats = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff"]
            if ext not in image_formats:
                ext = "jpg"  # 默认为JPG

            # 确定最终文件名
            output_filename = self.file_name or f"image_{timestamp}.{ext}"
            output_path = os.path.join(self.save_path, output_filename)

            # 检查文件是否已存在
            counter = 1
            while os.path.exists(output_path):
                name, ext = os.path.splitext(output_filename)
                output_filename = f"{name}_{counter}{ext}"
                output_path = os.path.join(self.save_path, output_filename)
                counter += 1

            # 开始下载
            self.message_received.emit(f"开始下载至: {output_path}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            }

            try:
                # 发送HEAD请求获取内容类型
                head_response = requests.head(self.url, headers=headers, timeout=15)
                head_response.raise_for_status()

                content_type = head_response.headers.get('content-type', '').lower()
                if 'image' not in content_type:
                    self.download_completed.emit(False, f"URL指向的不是图片类型: {content_type}")
                    return

                # 尝试从Content-Type确定扩展名
                if not ext and 'content-type' in head_response.headers:
                    content_type = head_response.headers['content-type'].lower()
                    if 'jpeg' in content_type:
                        ext = 'jpg'
                    elif 'png' in content_type:
                        ext = 'png'
                    elif 'gif' in content_type:
                        ext = 'gif'
                    elif 'webp' in content_type:
                        ext = 'webp'
                    elif 'svg' in content_type:
                        ext = 'svg'
                    elif 'bmp' in content_type:
                        ext = 'bmp'
                    elif 'tiff' in content_type:
                        ext = 'tiff'

                # 如果扩展名无效，使用从Content-Type确定的扩展名
                if ext not in image_formats and 'content-type' in head_response.headers:
                    output_filename = f"image_{timestamp}.{ext}"
                    output_path = os.path.join(self.save_path, output_filename)

                # 获取文件大小
                file_size = int(head_response.headers.get('content-length', 0))

            except Exception as e:
                self.message_received.emit(f"HEAD请求失败，直接下载: {str(e)}")
                file_size = 0

            # 开始下载
            try:
                response = requests.get(self.url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                with open(output_path, 'wb') as f:
                    downloaded_size = 0
                    chunk_size = 8192

                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if self.stop_requested:
                            response.close()
                            self.download_completed.emit(False, "下载已取消")
                            return
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if file_size > 0:
                                progress = int((downloaded_size / file_size) * 100)
                                self.progress_updated.emit(progress)
                                if progress % 10 == 0:
                                    self.message_received.emit(
                                        f"已下载 {downloaded_size}/{file_size} 字节 ({progress}%)")
                            else:
                                self.message_received.emit(f"已下载 {downloaded_size} 字节")

                # 验证文件大小
                if file_size > 0 and os.path.getsize(output_path) != file_size:
                    self.message_received.emit(
                        f"警告: 下载文件大小与预期不符 ({os.path.getsize(output_path)}/{file_size})")

                self.progress_updated.emit(100)
                self.download_completed.emit(True, f"图片下载完成，保存至: {output_path}")

            except Exception as e:
                self.download_completed.emit(False, f"图片下载失败: {str(e)}")

        except Exception as e:
            self.download_completed.emit(False, f"处理出错: {str(e)}")

# 视频下载器主窗口类
class VideoDownloaderWindow(QWidget):
    """视频下载器主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowFlags(Qt.WindowType.Window)
        self.VIDEO_OUTPUT_DIR = "video_output"
        self.MUSIC_OUTPUT_DIR = "music_output"
        self.IMAGE_OUTPUT_DIR = "image_output"  # 新增图片输出目录
        self.ensure_output_dirs_exist()
        self.init_ui()
        self.load_settings()
        self.download_thread = None  # 初始化下载线程变量
        # 设置窗口位置在上一个窗口的左上角
        if parent and parent.isVisible():
            parent_pos = parent.pos()
            self.move(parent_pos)

    def ensure_output_dirs_exist(self):
        """确保默认输出目录存在"""
        if not os.path.exists(self.VIDEO_OUTPUT_DIR):
            os.makedirs(self.VIDEO_OUTPUT_DIR)
        if not os.path.exists(self.MUSIC_OUTPUT_DIR):
            os.makedirs(self.MUSIC_OUTPUT_DIR)
        if not os.path.exists(self.IMAGE_OUTPUT_DIR):  # 新增图片目录检查
            os.makedirs(self.IMAGE_OUTPUT_DIR)

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("多功能下载器_designed_by_wwq")  # 标题改为更通用的名称
        self.setMinimumSize(600, 600)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 设置区域
        settings_group = QGroupBox("下载设置")
        settings_layout = QFormLayout()
        settings_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        settings_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        settings_layout.setSpacing(10)

        # URL输入
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入视频、音频或图片URL")  # 更新提示文本
        settings_layout.addRow("URL:", self.url_input)

        # 美化的格式选择器
        format_layout = QHBoxLayout()
        self.format_combo = FixedHeightComboBox()  # 使用自定义ComboBox
        self.format_combo.setMinimumWidth(250)

        # 添加视频格式分组
        video_group = QStandardItem("视频格式")
        video_group.setFlags(Qt.ItemFlag.ItemIsEnabled)  # 分组项不可选
        video_formats = [
            "MP4", "FLV", "F4V", "WebM", "MOV", "MKV",
            "AVI", "WMV", "ASF", "DIVX", "MPEG4", "OGV"
        ]

        # 添加音频格式分组
        audio_group = QStandardItem("音频格式")
        audio_group.setFlags(Qt.ItemFlag.ItemIsEnabled)
        audio_formats = [
            "MP3", "WMA", "WAV", "M4A", "AAC", "OGG", "OPUS", "WEBA"
        ]

        # 添加图片格式分组（新增）
        image_group = QStandardItem("图片格式")
        image_group.setFlags(Qt.ItemFlag.ItemIsEnabled)
        image_formats = [
            "JPG", "PNG", "GIF", "BMP", "WebP", "SVG", "TIFF"
        ]

        # 添加流媒体格式分组
        stream_group = QStandardItem("流媒体格式")
        stream_group.setFlags(Qt.ItemFlag.ItemIsEnabled)
        stream_formats = [
            "M3U8", "HLS", "M3U", "MPD"
        ]

        # 创建模型并添加分组
        model = QStandardItemModel()
        model.insertRow(0, QStandardItem("自动检测"))
        model.appendRow(video_group)
        for fmt in video_formats:
            item = QStandardItem(fmt)
            video_group.appendRow(item)

        model.appendRow(audio_group)
        for fmt in audio_formats:
            item = QStandardItem(fmt)
            audio_group.appendRow(item)

        # 添加图片格式
        model.appendRow(image_group)
        for fmt in image_formats:
            item = QStandardItem(fmt)
            image_group.appendRow(item)

        model.appendRow(stream_group)
        for fmt in stream_formats:
            item = QStandardItem(fmt)
            stream_group.appendRow(item)

        self.format_combo.setModel(model)
        self.format_combo.setCurrentIndex(0)  # 默认选中自动检测

        # 增强树状图视觉效果
        self.format_combo.setView(QTreeView())
        tree_view = self.format_combo.view()
        tree_view.setHeaderHidden(True)  # 确保表头被隐藏
        tree_view.setIndentation(15)

        # 设置样式表（移除max-height限制）
        self.format_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
                border-left: 1px solid #ccc;
                border-radius: 0 4px 4px 0;
            }
            QTreeView {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px;
                background-color: white;
            }
            QTreeView::item {
                height: 22px;
                border-radius: 2px;
            }
            QTreeView::item:selected {
                background-color: #E6F2FF;
                color: #2196F3;
            }
            QTreeView::item:hover:!selected {
                background-color: #F0F0F0;
            }
            QTreeView::item:has-children {
                font-weight: bold;
                color: #555;
            }
        """)

        format_layout.addWidget(QLabel("格式:"))
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        settings_layout.addRow("", format_layout)

        # 文件名
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("留空则自动生成")
        settings_layout.addRow("文件名:", self.filename_input)

        # FFmpeg路径
        ffmpeg_layout = QHBoxLayout()
        self.ffmpeg_input = QLineEdit()
        ffmpeg_browse_btn = QPushButton("浏览...")
        ffmpeg_browse_btn.clicked.connect(self.browse_ffmpeg)
        ffmpeg_layout.addWidget(self.ffmpeg_input)
        ffmpeg_layout.addWidget(ffmpeg_browse_btn)
        settings_layout.addRow("FFmpeg路径:", ffmpeg_layout)

        # 保存路径
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        path_browse_btn = QPushButton("浏览...")
        path_browse_btn.clicked.connect(self.browse_save_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(path_browse_btn)
        settings_layout.addRow("视频保存路径:", path_layout)

        # 新增：音乐保存路径
        music_path_layout = QHBoxLayout()
        self.music_path_input = QLineEdit()
        music_browse_btn = QPushButton("浏览...")
        music_browse_btn.clicked.connect(self.browse_music_save_path)
        music_path_layout.addWidget(self.music_path_input)
        music_path_layout.addWidget(music_browse_btn)
        settings_layout.addRow("音乐保存路径:", music_path_layout)

        # 新增：图片保存路径
        image_path_layout = QHBoxLayout()
        self.image_path_input = QLineEdit()
        self.image_path_input.setText(self.IMAGE_OUTPUT_DIR)  # 设置默认图片路径
        image_browse_btn = QPushButton("浏览...")
        image_browse_btn.clicked.connect(self.browse_image_save_path)
        image_path_layout.addWidget(self.image_path_input)
        image_path_layout.addWidget(image_browse_btn)
        settings_layout.addRow("图片保存路径:", image_path_layout)

        # 转换选项
        self.convert_checkbox = QCheckBox("转换为MP4/MP3格式")
        self.convert_checkbox.setChecked(True)
        settings_layout.addRow("格式设置:", self.convert_checkbox)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.download_btn = QPushButton("开始下载")
        self.download_btn.clicked.connect(self.start_download)
        self.stop_btn = QPushButton("停止下载")
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        self.save_settings_btn = QPushButton("保存设置")
        self.save_settings_btn.clicked.connect(self.save_settings)
        self.delete_suffix_btn = QPushButton("删除指定后缀名文件")
        self.delete_suffix_btn.clicked.connect(self.show_delete_by_suffix_dialog)

        btn_layout.addWidget(self.download_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.save_settings_btn)
        btn_layout.addWidget(self.delete_suffix_btn)
        settings_layout.addRow("", btn_layout)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # 公共日志和进度区域
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("准备就绪")
        progress_layout.addWidget(self.progress_bar)

        log_group = QGroupBox("下载日志")
        log_layout = QVBoxLayout()
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        font = QFont()
        font.setPointSize(9)
        self.log_display.setFont(font)
        log_layout.addWidget(self.log_display)
        log_group.setLayout(log_layout)
        progress_layout.addWidget(log_group)

        main_layout.addLayout(progress_layout)

        self.setLayout(main_layout)
        self.setup_styles()

    def setup_styles(self):
        """设置界面样式"""
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
                color: #333;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QProgressBar {
                height: 24px;
                border-radius: 4px;
                text-align: center;
                border: 1px solid #ccc;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 2px;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
                border-left: 1px solid #ccc;
                border-radius: 0 4px 4px 0;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down_arrow.png);
                width: 16px;
                height: 16px;
            }
            QTreeView {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 2px;
                background-color: white;
            }
            QTreeView::item {
                height: 22px;
                border-radius: 2px;
            }
            QTreeView::item:selected {
                background-color: #E6F2FF;
                color: #2196F3;
            }
            QTreeView::item:hover:!selected {
                background-color: #F0F0F0;
            }
            QTreeView::item:has-children {
                font-weight: bold;
                color: #555;
            }
        """)

    def browse_ffmpeg(self):
        filter_str = "可执行文件 (*.exe);;所有文件 (*)" if sys.platform.startswith('win') else "所有文件 (*)"
        path, _ = QFileDialog.getOpenFileName(self, "选择FFmpeg", "", filter_str)
        if path:
            self.ffmpeg_input.setText(path)

    def browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择视频保存目录")
        if path:
            self.path_input.setText(path)

    def browse_music_save_path(self):
        """浏览并设置音乐保存路径"""
        path = QFileDialog.getExistingDirectory(self, "选择音乐保存目录")
        if path:
            self.music_path_input.setText(path)

    def browse_image_save_path(self):
        """浏览并设置图片保存路径"""
        path = QFileDialog.getExistingDirectory(self, "选择图片保存目录")
        if path:
            self.image_path_input.setText(path)

    def start_download(self):
        url = self.url_input.text().strip()
        ffmpeg_path = self.ffmpeg_input.text().strip()
        save_path = self.path_input.text().strip()
        file_name = self.filename_input.text().strip()
        selected_format = self.format_combo.currentText().lower()
        convert_to_mp4 = self.convert_checkbox.isChecked()

        if not url:
            dialog = CustomDialog("请输入URL", title="输入错误", button_text='知道了', parent=self)
            dialog.exec()
            return

        # 根据格式决定保存位置
        detected_format = self.detect_format(url)
        format_to_use = selected_format if selected_format != "自动检测" else detected_format

        # 改进的格式检测（新增）
        if format_to_use == "unknown":
            # 尝试通过HEAD请求检测内容类型
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
                }
                response = requests.head(url, headers=headers, timeout=10)
                content_type = response.headers.get('content-type', '').lower()

                if 'video' in content_type:
                    format_to_use = "mp4"
                elif 'audio' in content_type:
                    format_to_use = "mp3"
                elif 'image' in content_type:
                    format_to_use = "jpg"
                else:
                    format_to_use = "unknown"
            except Exception as e:
                self.append_log(f"自动检测失败: {str(e)}")

        # 如果用户没有指定保存路径，使用默认的分类保存路径
        if not save_path:
            if format_to_use in ["mp3", "wma", "wav", "m4a", "aac", "ogg", "opus", "weba"]:
                save_path = self.music_path_input.text() or self.MUSIC_OUTPUT_DIR
            elif format_to_use in ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff"]:  # 新增图片判断
                save_path = self.image_path_input.text() or self.IMAGE_OUTPUT_DIR
            else:
                save_path = self.path_input.text() or self.VIDEO_OUTPUT_DIR

        # 确保保存目录存在
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except Exception as e:
                QMessageBox.warning(self, "路径错误", f"无法创建保存目录: {str(e)}")
                return

        # 检查FFmpeg是否需要
        if format_to_use in ["m3u8", "hls", "mpd", "m3u", "webm", "ogg", "ogv", "aac", "opus", "weba"]:
            if not ffmpeg_path or not os.path.exists(ffmpeg_path):
                auto_ffmpeg = M3U8VideoDownloadThread.find_ffmpeg()
                if os.path.exists(auto_ffmpeg):
                    self.ffmpeg_input.setText(auto_ffmpeg)
                    ffmpeg_path = auto_ffmpeg
                else:
                    QMessageBox.warning(self, "配置错误", "处理此格式需要FFmpeg，请设置有效的FFmpeg路径")
                    return

        self.save_settings()

        # 根据格式选择合适的下载线程（改进）
        if format_to_use in ["m3u8", "hls", "m3u"]:
            self.download_thread = M3U8VideoDownloadThread(
                url=url,
                save_path=save_path,
                ffmpeg_path=ffmpeg_path,
                convert_to_mp4=convert_to_mp4,
                file_name=file_name
            )
        elif format_to_use in ["mpd"]:
            self.download_thread = AdaptiveVideoDownloadThread(
                url=url,
                save_path=save_path,
                ffmpeg_path=ffmpeg_path,
                file_name=file_name,
                format_type="mp4"
            )
        elif format_to_use in ["mp3", "wma", "wav", "m4a", "aac", "opus", "weba"]:
            self.download_thread = AudioVideoDownloadThread(
                url=url,
                save_path=save_path,
                ffmpeg_path=ffmpeg_path,
                file_name=file_name,
                expected_ext=format_to_use
            )
        elif format_to_use in ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff"]:  # 新增图片下载
            self.download_thread = ImageDownloadThread(
                url=url,
                save_path=save_path,
                file_name=file_name,
                expected_ext=format_to_use
            )
        else:
            # 默认为直接下载（改进了MP4的处理）
            self.download_thread = DirectVideoDownloadThread(
                url=url,
                save_path=save_path,
                file_name=file_name,
                expected_ext=format_to_use
            )

        # 统一的信号连接和线程启动逻辑
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.message_received.connect(self.append_log)
        self.download_thread.download_completed.connect(self.download_finished)

        self.download_thread.start()
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_download(self):
        """安全停止下载线程"""
        if self.download_thread and self.download_thread.isRunning():
            self.append_log("正在停止下载线程...")
            self.download_thread.stop()
            # 等待线程结束
            if not self.download_thread.wait(5000):  # 等待5秒
                self.append_log("下载线程未能及时停止，强制终止")
                self.download_thread.terminate()
                self.download_thread.wait()  # 确保线程已停止
            self.download_thread = None
            self.stop_btn.setEnabled(False)

    def disconnect_signals(self):
        """断开所有线程信号连接"""
        if self.download_thread:
            try:
                self.download_thread.progress_updated.disconnect()
                self.download_thread.message_received.disconnect()
                self.download_thread.download_completed.disconnect()
            except Exception as e:
                # 忽略已断开的信号
                pass

    def download_finished(self, success, message):
        self.append_log(message)
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            self.progress_bar.setFormat("下载完成")
            QMessageBox.information(self, "成功", message)
            # 清空输入框，准备下一次下载
            self.url_input.clear()
            self.append_log("等待下一次下载...")
        else:
            self.progress_bar.setFormat("下载失败")
            QMessageBox.warning(self, "失败", message)

        self.download_thread = None

    def save_settings(self):
        """保存设置到配置文件"""
        settings = QSettings("VideoDownloader", "GeneralSettings")
        settings.setValue("ffmpeg_path", self.ffmpeg_input.text())
        settings.setValue("video_save_path", self.path_input.text())
        settings.setValue("music_save_path", self.music_path_input.text())
        settings.setValue("image_save_path", self.image_path_input.text())  # 新增图片路径保存
        settings.setValue("convert_to_mp4", self.convert_checkbox.isChecked())
        settings.setValue("last_format", self.format_combo.currentText())
        self.append_log("设置已保存")

    def load_settings(self):
        """从配置文件加载设置"""
        settings = QSettings("VideoDownloader", "GeneralSettings")
        self.ffmpeg_input.setText(settings.value("ffmpeg_path", ""))
        self.path_input.setText(settings.value("video_save_path", ""))
        self.music_path_input.setText(settings.value("music_save_path", ""))
        self.image_path_input.setText(settings.value("image_save_path", ""))
        convert_to_mp4 = settings.value("convert_to_mp4", True, type=bool)
        self.convert_checkbox.setChecked(convert_to_mp4)

        last_format = settings.value("last_format", "自动检测")
        format_index = self.format_combo.findText(last_format)
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)

        self.append_log("设置已加载")

    def detect_format(self, url):
        """尝试从URL检测格式"""
        url = url.lower()
        video_formats = ["mp4", "flv", "f4v", "webm", "mov", "mkv", "avi", "wmv", "asf", "divx", "mpeg4",
                         "ogv"]
        audio_formats = ["mp3", "wma", "wav", "m4a", "aac", "ogg", "opus", "weba"]
        image_formats = ["jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "tiff"]
        stream_formats = ["m3u8", "hls", "m3u", "mpd"]

        # 检查是否是流媒体格式
        for fmt in stream_formats:
            if f".{fmt}" in url or f"{fmt}?" in url or f"{fmt}=" in url:
                return fmt

        # 检查是否是视频格式
        for fmt in video_formats:
            if f".{fmt}" in url or f"{fmt}?" in url or f"{fmt}=" in url:
                return fmt

        # 检查是否是音频格式
        for fmt in audio_formats:
            if f".{fmt}" in url or f"{fmt}?" in url or f"{fmt}=" in url:
                return fmt

        # 检查是否是图片格式
        for fmt in image_formats:
            if f".{fmt}" in url or f"{fmt}?" in url or f"{fmt}=" in url:
                return fmt

        # 检查常见的流媒体服务
        if "youtube.com" in url or "youtu.be" in url:
            return "mp4"
        elif "vimeo.com" in url:
            return "mp4"
        elif "dailymotion.com" in url:
            return "mp4"
        elif "bilibili.com" in url or "b23.tv" in url:
            return "flv"
        elif "tiktok.com" in url or "douyin.com" in url:
            return "mp4"
        elif "soundcloud.com" in url:
            return "mp3"
        elif "spotify.com" in url:
            return "mp3"
        elif "pinterest.com" in url or "imgur.com" in url or "unsplash.com" in url:
            return "jpg"

        return "unknown"

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{value}%")
    
    def append_log(self, message):
        """添加日志信息到日志显示框，并自动滚动到底部
        
        Args:
            message: 要添加的日志消息
        """
        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        # 自动滚动到底部
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )
        
    def show_delete_by_suffix_dialog(self):
        """显示删除指定后缀名文件的对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("删除指定后缀名文件")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        # 创建目录选择部分
        dir_layout = QHBoxLayout()
        dir_label = QLabel("删除目录:")
        self.delete_dir_edit = QLineEdit()
        self.delete_dir_edit.setText(self.path_input.text())  # 默认使用视频保存路径
        browse_dir_btn = QPushButton("浏览...")
        browse_dir_btn.clicked.connect(lambda: self.browse_delete_dir(dialog))
        
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.delete_dir_edit)
        dir_layout.addWidget(browse_dir_btn)
        
        # 创建后缀名输入部分
        suffix_layout = QHBoxLayout()
        suffix_label = QLabel("文件后缀名:")
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setPlaceholderText("例如: .txt,.log,.tmp 或 txt,log,tmp")
        
        suffix_layout.addWidget(suffix_label)
        suffix_layout.addWidget(self.suffix_edit)
        
        # 创建选项部分
        option_layout = QVBoxLayout()
        self.include_subdirs = QCheckBox("包含子目录")
        self.include_subdirs.setChecked(True)
        self.confirm_before_delete = QCheckBox("删除前确认")
        self.confirm_before_delete.setChecked(True)
        
        option_layout.addWidget(self.include_subdirs)
        option_layout.addWidget(self.confirm_before_delete)
        
        # 创建按钮部分
        btn_layout = QHBoxLayout()
        start_delete_btn = QPushButton("开始删除")
        start_delete_btn.clicked.connect(lambda: self.delete_files_by_suffix(dialog))
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(start_delete_btn)
        btn_layout.addWidget(cancel_btn)
        
        # 添加到主布局
        layout.addLayout(dir_layout)
        layout.addLayout(suffix_layout)
        layout.addLayout(option_layout)
        layout.addLayout(btn_layout)
        
        dialog.exec()
        
    def browse_delete_dir(self, parent=None):
        """浏览删除文件的目录"""
        dir_path = QFileDialog.getExistingDirectory(
            parent, "选择要清理的目录", self.delete_dir_edit.text())
        
        if dir_path:
            self.delete_dir_edit.setText(dir_path)
        
    def delete_files_by_suffix(self, dialog):
        """根据后缀名删除文件"""
        # 获取用户输入的参数
        delete_dir = self.delete_dir_edit.text().strip()
        suffix_text = self.suffix_edit.text().strip()
        include_subdirs = self.include_subdirs.isChecked()
        confirm_before_delete = self.confirm_before_delete.isChecked()
        
        # 参数验证
        if not delete_dir:
            QMessageBox.warning(self, "警告", "请选择要清理的目录")
            return
        
        if not suffix_text:
            QMessageBox.warning(self, "警告", "请输入要删除的文件后缀名")
            return
        
        # 解析后缀名
        suffixes = [s.strip() for s in suffix_text.split(',') if s.strip()]
        if not suffixes:
            QMessageBox.warning(self, "警告", "请输入有效的文件后缀名")
            return
        
        # 标准化后缀名（确保以点开头）
        normalized_suffixes = []
        for suffix in suffixes:
            if not suffix.startswith('.'):
                normalized_suffixes.append('.' + suffix)
            else:
                normalized_suffixes.append(suffix)
        
        self.append_log(f"开始搜索文件: 目录='{delete_dir}', 后缀名={','.join(normalized_suffixes)}, 包含子目录={include_subdirs}")
        
        # 搜索匹配的文件
        matching_files = []
        try:
            if include_subdirs:
                for root, _, files in os.walk(delete_dir):
                    for file in files:
                        for suffix in normalized_suffixes:
                            if file.lower().endswith(suffix.lower()):
                                matching_files.append(os.path.join(root, file))
                                break
            else:
                # 只搜索当前目录
                for file in os.listdir(delete_dir):
                    file_path = os.path.join(delete_dir, file)
                    if os.path.isfile(file_path):
                        for suffix in normalized_suffixes:
                            if file.lower().endswith(suffix.lower()):
                                matching_files.append(file_path)
                                break
                                 
            self.append_log(f"搜索完成，找到 {len(matching_files)} 个匹配的文件")
        except Exception as e:
            error_msg = f"搜索文件时出错: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)
            self.append_log(error_msg)
            return
        
        # 检查是否找到匹配的文件
        if not matching_files:
            QMessageBox.information(self, "提示", f"在目录 '{delete_dir}' 中未找到匹配后缀名的文件")
            return
        
        # 删除前确认
        if confirm_before_delete:
            msg = f"找到 {len(matching_files)} 个匹配的文件，是否确认删除？\n\n"
            
            # 显示前5个文件作为示例
            show_count = min(5, len(matching_files))
            for i in range(show_count):
                msg += f"{matching_files[i]}\n"
            
            if len(matching_files) > show_count:
                msg += f"... 还有 {len(matching_files) - show_count} 个文件 ...\n\n"
            
            msg += "\n注意：此操作不可撤销！"
            
            reply = QMessageBox.question(
                self, "确认删除", msg, QMessageBox.Yes | QMessageBox.No)
            
            if reply != QMessageBox.Yes:
                return
        
        # 执行删除操作
        deleted_count = 0
        failed_count = 0
        failed_files = []
        
        self.append_log(f"开始删除文件: 总共 {len(matching_files)} 个文件")
        
        try:
            for file_path in matching_files:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    self.append_log(f"已删除文件: {file_path}")
                except Exception as e:
                    failed_count += 1
                    error_msg = f"{file_path}: {str(e)}"
                    failed_files.append(error_msg)
                    self.append_log(f"删除文件失败: {error_msg}")
        except Exception as e:
            error_msg = f"删除文件时发生异常: {str(e)}"
            QMessageBox.critical(self, "错误", error_msg)
            self.append_log(error_msg)
            return
        
        # 显示删除结果
        result_msg = f"删除完成！\n成功删除: {deleted_count} 个文件\n删除失败: {failed_count} 个文件"
        self.append_log(result_msg)
        
        if failed_count > 0:
            # 显示失败文件的详细信息
            detailed_msg = "删除成功的文件: " + str(deleted_count) + "\n\n删除失败的文件:\n"
            for failed_file in failed_files:
                detailed_msg += f"{failed_file}\n"
            
            QMessageBox.information(
                self, "删除结果", result_msg, QMessageBox.Ok)
        else:
            QMessageBox.information(
                self, "删除结果", result_msg, QMessageBox.Ok)
        
        # 关闭对话框
        dialog.accept()

# ===== 重复文件查找线程 - 用于识别内容相同的文件 =====
class DuplicateFileFinderThread(QThread):
    """重复文件查找线程 - 通过计算文件哈希值来识别内容相同的文件"""
    
    import hashlib  # 在类内部导入hashlib以确保线程环境中可用
    
    progress_updated = pyqtSignal(int)
    message_received = pyqtSignal(str)
    duplicates_found = pyqtSignal(list)
    search_completed = pyqtSignal(bool, str)
    current_file_processed = pyqtSignal(str)  # 新信号：当前正在处理的文件
    duplicate_file_found = pyqtSignal(list)   # 新信号：实时发现的单个重复文件组
    
    def __init__(self, folder_path, supported_formats=None):
        super().__init__()
        self.folder_path = folder_path
        self.supported_formats = supported_formats or ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'opus', 'weba', 'flac', 'alac', 'wma']
        self.stop_requested = False
        self.file_hashes = {}  # 用于存储文件哈希值和对应的文件路径列表
    
    def stop(self):
        """停止查找线程"""
        self.stop_requested = True
    
    def calculate_file_hash(self, file_path, block_size=65536):
        """计算文件的MD5哈希值，用于识别重复文件"""
        try:
            import hashlib  # 在方法内部导入hashlib以确保运行时可用
            hasher = hashlib.md5()
            with open(file_path, 'rb') as file:
                buf = file.read(block_size)
                while buf and not self.stop_requested:
                    hasher.update(buf)
                    buf = file.read(block_size)
            if self.stop_requested:
                return None
            return hasher.hexdigest()
        except Exception as e:
            self.message_received.emit(f"计算文件哈希时出错: {str(e)}")
            return None
    
    def run(self):
        """线程主执行函数"""
        try:
            # 确保中文目录路径正确显示
            try:
                self.message_received.emit(f"开始查找重复文件: {self.folder_path}")
            except UnicodeEncodeError:
                self.message_received.emit(f"开始查找重复文件: [路径包含特殊字符]")
            
            # 查找所有支持的音频文件
            audio_files = []
            try:
                for root, dirs, files in os.walk(self.folder_path):
                    if self.stop_requested:
                        self.search_completed.emit(False, "查找已取消")
                        return
                    
                    for file in files:
                        _, ext = os.path.splitext(file)
                        ext = ext[1:].lower()
                        if ext in self.supported_formats:
                            audio_files.append(os.path.normpath(os.path.join(root, file)))
            except Exception as e:
                self.message_received.emit(f"搜索音频文件出错: {str(e)}")
                self.search_completed.emit(False, f"搜索文件失败: {str(e)}")
                return
            
            total_files = len(audio_files)
            if total_files == 0:
                self.search_completed.emit(True, "未找到音频文件")
                return
            
            self.message_received.emit(f"找到 {total_files} 个音频文件，开始计算哈希值...")
            
            # 计算每个文件的哈希值并查找重复
            for i, file_path in enumerate(audio_files):
                if self.stop_requested:
                    self.search_completed.emit(False, "查找已取消")
                    return
                
                # 发出当前处理的文件信号
                try:
                    self.current_file_processed.emit(file_path)
                except UnicodeEncodeError:
                    self.current_file_processed.emit("[文件名包含特殊字符]")
                
                # 计算文件哈希值
                file_hash = self.calculate_file_hash(file_path)
                if file_hash:
                    # 记录哈希值和对应的文件路径
                    if file_hash in self.file_hashes:
                        self.file_hashes[file_hash].append(file_path)
                        # 如果这个哈希值现在有多个文件了，说明找到了重复文件
                        if len(self.file_hashes[file_hash]) == 2:
                            # 发出实时发现的重复文件组信号
                            self.duplicate_file_found.emit(self.file_hashes[file_hash])
                    else:
                        self.file_hashes[file_hash] = [file_path]
                
                # 更新进度
                progress = int(((i + 1) / total_files) * 100)
                self.progress_updated.emit(progress)
            
            # 筛选出重复的文件组（包含多个文件的哈希组）
            duplicate_groups = [files for files in self.file_hashes.values() if len(files) > 1]
            
            # 添加调试信息
            self.message_received.emit(f"即将发送重复文件列表，共{len(duplicate_groups)}组重复文件")
            
            # 发送重复文件列表
            try:
                self.duplicates_found.emit(duplicate_groups)
                self.message_received.emit("成功发送重复文件列表信号")
            except Exception as e:
                self.message_received.emit(f"发送重复文件列表信号时出错: {str(e)}")
                
            # 完成查找
            if duplicate_groups:
                total_duplicates = sum(len(group) for group in duplicate_groups)
                self.search_completed.emit(True, f"查找完成，找到 {len(duplicate_groups)} 组重复文件，共 {total_duplicates} 个重复文件")
            else:
                self.search_completed.emit(True, "查找完成，未发现重复文件")
        except Exception as e:
            self.search_completed.emit(False, f"查找过程中出错: {str(e)}")


# ===== 音频格式转换工具 =====
class AudioFormatConverterThread(VideoDownloadThread):
    """音频格式转换线程 - 用于批量转换音频文件格式"""
    
    def __init__(self, folder_path, target_format, ffmpeg_path, overwrite_existing=False):
        super().__init__()
        self.folder_path = folder_path
        self.target_format = target_format.lower()
        self.ffmpeg_path = ffmpeg_path
        self.overwrite_existing = overwrite_existing
        self.supported_formats = ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'opus', 'weba', 'flac', 'alac', 'wma']
        
    def find_audio_files(self):
        """查找目录中所有支持的音频文件"""
        audio_files = []
        try:
            for root, dirs, files in os.walk(self.folder_path):
                for file in files:
                    # 检查文件扩展名是否在支持的格式列表中
                    _, ext = os.path.splitext(file)
                    ext = ext[1:].lower()  # 移除点并转为小写
                    if ext in self.supported_formats:
                        # 如果目标格式与当前格式相同，则跳过（除非强制覆盖）
                        if ext == self.target_format and not self.overwrite_existing:
                            continue
                        audio_files.append(os.path.join(root, file))
        except Exception as e:
            self.message_received.emit(f"搜索音频文件出错: {str(e)}")
        
        return audio_files
        
    def convert_file(self, input_path):
        """使用FFmpeg转换单个音频文件格式"""
        try:
            # 确保输入路径使用Windows兼容的路径分隔符
            input_path = os.path.normpath(input_path)
            
            # 获取文件信息
            file_name = os.path.basename(input_path)
            file_dir = os.path.dirname(input_path)
            base_name, _ = os.path.splitext(file_name)
            
            # 构建输出文件路径
            output_path = os.path.normpath(os.path.join(file_dir, f"{base_name}.{self.target_format}"))
            
            # 检查输出文件是否已存在
            counter = 1
            while os.path.exists(output_path):
                if self.overwrite_existing:
                    break
                output_path = os.path.normpath(os.path.join(file_dir, f"{base_name}_{counter}.{self.target_format}"))
                counter += 1
                
            # 确保中文文件名正确显示
            try:
                display_file_name = file_name
                display_output_name = f"{base_name}.{self.target_format}"
                self.message_received.emit(f"开始转换: {display_file_name} -> {display_output_name}")
            except UnicodeEncodeError:
                # 如果文件名包含无法编码的字符，则使用安全的显示方式
                self.message_received.emit(f"开始转换: [文件路径包含特殊字符] -> [{base_name}.{self.target_format}]")
            
            # 构建FFmpeg命令 - 注意在Windows中处理中文路径的特殊处理
            cmd = [
                self.ffmpeg_path,
                '-y',  # 覆盖现有文件
                '-i', input_path,
                '-vn',  # 禁用视频流
                # 添加编码相关参数以确保中文支持
                '-hide_banner'
            ]
            
            # 根据目标格式设置不同的编码参数
            if self.target_format == 'mp3':
                cmd.extend(['-c:a', 'libmp3lame', '-q:a', '2'])  # MP3高质量设置
            elif self.target_format == 'wav':
                cmd.extend(['-c:a', 'pcm_s16le', '-ar', '44100'])  # WAV无损格式
            elif self.target_format == 'm4a':
                cmd.extend(['-c:a', 'aac', '-b:a', '256k'])  # AAC高质量设置
            elif self.target_format in ['ogg', 'opus']:
                cmd.extend(['-c:a', 'libopus', '-b:a', '192k'])  # Opus高质量设置
            elif self.target_format == 'flac':
                cmd.extend(['-c:a', 'flac', '-compression_level', '8'])  # FLAC无损压缩
            else:
                cmd.extend(['-c:a', 'copy'])  # 对于其他支持的格式，直接复制音频流
            
            # 添加输出路径
            cmd.append(output_path)
            
            # 执行FFmpeg命令 - 修改为二进制模式处理，避免编码问题
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=False  # 在Windows上不使用shell
            )
            
            # 捕获FFmpeg输出（二进制模式）
            error_output = []
            try:
                while True:
                    if self.stop_requested:
                        process.terminate()
                        return False, "转换已取消"
                    
                    line = process.stdout.readline()
                    if not line:
                        break
                    
                    # 尝试解码输出，使用不同的编码
                    try:
                        line_str = line.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            line_str = line.decode('cp936')  # Windows中文编码
                        except UnicodeDecodeError:
                            line_str = line.decode('latin-1')  # 最后的后备方案
                    
                    # 收集错误信息
                    if 'error' in line_str.lower() or 'failed' in line_str.lower():
                        error_output.append(line_str.strip())
            except Exception as e:
                # 忽略输出读取过程中的错误，继续执行
                pass
            
            process.wait()
            
            if process.returncode == 0:
                try:
                    self.message_received.emit(f"转换成功: {display_file_name} -> {display_output_name}")
                except UnicodeEncodeError:
                    self.message_received.emit(f"转换成功: [文件路径包含特殊字符]")
                return True, output_path
            else:
                error_msg = "\n".join(error_output) if error_output else "未知错误"
                try:
                    self.message_received.emit(f"转换失败: {display_file_name}\n错误: {error_msg}")
                except UnicodeEncodeError:
                    self.message_received.emit(f"转换失败: [文件路径包含特殊字符]\n错误: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            # 捕获并处理所有异常，特别是编码相关的异常
            try:
                error_msg = f"处理文件时出错: {str(e)}"
                self.message_received.emit(error_msg)
            except UnicodeEncodeError:
                self.message_received.emit(f"处理文件时出错: 文件名或路径包含特殊字符")
            return False, str(e)
    
    def run(self):
        """线程主执行函数"""
        try:
            # 确保中文目录路径正确显示
            try:
                self.message_received.emit(f"开始扫描目录: {self.folder_path}")
            except UnicodeEncodeError:
                self.message_received.emit(f"开始扫描目录: [路径包含特殊字符]")
            
            # 查找音频文件
            audio_files = self.find_audio_files()
            total_files = len(audio_files)
            
            if total_files == 0:
                self.message_received.emit(f"未找到需要转换的音频文件")
                self.progress_updated.emit(100)
                self.download_completed.emit(True, "扫描完成，没有需要转换的文件")
                return
            
            self.message_received.emit(f"找到 {total_files} 个需要转换的音频文件")
            
            # 显示需要转换的文件列表 - 添加中文文件名的编码处理
            self.message_received.emit("需要转换的文件列表:")
            for file_path in audio_files:
                try:
                    file_name = os.path.basename(file_path)
                    self.message_received.emit(f"- {file_name}")
                except UnicodeEncodeError:
                    # 如果文件名包含无法编码的字符，则使用安全的显示方式
                    self.message_received.emit(f"- [文件名包含特殊字符]")
            
            # 开始转换文件
            success_count = 0
            fail_count = 0
            
            for i, file_path in enumerate(audio_files):
                if self.stop_requested:
                    self.download_completed.emit(False, "转换操作已取消")
                    return
                
                # 转换单个文件 - 确保文件路径使用Windows兼容的路径分隔符
                file_path = os.path.normpath(file_path)
                success, result = self.convert_file(file_path)
                
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                
                # 更新进度
                progress = int(((i + 1) / total_files) * 100)
                self.progress_updated.emit(progress)
            
            # 完成转换 - 添加异常处理
            try:
                self.progress_updated.emit(100)
                self.download_completed.emit(True, f"转换完成！成功: {success_count} 个, 失败: {fail_count} 个")
            except UnicodeEncodeError:
                self.download_completed.emit(True, f"转换完成！成功: {success_count} 个, 失败: {fail_count} 个")
            
        except Exception as e:
            # 捕获并处理所有异常，特别是编码相关的异常
            try:
                self.download_completed.emit(False, f"转换过程出错: {str(e)}")
            except UnicodeEncodeError:
                self.download_completed.emit(False, "转换过程出错: 编码相关错误")


# ===== 音频格式转换器窗口 =====
# 音频格式转换器设置文件路径
AUDIO_CONVERTER_SETTINGS_FILE = os.path.join(CONFIG_DIR, 'audio_converter_settings.pkl')

class AudioFormatConverterWindow(QWidget):
    """音频格式转换器主窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowFlags(Qt.WindowType.Window)
        self.init_ui()
        self.convert_thread = None  # 初始化转换线程变量
        # 设置窗口位置在上一个窗口的左上角
        if parent and parent.isVisible():
            parent_pos = parent.pos()
            self.move(parent_pos)
        # 加载保存的设置
        self.load_settings()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("音频格式转换工具_designed_by_wwq")
        self.setMinimumSize(600, 500)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 设置区域
        settings_group = QGroupBox("转换设置")
        settings_layout = QFormLayout()
        settings_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        settings_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        settings_layout.setSpacing(10)
        
        # 选择文件夹
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("请选择包含音频文件的文件夹")
        folder_browse_btn = QPushButton("浏览...")
        folder_browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(folder_browse_btn)
        settings_layout.addRow("文件夹路径:", folder_layout)
        
        # 目标格式选择
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "WAV", "M4A", "OGG", "FLAC", "OPUS"])
        self.format_combo.setCurrentIndex(0)  # 默认MP3格式
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        settings_layout.addRow("目标格式:", format_layout)
        
        # FFmpeg路径
        ffmpeg_layout = QHBoxLayout()
        self.ffmpeg_input = QLineEdit()
        ffmpeg_browse_btn = QPushButton("浏览...")
        ffmpeg_browse_btn.clicked.connect(self.browse_ffmpeg)
        ffmpeg_layout.addWidget(self.ffmpeg_input)
        ffmpeg_layout.addWidget(ffmpeg_browse_btn)
        settings_layout.addRow("FFmpeg路径:", ffmpeg_layout)
        
        # 覆盖选项
        self.overwrite_checkbox = QCheckBox("覆盖已存在的文件")
        settings_layout.addRow("覆盖设置:", self.overwrite_checkbox)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.scan_btn = QPushButton("扫描文件")
        self.scan_btn.clicked.connect(self.scan_files)
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)  # 初始禁用
        self.stop_btn = QPushButton("停止转换")
        self.stop_btn.clicked.connect(self.stop_conversion)
        self.stop_btn.setEnabled(False)  # 初始禁用
        self.find_duplicates_btn = QPushButton("查找重复文件")
        self.find_duplicates_btn.clicked.connect(self.find_duplicate_files)
        self.delete_by_suffix_btn = QPushButton("删除指定后缀名文件")
        self.delete_by_suffix_btn.clicked.connect(self.show_delete_by_suffix_dialog)
        self.delete_by_suffix_btn.setEnabled(False)  # 初始禁用
        
        btn_layout.addWidget(self.scan_btn)
        btn_layout.addWidget(self.convert_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.find_duplicates_btn)
        btn_layout.addWidget(self.delete_by_suffix_btn)
        settings_layout.addRow("", btn_layout)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 公共日志和进度区域
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("准备就绪")
        progress_layout.addWidget(self.progress_bar)
        
        log_group = QGroupBox("转换日志")
        log_layout = QVBoxLayout()
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        font = QFont()
        font.setPointSize(9)
        self.log_display.setFont(font)
        log_layout.addWidget(self.log_display)
        log_group.setLayout(log_layout)
        progress_layout.addWidget(log_group)
        
        main_layout.addLayout(progress_layout)
        
        self.setLayout(main_layout)
        self.setup_styles()
    
    def setup_styles(self):
        """设置界面样式，使用与视频下载器相似的风格"""
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
                color: #333;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                background-color: #009688;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00796B;
            }
            QPushButton:pressed {
                background-color: #00796B;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QProgressBar {
                height: 24px;
                border-radius: 4px;
                text-align: center;
                border: 1px solid #ccc;
            }
            QProgressBar::chunk {
                background-color: #009688;
                border-radius: 2px;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
                width: 25px;
                border-left: 1px solid #ccc;
                border-radius: 0 4px 4px 0;
            }
        """)
    
    def browse_folder(self):
        """浏览并设置文件夹路径"""
        path = QFileDialog.getExistingDirectory(self, "选择音频文件文件夹")
        if path:
            self.folder_input.setText(path)
            # 选择文件夹后启用扫描按钮和删除指定后缀名文件按钮
            self.scan_btn.setEnabled(True)
            self.delete_by_suffix_btn.setEnabled(True)
    
    def browse_ffmpeg(self):
        """浏览并设置FFmpeg路径"""
        filter_str = "可执行文件 (*.exe);;所有文件 (*)" if sys.platform.startswith('win') else "所有文件 (*)"
        path, _ = QFileDialog.getOpenFileName(self, "选择FFmpeg", "", filter_str)
        if path:
            self.ffmpeg_input.setText(path)
            
    def show_delete_by_suffix_dialog(self):
        """显示删除指定后缀名文件的对话框"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("删除指定后缀名文件")
        dialog.setMinimumSize(400, 200)
        
        # 创建布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 目录选择部分
        dir_layout = QHBoxLayout()
        dir_label = QLabel("选择要删除文件的目录:")
        self.delete_dir_edit = QLineEdit()
        self.delete_dir_edit.setText(self.folder_input.text())
        browse_dir_btn = QPushButton("浏览...")
        browse_dir_btn.clicked.connect(self.browse_delete_dir)
        
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.delete_dir_edit)
        dir_layout.addWidget(browse_dir_btn)
        
        # 后缀名输入部分
        suffix_layout = QHBoxLayout()
        suffix_label = QLabel("输入要删除的文件后缀名 (如: mp3, wav):")
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("多个后缀名用逗号分隔")
        
        suffix_layout.addWidget(suffix_label)
        suffix_layout.addWidget(self.suffix_input)
        
        # 选项部分
        options_layout = QHBoxLayout()
        self.include_subdirs_check = QCheckBox("包含子目录")
        self.include_subdirs_check.setChecked(True)
        self.confirm_before_delete_check = QCheckBox("删除前确认")
        self.confirm_before_delete_check.setChecked(True)
        
        options_layout.addWidget(self.include_subdirs_check)
        options_layout.addWidget(self.confirm_before_delete_check)
        options_layout.addStretch()
        
        # 按钮部分
        btn_layout = QHBoxLayout()
        start_delete_btn = QPushButton("开始删除")
        start_delete_btn.clicked.connect(lambda: self.delete_files_by_suffix(dialog))
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(start_delete_btn)
        btn_layout.addWidget(cancel_btn)
        
        # 添加到主布局
        main_layout.addLayout(dir_layout)
        main_layout.addLayout(suffix_layout)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(btn_layout)
        
        # 执行对话框
        dialog.exec()
    
    def browse_delete_dir(self):
        """浏览并设置要删除文件的目录"""
        path = QFileDialog.getExistingDirectory(self, "选择要删除文件的目录")
        if path:
            self.delete_dir_edit.setText(path)
    
    def scan_files(self):
        """扫描文件夹中的音频文件"""
        folder_path = self.folder_input.text().strip()
        target_format = self.format_combo.currentText().lower()
        
        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "路径错误", "请选择有效的文件夹路径")
            return
        
        # 确保中文路径正确显示
        try:
            self.append_log(f"开始扫描目录: {folder_path}")
        except UnicodeEncodeError:
            self.append_log(f"开始扫描目录: [路径包含特殊字符]")
        
        # 查找音频文件 - 标准化路径以处理Windows路径分隔符
        folder_path = os.path.normpath(folder_path)
        supported_formats = ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'opus', 'weba', 'flac', 'alac', 'wma']
        audio_files = []
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    try:
                        _, ext = os.path.splitext(file)
                        ext = ext[1:].lower()
                        if ext in supported_formats and ext != target_format:
                            # 确保添加的文件路径使用正确的路径分隔符
                            file_path = os.path.normpath(os.path.join(root, file))
                            audio_files.append(file_path)
                    except UnicodeEncodeError:
                        # 忽略无法处理的文件名
                        continue
        except Exception as e:
            try:
                self.append_log(f"扫描文件出错: {str(e)}")
            except UnicodeEncodeError:
                self.append_log("扫描文件出错: 路径包含特殊字符")
            return
        
        # 显示扫描结果
        total_files = len(audio_files)
        self.append_log(f"扫描完成，找到 {total_files} 个需要转换的音频文件")
        
        if total_files > 0:
            self.append_log("需要转换的文件列表:")
            for file_path in audio_files:
                try:
                    file_name = os.path.basename(file_path)
                    self.append_log(f"- {file_name}")
                except UnicodeEncodeError:
                    # 如果文件名包含无法编码的字符，则使用安全的显示方式
                    self.append_log(f"- [文件名包含特殊字符]")
            
            # 启用转换按钮
            self.convert_btn.setEnabled(True)
        else:
            self.append_log("没有找到需要转换的音频文件")
            self.convert_btn.setEnabled(False)
    
    def find_duplicate_files(self):
        """开始查找重复文件"""
        folder_path = self.folder_input.text().strip()
        
        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "路径错误", "请选择有效的文件夹路径")
            return
        
        # 禁用按钮防止重复操作
        self.find_duplicates_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.convert_btn.setEnabled(False)
        
        # 创建并启动重复文件查找线程
        self.duplicate_finder_thread = DuplicateFileFinderThread(folder_path)
        self.duplicate_finder_thread.progress_updated.connect(self.update_progress)
        self.duplicate_finder_thread.message_received.connect(self.append_log)
        self.duplicate_finder_thread.duplicates_found.connect(self.show_duplicate_files)
        self.duplicate_finder_thread.search_completed.connect(self.on_duplicate_search_completed)
        self.duplicate_finder_thread.current_file_processed.connect(self.update_current_processed_file)
        self.duplicate_finder_thread.duplicate_file_found.connect(self.append_duplicate_file_log)
        
        # 更新进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("查找重复文件中...")
        
        # 开始查找
        self.duplicate_finder_thread.start()
    
    def show_duplicate_files(self, duplicate_groups):
        """显示找到的重复文件列表"""
        if not duplicate_groups:
            return
        
        # 创建重复文件对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("重复文件列表")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 创建重复文件选择模型
        self.duplicate_file_model = QStandardItemModel()
        self.duplicate_file_model.setHorizontalHeaderLabels(["选择", "文件路径", "大小", "修改日期"])
        
        # 添加重复文件组
        for group_idx, file_group in enumerate(duplicate_groups):
            # 添加组标题
            group_title = QStandardItem(f"重复组 #{group_idx + 1} (共{len(file_group)}个文件)")
            group_title.setEditable(False)
            group_title.setBackground(QBrush(QColor(240, 240, 240)))
            self.duplicate_file_model.appendRow([group_title, QStandardItem(), QStandardItem(), QStandardItem()])
            
            # 添加文件信息
            for file_path in file_group:
                try:
                    # 获取文件信息
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    file_mtime = os.path.getmtime(file_path)
                    file_mtime_str = datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 创建可勾选的项目
                    check_item = QStandardItem()
                    check_item.setCheckable(True)
                    check_item.setCheckState(Qt.CheckState.Unchecked)
                    
                    # 文件名项目
                    file_item = QStandardItem(file_path)
                    file_item.setEditable(False)
                    
                    # 文件大小项目
                    size_item = QStandardItem(f"{file_size:.2f} MB")
                    size_item.setEditable(False)
                    
                    # 修改日期项目
                    date_item = QStandardItem(file_mtime_str)
                    date_item.setEditable(False)
                    
                    # 添加到模型
                    self.duplicate_file_model.appendRow([check_item, file_item, size_item, date_item])
                except Exception as e:
                    # 处理无法获取文件信息的情况
                    error_item = QStandardItem(f"{file_path} (无法获取文件信息: {str(e)})")
                    error_item.setEditable(False)
                    error_item.setForeground(QBrush(QColor(255, 0, 0)))
                    self.duplicate_file_model.appendRow([QStandardItem(), error_item, QStandardItem(), QStandardItem()])
        
        # 创建表格视图
        table_view = QTableView()
        table_view.setModel(self.duplicate_file_model)
        table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table_view.setAlternatingRowColors(True)
        
        # 设置第一列宽度
        table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        content_layout.addWidget(table_view)
        scroll_area.setWidget(content_widget)
        
        # 添加操作按钮
        btn_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(lambda: self.select_all_duplicates(True))
        
        deselect_all_btn = QPushButton("取消全选")
        deselect_all_btn.clicked.connect(lambda: self.select_all_duplicates(False))
        
        delete_btn = QPushButton("删除选中文件")
        delete_btn.clicked.connect(lambda: self.delete_selected_duplicates(dialog))
        
        # 添加后缀名删除按钮到操作按钮布局
        delete_by_suffix_btn = QPushButton("删除指定后缀名文件")
        delete_by_suffix_btn.clicked.connect(lambda: self.delete_files_by_suffix(dialog))
        
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(delete_by_suffix_btn)
        
        # 先添加滚动区域
        layout.addWidget(scroll_area)
        
        # 添加后缀名输入区域
        self.append_log("正在添加后缀名删除区域")
        suffix_layout = QHBoxLayout()
        suffix_label = QLabel("输入要删除的文件后缀名 (如: mp3, wav):")
        self.suffix_input = QLineEdit()
        self.suffix_input.setPlaceholderText("多个后缀名用逗号分隔")
        
        suffix_layout.addWidget(suffix_label)
        suffix_layout.addWidget(self.suffix_input)
        
        # 添加布局到对话框
        layout.addLayout(suffix_layout)
        layout.addLayout(btn_layout)
        
        # 调整对话框大小，确保所有内容可见
        dialog.resize(800, 600)
        
        try:
            # 显示对话框
            self.append_log("即将显示重复文件对话框")
            dialog.exec()
            self.append_log("重复文件对话框已关闭")
        except Exception as e:
            self.append_log(f"显示重复文件对话框时出错: {str(e)}")
    
    def select_all_duplicates(self, select):
        """全选或取消全选重复文件"""
        check_state = Qt.CheckState.Checked if select else Qt.CheckState.Unchecked
        
        for row in range(self.duplicate_file_model.rowCount()):
            item = self.duplicate_file_model.item(row, 0)
            if item and item.isCheckable():
                item.setCheckState(check_state)
    
    def delete_selected_duplicates(self, dialog):
        """删除选中的重复文件"""
        files_to_delete = []
        
        # 收集选中的文件
        for row in range(self.duplicate_file_model.rowCount()):
            check_item = self.duplicate_file_model.item(row, 0)
            file_item = self.duplicate_file_model.item(row, 1)
            
            if check_item and check_item.isCheckable() and check_item.checkState() == Qt.CheckState.Checked and file_item:
                file_path = file_item.text()
                if os.path.exists(file_path):
                    files_to_delete.append(file_path)
        
        if not files_to_delete:
            QMessageBox.information(self, "提示", "请先选择要删除的文件")
            return
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", f"确定要删除选中的 {len(files_to_delete)} 个文件吗？此操作不可恢复！",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            failed_count = 0
            
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    self.append_log(f"已删除重复文件: {file_path}")
                except Exception as e:
                    failed_count += 1
                    self.append_log(f"删除文件失败: {file_path}, 错误: {str(e)}")
            
            QMessageBox.information(self, "删除完成", 
                                  f"删除操作完成:\n成功删除 {deleted_count} 个文件\n删除失败 {failed_count} 个文件")
            
            # 关闭对话框
            dialog.accept()
            
    def delete_files_by_suffix(self, dialog):
        """根据用户指定的后缀名删除文件"""
        # 获取用户输入的后缀名
        suffix_text = self.suffix_input.text().strip()
        
        if not suffix_text:
            QMessageBox.warning(self, "输入错误", "请输入要删除的文件后缀名")
            return
        
        # 解析后缀名列表，支持逗号分隔多个后缀名
        suffixes = [s.strip().lower() for s in suffix_text.split(',') if s.strip()]
        
        if not suffixes:
            QMessageBox.warning(self, "输入错误", "请输入有效的文件后缀名")
            return
        
        # 记录开始搜索信息
        folder_path = self.folder_input.text().strip()
        suffix_list = ", ".join(suffixes)
        self.append_log(f"开始搜索指定后缀名文件: 目录={folder_path}, 后缀名={suffix_list}")
        
        # 收集匹配后缀名的文件
        files_to_delete = []
        
        # 获取要搜索的目录
        folder_path = self.delete_dir_edit.text().strip()
        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "路径错误", "请选择有效的文件夹路径")
            return
            
        # 标准化路径以处理Windows路径分隔符
        folder_path = os.path.normpath(folder_path)
        
        try:
            # 检查是否包含子目录
            include_subdirs = self.include_subdirs_check.isChecked()
            
            if include_subdirs:
                # 遍历目录及其子目录
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        try:
                            # 获取文件后缀名（不包含点）
                            _, file_ext = os.path.splitext(file)
                            file_ext = file_ext[1:].lower()  # 去掉点并转为小写
                            
                            # 检查文件后缀名是否匹配
                            if file_ext in suffixes:
                                # 确保添加的文件路径使用正确的路径分隔符
                                file_path = os.path.normpath(os.path.join(root, file))
                                files_to_delete.append(file_path)
                        except UnicodeEncodeError:
                            # 忽略无法处理的文件名
                            continue
            else:
                # 只遍历当前目录
                if os.path.exists(folder_path):
                    try:
                        for file in os.listdir(folder_path):
                            file_path = os.path.join(folder_path, file)
                            if os.path.isfile(file_path):
                                try:
                                    # 获取文件后缀名（不包含点）
                                    _, file_ext = os.path.splitext(file)
                                    file_ext = file_ext[1:].lower()  # 去掉点并转为小写
                                    
                                    # 检查文件后缀名是否匹配
                                    if file_ext in suffixes:
                                        # 确保添加的文件路径使用正确的路径分隔符
                                        file_path = os.path.normpath(file_path)
                                        files_to_delete.append(file_path)
                                except UnicodeEncodeError:
                                    # 忽略无法处理的文件名
                                    continue
                    except Exception as e:
                        self.append_log(f"读取目录文件出错: {str(e)}")
                        QMessageBox.warning(self, "错误", f"读取目录文件出错: {str(e)}")
                        return
        except Exception as e:
            try:
                self.append_log(f"搜索文件出错: {str(e)}")
            except UnicodeEncodeError:
                self.append_log(f"搜索文件出错: [错误信息包含特殊字符]")
            QMessageBox.warning(self, "错误", f"搜索文件出错: {str(e)}")
            return
        
        if not files_to_delete:
            suffix_list = ", ".join(suffixes)
            self.append_log(f"搜索完成: 没有找到后缀名为 {suffix_list} 的文件")
            QMessageBox.information(self, "提示", f"没有找到后缀名为 {suffix_list} 的文件")
            return
        
        # 记录搜索完成结果
        self.append_log(f"搜索完成: 找到 {len(files_to_delete)} 个需要删除的文件")
        
        # 显示找到的文件列表，并提供确认删除选项
        self.show_files_to_delete(files_to_delete, suffixes, dialog)
    
    def show_files_to_delete(self, files_to_delete, suffixes, dialog):
        """显示找到的文件列表对话框"""
        # 创建文件列表对话框
        files_dialog = QDialog(self)
        files_dialog.setWindowTitle("找到的文件")
        files_dialog.setMinimumSize(800, 600)
        
        # 设置布局
        layout = QVBoxLayout(files_dialog)
        
        # 创建文件列表标签
        suffix_list = ", ".join(suffixes)
        header_label = QLabel(f"找到 {len(files_to_delete)} 个后缀名为 {suffix_list} 的文件：")
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 创建文件列表容器
        files_container = QWidget()
        files_layout = QVBoxLayout(files_container)
        
        # 添加文件列表
        for file_path in files_to_delete:
            try:
                file_label = QLabel(file_path)
                file_label.setWordWrap(True)
                file_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                files_layout.addWidget(file_label)
            except UnicodeEncodeError:
                # 忽略无法显示的文件名
                continue
        
        # 添加垂直分隔空间
        files_layout.addStretch()
        
        # 将容器添加到滚动区域
        scroll_area.setWidget(files_container)
        
        # 创建按钮区域
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # 添加取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(files_dialog.reject)
        buttons_layout.addWidget(cancel_btn)
        
        # 添加删除按钮
        delete_btn = QPushButton("删除所选文件")
        delete_btn.setStyleSheet("background-color: #f44336; color: white;")
        delete_btn.clicked.connect(lambda: self.perform_delete_files(files_to_delete, suffixes, files_dialog, dialog))
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
        
        # 显示对话框
        files_dialog.exec()
        
    def perform_delete_files(self, files_to_delete, suffixes, files_dialog, parent_dialog):
        """执行文件删除操作"""
        # 确认删除
        suffix_list = ", ".join(suffixes)
        reply = QMessageBox.question(self, "最终确认删除", 
                                    f"确定要删除所有后缀名为 {suffix_list} 的 {len(files_to_delete)} 个文件吗？\n此操作不可恢复！",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 关闭文件列表对话框
        files_dialog.accept()
        
        # 执行删除操作
        deleted_count = 0
        failed_count = 0
        
        # 记录开始删除信息
        total_files = len(files_to_delete)
        self.append_log(f"开始删除文件: 总共 {total_files} 个文件")
        
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_count += 1
                self.append_log(f"已删除文件 (按后缀名): {file_path}")
            except Exception as e:
                failed_count += 1
                self.append_log(f"删除文件失败: {file_path}, 错误: {str(e)}")
        
        # 记录删除结果
        self.append_log(f"删除操作完成: 成功删除 {deleted_count} 个文件，删除失败 {failed_count} 个文件")
        
        QMessageBox.information(self, "删除完成", 
                              f"删除操作完成:\n成功删除 {deleted_count} 个文件\n删除失败 {failed_count} 个文件")
        
        # 关闭父对话框
        if parent_dialog:
            parent_dialog.accept()
    
    def on_duplicate_search_completed(self, success, message):
        """重复文件查找完成后的处理"""
        self.progress_bar.setFormat(message)
        
        # 重新启用按钮
        self.find_duplicates_btn.setEnabled(True)
        self.scan_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
    
    def start_conversion(self):
        """开始音频格式转换"""
        folder_path = self.folder_input.text().strip()
        ffmpeg_path = self.ffmpeg_input.text().strip()
        target_format = self.format_combo.currentText().lower()
        overwrite_existing = self.overwrite_checkbox.isChecked()
        
        # 验证输入
        if not folder_path or not os.path.exists(folder_path):
            QMessageBox.warning(self, "路径错误", "请选择有效的文件夹路径")
            return
        
        # 检查FFmpeg
        if not ffmpeg_path or not os.path.exists(ffmpeg_path):
            # 尝试自动查找FFmpeg
            auto_ffmpeg = M3U8VideoDownloadThread.find_ffmpeg()
            if os.path.exists(auto_ffmpeg):
                self.ffmpeg_input.setText(auto_ffmpeg)
                ffmpeg_path = auto_ffmpeg
            else:
                QMessageBox.warning(self, "配置错误", "处理音频格式需要FFmpeg，请设置有效的FFmpeg路径")
                return
        
        # 创建转换线程
        self.convert_thread = AudioFormatConverterThread(
            folder_path=folder_path,
            target_format=target_format,
            ffmpeg_path=ffmpeg_path,
            overwrite_existing=overwrite_existing
        )
        
        # 连接信号
        self.convert_thread.progress_updated.connect(self.update_progress)
        self.convert_thread.message_received.connect(self.append_log)
        self.convert_thread.download_completed.connect(self.conversion_finished)
        
        # 启动线程
        self.convert_thread.start()
        self.scan_btn.setEnabled(False)
        self.convert_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
    
    def stop_conversion(self):
        """停止转换过程"""
        if self.convert_thread and self.convert_thread.isRunning():
            self.append_log("正在停止转换线程...")
            self.convert_thread.stop()
            # 等待线程结束
            if not self.convert_thread.wait(5000):
                self.append_log("转换线程未能及时停止，强制终止")
                self.convert_thread.terminate()
                self.convert_thread.wait()
            self.convert_thread = None
            self.scan_btn.setEnabled(True)
            self.convert_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"{value}%")
    
    def append_log(self, message):
        """添加日志信息，确保中文正确显示"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            log_entry = f"[{timestamp}] {message}\n"
            self.log_display.insertPlainText(log_entry)
        except UnicodeEncodeError:
            # 如果消息包含无法编码的字符，使用安全的显示方式
            safe_message = "[消息包含特殊字符]"
            log_entry = f"[{timestamp}] {safe_message}\n"
            self.log_display.insertPlainText(log_entry)
        # 自动滚动到底部
        self.log_display.moveCursor(QTextCursor.MoveOperation.End)
        
    def update_current_processed_file(self, file_path):
        """更新当前正在处理的文件名"""
        # 更新进度条格式以显示当前处理的文件
        try:
            self.progress_bar.setFormat(f"正在计算: {os.path.basename(file_path)}")
        except UnicodeEncodeError:
            self.progress_bar.setFormat(f"正在计算: [文件名包含特殊字符]")
        
    def append_duplicate_file_log(self, duplicate_files):
        """实时添加发现的重复文件日志"""
        # 确保中文文件名正确显示
        try:
            base_names = [os.path.basename(file) for file in duplicate_files]
            self.append_log(f"发现重复文件: {', '.join(base_names)}")
        except UnicodeEncodeError:
            self.append_log(f"发现重复文件组")
    
    def conversion_finished(self, success, message):
        """转换完成后的处理"""
        self.append_log(message)
        self.scan_btn.setEnabled(True)
        self.convert_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.progress_bar.setFormat("转换完成")
            QMessageBox.information(self, "成功", message)
        else:
            self.progress_bar.setFormat("转换失败")
            QMessageBox.warning(self, "失败", message)
        
        self.convert_thread = None
    
    def disconnect_signals(self):
        """断开所有线程信号连接"""
        if self.convert_thread:
            try:
                self.convert_thread.progress_updated.disconnect()
                self.convert_thread.message_received.disconnect()
                self.convert_thread.download_completed.disconnect()
            except Exception:
                # 忽略已断开的信号
                pass
    
    def load_settings(self):
        """加载保存的设置"""
        try:
            # 确保配置目录存在
            if not os.path.exists(CONFIG_DIR):
                try:
                    os.makedirs(CONFIG_DIR)
                except Exception as e:
                    print(f"创建配置目录失败: {e}")
                    return
            
            # 尝试加载设置
            if os.path.exists(AUDIO_CONVERTER_SETTINGS_FILE):
                try:
                    with open(AUDIO_CONVERTER_SETTINGS_FILE, 'rb') as f:
                        settings = pickle.load(f)
                except Exception as e:
                    print(f"加载设置文件失败: {e}")
                    return
                
                # 应用设置
                if 'folder_path' in settings:
                    self.folder_input.setText(settings['folder_path'])
                if 'target_format' in settings:
                    index = self.format_combo.findText(settings['target_format'].upper())
                    if index >= 0:
                        self.format_combo.setCurrentIndex(index)
                if 'ffmpeg_path' in settings:
                    self.ffmpeg_input.setText(settings['ffmpeg_path'])
                if 'overwrite_existing' in settings:
                    self.overwrite_checkbox.setChecked(settings['overwrite_existing'])
            
            # 检查文件夹路径是否有效，如果有效则启用相关按钮
            folder_path = self.folder_input.text().strip()
            if folder_path and os.path.exists(folder_path):
                self.scan_btn.setEnabled(True)
                self.delete_by_suffix_btn.setEnabled(True)
            else:
                self.scan_btn.setEnabled(False)
                self.delete_by_suffix_btn.setEnabled(False)
        except Exception as e:
            print(f"加载设置时出错: {e}")
    
    def save_settings(self):
        """保存当前设置"""
        try:
            # 确保配置目录存在
            if not os.path.exists(CONFIG_DIR):
                try:
                    os.makedirs(CONFIG_DIR)
                except Exception as e:
                    print(f"创建配置目录失败: {e}")
                    return
            
            # 收集当前设置
            settings = {
                'folder_path': self.folder_input.text().strip(),
                'target_format': self.format_combo.currentText().lower(),
                'ffmpeg_path': self.ffmpeg_input.text().strip(),
                'overwrite_existing': self.overwrite_checkbox.isChecked()
            }
            
            # 保存设置
            with open(AUDIO_CONVERTER_SETTINGS_FILE, 'wb') as f:
                pickle.dump(settings, f)
        except Exception as e:
            print(f"保存设置时出错: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 保存当前设置
        self.save_settings()
        
        self.stop_conversion()
        self.disconnect_signals()
        # 将窗口添加到父窗口的子窗口列表中进行管理
        if self.parent and hasattr(self.parent, 'child_windows'):
            if self in self.parent.child_windows:
                self.parent.child_windows.remove(self)
        event.accept()



# ===== 应用程序打包图形界面 =====
class PackagingThread(QThread):
    """
    用于在单独线程中执行打包操作的QThread子类
    """
    # 定义信号，用于发送打包进度和结果
    progress_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    output_received = pyqtSignal(str)
    
    def __init__(self, python_file, app_name, is_single_file, spec_file=""):
        super().__init__()
        self.python_file = python_file
        self.app_name = app_name
        self.is_single_file = is_single_file
        self.spec_file = spec_file  # 添加spec文件路径参数
        self.overwrite_output = True  # 默认启用覆盖输出
    
    def _verify_spec_file_entry_point(self):
        """
        验证spec文件中的入口点文件是否存在
        这个方法会检查spec文件中的入口点并通过信号通知问题
        """
        try:
            # 读取spec文件内容
            with open(self.spec_file, 'r', encoding='utf-8') as f:
                spec_content = f.read()
                
            # 尝试提取Analysis部分中的第一个文件路径
            import re
            analysis_match = re.search(r'a\s*=\s*Analysis\(\s*\[([^\]]+)\]', spec_content)
            
            if analysis_match:
                entry_points_str = analysis_match.group(1)
                # 提取第一个文件路径（通常是主要的入口点）
                entry_point_match = re.search(r'[\\"\']([^\\"\']+\.py)[\\"\']', entry_points_str)
                
                if entry_point_match:
                    entry_point_path = entry_point_match.group(1)
                    
                    # 检查路径是否为绝对路径
                    if not os.path.isabs(entry_point_path):
                        # 假设相对路径是相对于spec文件所在的目录
                        spec_dir = os.path.dirname(self.spec_file)
                        entry_point_path = os.path.join(spec_dir, entry_point_path)
                    
                    # 检查文件是否存在
                    if not os.path.exists(entry_point_path):
                        error_msg = f"spec文件中指定的入口点文件不存在：\n{entry_point_path}\n\n" \
                                  "请修改spec文件或确保该文件存在于指定位置。"
                        self.finished.emit(False, error_msg)
                        raise FileNotFoundError(error_msg)
        except Exception as e:
            # 如果解析失败或文件不存在，发出错误信号
            self.finished.emit(False, f"验证spec文件时出错：{str(e)}")
            raise
        
    def run(self):
        """
        运行打包操作
        """
        try:
            self.progress_updated.emit("开始打包应用程序...")
            
            # 确保package_infor目录存在
            package_infor_dir = os.path.join(os.getcwd(), "package_infor")
            if not os.path.exists(package_infor_dir):
                os.makedirs(package_infor_dir)
                
            # 构建PyInstaller命令
            # 检查是否指定了spec文件
            if self.spec_file:
                # 再次验证spec文件中的入口点文件是否存在
                self._verify_spec_file_entry_point()
                # 使用现有的spec文件进行打包
                self.progress_updated.emit(f"使用现有的spec文件: {self.spec_file}")
                cmd = [
                    sys.executable, '-m', 'PyInstaller', self.spec_file,
                    '--clean',  # 清理临时文件
                    '--workpath', os.path.join(package_infor_dir, "build"),  # 指定临时文件路径
                    '--distpath', os.path.join(package_infor_dir, "dist")    # 指定输出目录路径
                ]
                # 如果设置了覆盖现有目录，添加-y选项
                if getattr(self, 'overwrite_output', True):
                    cmd.append('-y')
            else:
                # 使用Python文件进行打包，自动生成spec文件
                # 添加优化参数和修复QtWidgets DLL加载问题的参数
                cmd = [
                    sys.executable, '-m', 'PyInstaller', self.python_file,
                    '--name', self.app_name, '--windowed',
                    '--optimize=2',  # 启用最大优化级别
                    '--noupx',       # 不使用UPX压缩，避免DLL相关问题
                    '--clean',       # 清理临时文件，确保每次打包都是全新的
                    '--workpath', os.path.join(package_infor_dir, "build"),  # 指定临时文件路径
                    '--distpath', os.path.join(package_infor_dir, "dist"),    # 指定输出目录路径
                    '--specpath', package_infor_dir,                          # 指定spec文件路径
                    # 添加PyQt6相关的hiddenimports参数
                    '--hidden-import=PyQt6',
                    '--hidden-import=PyQt6.QtWidgets',
                    '--hidden-import=PyQt6.QtGui',
                    '--hidden-import=PyQt6.QtCore'
                ]
                # 如果设置了覆盖现有目录，添加-y选项
                if getattr(self, 'overwrite_output', True):
                    cmd.append('-y')
                
                # 根据选择添加打包方式参数
                if self.is_single_file:
                    cmd.append('--onefile')
            
            # 执行打包命令 - 不使用shell=True，以提高安全性和稳定性
            try:
                # 使用更宽松的编码处理Windows系统上的各种字符
                # cp936是Windows中文系统常用的编码，能够处理更多中文和特殊字符
                process = subprocess.Popen(
                    cmd,
                    shell=False,  # 不使用shell=True
                    stdout=subprocess.PIPE,  # 捕获标准输出
                    stderr=subprocess.STDOUT,  # 合并标准错误到标准输出
                    text=True,  # 以文本模式读取输出
                    encoding='cp936',  # 使用cp936编码代替utf-8
                    errors='replace'  # 遇到无法解码的字符时替换为替换字符
                )
                
                # 实时读取输出并发送信号
                output_lines = []
                while True:
                    try:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            # 检查是否还有剩余输出
                            remaining_output = process.stdout.read()
                            if remaining_output:
                                for line in remaining_output.split('\n'):
                                    if line.strip():
                                        output_lines.append(line.strip())
                                        self.output_received.emit(line.strip())
                            break
                        if output:
                            clean_output = output.strip()
                            output_lines.append(clean_output)
                            self.output_received.emit(clean_output)
                    except Exception as read_error:
                        # 捕获读取输出时可能出现的错误
                        error_msg = f"读取输出时出错: {str(read_error)}"
                        self.output_received.emit(error_msg)
                        break
                
                # 检查进程退出码
                if process.returncode is not None and process.returncode != 0:
                    # 收集完整的错误信息
                    error_info = f"打包失败，退出码: {process.returncode}\n"
                    # 显示最后50行输出，以便更全面地了解错误
                    error_info += "\n".join(output_lines[-50:])
                    # 强调重要的错误信息
                    error_info += "\n\n========= 重要提示 ========="
                    error_info += "\n请仔细检查以上错误信息，特别关注包含 'ERROR' 或 'Traceback' 的行。"
                    error_info += "\n常见问题可能是：缺少依赖库、Python文件路径错误、spec文件配置不正确等。"
                    error_info += "\n=========================="
                    raise subprocess.CalledProcessError(process.returncode, cmd, error_info)
            except subprocess.SubprocessError as subprocess_error:
                # 捕获子进程相关的错误
                self.progress_updated.emit("打包过程中子进程出错")
                # 安全地处理subprocess_error，避免在格式化时出现类型错误
                try:
                    error_str = str(subprocess_error)
                except Exception:
                    # 如果直接str()失败，尝试手动构建错误信息
                    error_str = f"子进程错误，类型: {type(subprocess_error).__name__}"
                    if hasattr(subprocess_error, 'cmd'):
                        error_str += f", 命令: {subprocess_error.cmd}"
                    if hasattr(subprocess_error, 'returncode'):
                        error_str += f", 退出码: {subprocess_error.returncode}"
                self.finished.emit(False, f"子进程错误: {error_str}")
                return
            
            # 确定打包后的文件路径
            try:
                # 确定PyInstaller实际使用的输出目录路径
                # 优先使用命令中指定的distpath
                package_infor_dir = os.path.join(os.getcwd(), "package_infor")
                default_dist_path = os.path.join(package_infor_dir, 'dist')
                
                # 根据打包类型构建文件或目录路径
                if self.is_single_file:
                    package_path = os.path.join(default_dist_path, f'{self.app_name}.exe')
                else:
                    package_path = os.path.join(default_dist_path, self.app_name)
                
                # 如果默认路径不存在，尝试其他可能的位置
                possible_paths = [package_path]
                if not os.path.exists(package_path):
                    # 尝试当前工作目录下的dist目录
                    alt_dist_path = os.path.join(os.getcwd(), 'dist')
                    if self.is_single_file:
                        possible_paths.append(os.path.join(alt_dist_path, f'{self.app_name}.exe'))
                    else:
                        possible_paths.append(os.path.join(alt_dist_path, self.app_name))
                
                # 遍历所有可能的路径，找到第一个存在的路径
                found_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        found_path = path
                        break
                
                # 如果没有找到任何路径，抛出异常
                if found_path is None:
                    paths_str = "\n".join(possible_paths)
                    raise FileNotFoundError(f"打包后的文件不存在。\n尝试的路径：\n{paths_str}")
                
                # 使用找到的实际路径
                package_path = found_path
                
                self.progress_updated.emit("应用程序打包成功！")
                self.finished.emit(True, package_path)
            except FileNotFoundError as file_error:
                self.progress_updated.emit("打包成功但文件未找到")
                self.finished.emit(False, f"文件未找到: {str(file_error)}")
        except subprocess.CalledProcessError as e:
            self.progress_updated.emit("打包失败")
            # 提供更详细的错误信息
            error_details = f"打包命令执行失败: {str(e)}"
            if hasattr(e, 'output') and e.output:
                error_details += f"\n\n详细输出:\n{e.output}"
            self.finished.emit(False, error_details)
        except Exception as e:
            self.progress_updated.emit("打包过程中发生错误")
            # 捕获所有其他异常并提供详细信息
            import traceback
            error_traceback = traceback.format_exc()
            error_msg = f"打包过程中发生错误: {str(e)}\n\n详细错误信息:\n{error_traceback}"
            self.finished.emit(False, error_msg)
    
    def __del__(self):
        """
        确保线程在对象被删除时停止
        处理线程对象可能已被销毁的情况
        """
        try:
            if self.isRunning():
                self.wait(1000)  # 最多等待1秒
        except RuntimeError:
            # 忽略C++对象已被销毁的错误
            pass

class PackageAppGUI(QMainWindow):
    """
    应用程序打包图形界面类
    """
    def __init__(self):
        super().__init__()
        self.python_file = ''  # 初始化python_file属性
        self.save_path = ""
        self.spec_file = ""  # 存储spec文件路径
        self.use_existing_spec = False  # 是否使用现有spec文件
        self.overwrite_output = True  # 是否覆盖现有输出目录（默认为True）
        # 设置配置文件目录和路径（使用相对路径）
        self.config_dir = "package_infor"
        self.config_file = os.path.join(self.config_dir, "package_settings.pkl")
        self.init_ui()
        # 加载保存的设置
        self.load_settings()
        
        # 初始化打包线程
        self.packaging_thread = None
        
    def init_ui(self):
        """
        初始化用户界面
        """
        # 设置窗口标题和大小
        self.setWindowTitle("应用程序打包工具_designed_by_wwq")
        self.setMinimumSize(700, 600)  # 大大增加窗口宽度
        self.resize(700, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)  # 减小内边距
        main_layout.setSpacing(12)  # 减小间距
        
        # 创建一个包含多个设置的水平布局
        settings_container = QWidget()
        settings_layout = QHBoxLayout(settings_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(10)
        
        # 左侧设置区域
        left_settings = QWidget()
        left_layout = QVBoxLayout(left_settings)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 应用程序入口文件选择
        file_layout = QHBoxLayout()
        file_label = QLabel("Python入口文件:")
        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.file_input.setPlaceholderText("请选择要打包的Python文件")
        browse_file_button = QPushButton("浏览...")
        browse_file_button.setMinimumWidth(80)
        browse_file_button.clicked.connect(self.browse_python_file)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_input, 1)  # 让输入框占据更多空间
        file_layout.addWidget(browse_file_button)
        left_layout.addLayout(file_layout)

        # 应用名称输入
        name_layout = QHBoxLayout()
        name_label = QLabel("应用程序名称:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入应用程序名称")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input, 1)  # 让输入框占据更多空间
        left_layout.addLayout(name_layout)
        
        # 右侧设置区域
        right_settings = QWidget()
        right_layout = QVBoxLayout(right_settings)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # 保存路径选择
        path_layout = QHBoxLayout()
        path_label = QLabel("保存路径:")
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        browse_button = QPushButton("浏览...")
        browse_button.setMinimumWidth(80)
        browse_button.clicked.connect(self.browse_save_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input, 1)  # 让输入框占据更多空间
        path_layout.addWidget(browse_button)
        right_layout.addLayout(path_layout)
        
        # 添加左右设置区域到容器
        settings_layout.addWidget(left_settings, 1)
        settings_layout.addWidget(right_settings, 1)
        main_layout.addWidget(settings_container)
        
        # 高级选项区域 - 横向排列
        advanced_options = QWidget()
        advanced_layout = QHBoxLayout(advanced_options)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setSpacing(10)
        
        # 打包方式选择 - 改为横向
        package_group = QGroupBox("打包方式")
        package_layout = QHBoxLayout()
        
        self.package_group = QButtonGroup()
        
        self.single_file_radio = QRadioButton("单一可执行文件 (.exe)")
        self.single_file_radio.setChecked(True)
        self.folder_radio = QRadioButton("文件夹形式 (包含多个文件)")
        
        self.package_group.addButton(self.single_file_radio)
        self.package_group.addButton(self.folder_radio)
        
        package_layout.addWidget(self.single_file_radio)
        package_layout.addWidget(self.folder_radio)
        package_group.setLayout(package_layout)
        advanced_layout.addWidget(package_group, 1)
        
        # Spec文件选择和覆盖输出选项组合成一个区域
        options_group = QGroupBox("选项")
        options_layout = QVBoxLayout()
        
        # Spec文件选择
        spec_layout = QHBoxLayout()
        self.spec_checkbox = QCheckBox("使用现有spec文件")
        self.spec_checkbox.stateChanged.connect(self.toggle_spec_selection)
        self.spec_input = QLineEdit()
        self.spec_input.setReadOnly(True)
        self.spec_input.setPlaceholderText("请选择spec文件")
        self.spec_input.setEnabled(False)  # 初始禁用
        browse_spec_button = QPushButton("浏览...")
        browse_spec_button.setMinimumWidth(80)
        browse_spec_button.clicked.connect(self.browse_spec_file)
        browse_spec_button.setEnabled(False)  # 初始禁用
        
        spec_layout.addWidget(self.spec_checkbox)
        spec_layout.addWidget(self.spec_input, 1)
        spec_layout.addWidget(browse_spec_button)
        options_layout.addLayout(spec_layout)
        
        # 覆盖输出目录选项
        overwrite_layout = QHBoxLayout()
        overwrite_label = QLabel("高级选项:")
        self.overwrite_checkbox = QCheckBox("覆盖现有输出目录")
        self.overwrite_checkbox.setChecked(True)  # 默认为选中
        self.overwrite_checkbox.stateChanged.connect(self.on_overwrite_checkbox_changed)
        overwrite_layout.addWidget(overwrite_label)
        overwrite_layout.addWidget(self.overwrite_checkbox, 1)
        options_layout.addLayout(overwrite_layout)
        
        options_group.setLayout(options_layout)
        advanced_layout.addWidget(options_group, 1)
        
        main_layout.addWidget(advanced_options)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 5, 0, 5)
        self.package_button = QPushButton("开始打包")
        self.package_button.setMinimumHeight(36)
        self.package_button.clicked.connect(self.package_app)
        self.save_settings_button = QPushButton("保存设置")
        self.save_settings_button.setMinimumHeight(36)
        self.save_settings_button.clicked.connect(self.save_settings)
        self.exit_button = QPushButton("退出")
        self.exit_button.setMinimumHeight(36)
        self.exit_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.package_button, 1)  # 均分空间
        button_layout.addWidget(self.save_settings_button, 1)  # 均分空间
        button_layout.addWidget(self.exit_button, 1)     # 均分空间
        main_layout.addLayout(button_layout)
        
        # 添加一个文本框用于显示打包过程信息
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("打包过程信息将显示在这里...")
        self.output_text.setMinimumHeight(250)  # 增加输出框高度，显示更多信息
        main_layout.addWidget(self.output_text)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # 美化UI
        self.setup_styles()
    
    def browse_python_file(self):
        """
        浏览并选择要打包的Python文件
        """
        # 打开文件选择对话框，过滤Python文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Python文件", os.getcwd(), "Python Files (*.py)"
        )
        
        if file_path:
            self.python_file = file_path
            self.file_input.setText(file_path)
            
            # 如果应用程序名称为空，自动从文件名填充
            if not self.name_input.text().strip():
                file_name = os.path.basename(file_path)
                app_name = os.path.splitext(file_name)[0]
                self.name_input.setText(app_name)

    def toggle_spec_selection(self, state):
        """
        切换spec文件选择的启用状态
        
        Args:
            state: 复选框的状态
        """
        enabled = state == Qt.CheckState.Checked.value
        self.spec_input.setEnabled(enabled)
        
        # 如果启用了spec文件选择，显示警告提醒用户确认spec文件内容
        if enabled:
            QMessageBox.information(
                self, "注意",
                "使用现有的spec文件时，请确保spec文件中指定的入口点文件路径正确！\n\n"
                "PyInstaller会严格按照spec文件中的配置执行打包，不会使用界面上选择的Python文件。"
            )

        
        # 查找spec文件的浏览按钮并设置其状态
        # 我们通过遍历所有按钮并检查其父级来确定哪个是spec文件的浏览按钮
        for child in self.findChildren(QPushButton):
            if child.text() == "浏览...":
                # 检查按钮的父级是否包含spec_input
                parent = child.parent()
                if parent and hasattr(parent, 'findChild'):
                    spec_input_sibling = parent.findChild(QLineEdit)
                    if spec_input_sibling and spec_input_sibling == self.spec_input:
                        child.setEnabled(enabled)
                        break
        
        self.use_existing_spec = enabled
        
    def browse_spec_file(self):
        """
        浏览并选择现有的spec文件
        """
        # 打开文件选择对话框，过滤spec文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择spec文件", os.getcwd(), "Spec Files (*.spec)"
        )
        
        if file_path:
            self.spec_file = file_path
            self.spec_input.setText(file_path)
            
            # 验证spec文件中的入口点文件是否存在
            self._verify_spec_file_entry_point_gui(file_path)
            
    def browse_save_path(self):
        """
        浏览并选择保存路径
        """
        # 打开目录选择对话框
        directory = QFileDialog.getExistingDirectory(
            self, "选择保存路径", os.path.expanduser("~")
        )
        
        if directory:
            self.save_path = directory
            self.path_input.setText(directory)
    
    def setup_styles(self):
        """
        设置美化的UI样式，使用Qt样式表设置各控件的外观
        """
        # 设置应用整体样式
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei";
            }
            QLabel {
                color: #333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
                color: #333;
            }
            QRadioButton {
                color: #333;
                font-size: 14px;
                padding: 4px;
            }
        """)
        
        # 设置按钮颜色
        palette = self.package_button.palette()
        palette.setColor(QPalette.ColorRole.Button, QColor(76, 175, 80))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        self.package_button.setPalette(palette)
        self.exit_button.setPalette(palette)
    
    def package_app(self):
        """
        使用PyInstaller打包应用程序（在线程中执行）
        """
        try:
            app_name = self.name_input.text().strip()
            if not app_name:
                QMessageBox.warning(self, "警告", "请输入应用程序名称")
                return False, ""
            
            if not hasattr(self, 'python_file') or not self.python_file:
                QMessageBox.warning(self, "警告", "请选择要打包的Python文件")
                return False, ""
            
            if not self.save_path:
                QMessageBox.warning(self, "警告", "请选择保存路径")
                return False, ""
            
            # 禁用打包按钮，防止重复点击
            self.package_button.setEnabled(False)
            self.exit_button.setEnabled(False)
            self.save_settings_button.setEnabled(False)
            
            # 清空之前的输出信息
            self.output_text.setText("")
            
            # 确保即使在错误情况下，打包线程对象也是有效的
            if not hasattr(self, 'packaging_thread') or self.packaging_thread is None or not self.packaging_thread.isFinished():
                # 如果线程不存在、为None或未完成，则创建新线程
                self.packaging_thread = PackagingThread(
                    self.python_file,
                    app_name,
                    self.single_file_radio.isChecked(),
                    self.spec_file if self.use_existing_spec else ""
                )
            else:
                # 重新创建线程
                self.packaging_thread = PackagingThread(
                    self.python_file,
                    app_name,
                    self.single_file_radio.isChecked(),
                    self.spec_file if self.use_existing_spec else ""
                )
            
            # 连接信号和槽
            self.packaging_thread.progress_updated.connect(self.update_status)
            self.packaging_thread.output_received.connect(self.update_output)
            self.packaging_thread.finished.connect(self.on_packaging_finished)
            
            # 启动线程
            self.packaging_thread.start()
            
        except Exception as e:
            self.status_label.setText(f"打包过程中发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"打包过程中发生错误: {str(e)}")
            # 恢复按钮状态
            self.package_button.setEnabled(True)
            self.exit_button.setEnabled(True)
            self.save_settings_button.setEnabled(True)
            return False, ""
        
        return True, ""  # 返回成功表示线程已启动
    


    # 以下是GUI类中的方法
    def _verify_spec_file_entry_point_gui(self, spec_file_path):
        """
        在GUI类中验证spec文件中的入口点文件是否存在
        这个方法会向用户显示警告对话框
        
        Args:
            spec_file_path: spec文件的路径
        """
        try:
            # 读取spec文件内容
            with open(spec_file_path, 'r', encoding='utf-8') as f:
                spec_content = f.read()
                
            # 尝试提取Analysis部分中的第一个文件路径
            # 这是一个简单的解析方法，仅适用于标准格式的spec文件
            import re
            analysis_match = re.search(r'a\s*=\s*Analysis\(\s*\[([^\]]+)\]', spec_content)
            
            if analysis_match:
                entry_points_str = analysis_match.group(1)
                # 提取第一个文件路径（通常是主要的入口点）
                entry_point_match = re.search(r'[\\"\']([^\\"\']+\.py)[\\"\']', entry_points_str)
                
                if entry_point_match:
                    entry_point_path = entry_point_match.group(1)
                    
                    # 检查路径是否为绝对路径
                    if not os.path.isabs(entry_point_path):
                        # 假设相对路径是相对于spec文件所在的目录
                        spec_dir = os.path.dirname(spec_file_path)
                        entry_point_path = os.path.join(spec_dir, entry_point_path)
                    
                    # 检查文件是否存在
                    if not os.path.exists(entry_point_path):
                        QMessageBox.warning(
                            self, "警告",
                            f"spec文件中指定的入口点文件不存在：\n{entry_point_path}\n\n"
                            "请修改spec文件或确保该文件存在于指定位置。"
                        )
        except Exception as e:
            # 如果解析失败，显示警告但不阻止用户继续
            self.status_label.setText(f"检查spec文件时出错：{str(e)}")
            
    def update_status(self, message):
        """
        更新状态标签
        """
        self.status_label.setText(message)
        
    def update_output(self, output):
        """
        更新打包过程输出信息，累积显示所有信息
        """
        try:
            # 确保输出不为空
            if not output or not output.strip():
                return
            
            # 确保在主线程中更新UI
            if QThread.currentThread() != self.thread():
                # 如果不是主线程，则使用信号槽机制在主线程中更新
                QMetaObject.invokeMethod(
                    self,
                    "update_output_slot",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, output)
                )
                return
            
            # 获取当前文本
            current_text = self.output_text.toPlainText()
            
            # 如果当前文本不为空，添加换行符
            if current_text:
                updated_text = f"{current_text}\n{output}"
            else:
                updated_text = output
            
            # 限制输出文本长度，避免内存占用过多
            # 先计算行数
            lines = updated_text.split('\n')
            max_lines = 200  # 增加保留的行数到200行，以便显示更多错误信息
            
            if len(lines) > max_lines:
                # 只保留最后max_lines行
                updated_text = '\n'.join(lines[-max_lines:])
            
            # 更新显示的文本
            self.output_text.setText(updated_text)
            
            # 自动滚动到底部
            self.output_text.verticalScrollBar().setValue(
                self.output_text.verticalScrollBar().maximum()
            )
        except Exception as e:
            # 防止在更新输出时出现问题导致整个应用崩溃
            error_msg = f"更新输出时出错: {str(e)}"
            print(error_msg)
            # 尝试在UI中显示错误信息
            try:
                if QThread.currentThread() == self.thread():
                    current_text = self.output_text.toPlainText()
                    if current_text:
                        self.output_text.setText(f"{current_text}\n{error_msg}")
                    else:
                        self.output_text.setText(error_msg)
                else:
                    # 如果不在主线程，则使用信号槽机制
                    QMetaObject.invokeMethod(
                        self, 
                        "update_output_slot", 
                        Qt.ConnectionType.QueuedConnection, 
                        Q_ARG(str, error_msg)
                    )
            except:
                # 如果仍然失败，至少记录到控制台
                pass
    
    @pyqtSlot(str)
    def update_output_slot(self, output):
        """
        用于在主线程中更新输出的槽函数
        """
        self.update_output(output)
        
    def on_packaging_finished(self, success, result):
        """
        处理打包完成事件
        """
        # 恢复按钮状态
        self.package_button.setEnabled(True)
        self.exit_button.setEnabled(True)
        self.save_settings_button.setEnabled(True)
        
        if success:
            # 打包成功，继续复制到指定路径
            if not self.copy_to_path(result):
                QMessageBox.warning(
                    self, "警告", 
                    "复制到指定路径失败，但应用程序已打包成功，可以在dist目录中找到文件。"
                )
        else:
            # 打包失败，先将错误信息添加到输出文本框
            try:
                if self.output_text.toPlainText():
                    self.output_text.append("\n\n==== 打包失败详细信息 ====")
                self.output_text.append(result)
                self.output_text.verticalScrollBar().setValue(
                    self.output_text.verticalScrollBar().maximum()
                )
            except Exception as e:
                print(f"更新输出文本失败: {str(e)}")
            
            # 然后显示错误对话框
            # 将长错误信息截断，只在对话框中显示部分内容
            if len(result) > 500:
                dialog_result = result[:500] + "...\n\n(更多错误信息请查看下方输出文本框)"
            else:
                dialog_result = result
            
            QMessageBox.critical(self, "错误", dialog_result)
    
    def on_overwrite_checkbox_changed(self, state):
        """
        处理覆盖输出目录复选框的状态变化
        
        Args:
            state: 复选框的状态
        """
        self.overwrite_output = (state == Qt.CheckState.Checked.value)
        
    def copy_to_path(self, source_path):
        """
        将打包后的文件复制到选择的保存路径（移至单独线程执行以避免UI阻塞）
        
        Args:
            source_path: 源文件路径
            
        Returns:
            bool: 复制线程是否成功启动
        """
        try:
            app_name = self.name_input.text().strip()
            
            # 检查源文件是否存在
            if not os.path.exists(source_path):
                QMessageBox.critical(self, "错误", f"源文件 '{source_path}' 不存在")
                return False
            
            # 创建复制文件的线程
            self.copy_thread = QThread()
            self.copy_worker = CopyFileWorker(source_path, self.save_path, app_name)
            self.copy_worker.moveToThread(self.copy_thread)
            
            # 连接信号和槽
            self.copy_thread.started.connect(self.copy_worker.run)
            self.copy_worker.progress_updated.connect(self.update_copy_progress)
            self.copy_worker.finished.connect(self.on_copy_finished)
            self.copy_worker.finished.connect(self.copy_thread.quit)
            self.copy_worker.finished.connect(self.copy_worker.deleteLater)
            self.copy_thread.finished.connect(self.copy_thread.deleteLater)
            
            # 启动线程
            self.copy_thread.start()
            self.status_label.setText(f"正在复制文件到 {self.save_path}...")
            return True
        except Exception as e:
            self.status_label.setText(f"复制文件时出错")
            QMessageBox.critical(self, "错误", f"复制文件时出错: {str(e)}")
            return False
    
    def update_copy_progress(self, message):
        """
        更新文件复制进度
        """
        self.status_label.setText(message)
        QApplication.processEvents()  # 定期更新UI
    
    def on_copy_finished(self, success, message):
        """
        处理文件复制完成事件
        """
        if success:
            self.status_label.setText(message)
            QMessageBox.information(
                self, "成功", 
                f"应用程序已成功打包并复制到\n{self.save_path}\n\n" +
                f"您可以前往该目录运行应用程序。"
            )
        else:
            self.status_label.setText(f"复制文件时出错")
            QMessageBox.critical(self, "错误", message)

class CopyFileWorker(QObject):
    """
    文件复制工作线程类
    用于在后台线程中执行文件复制操作，避免阻塞UI
    """
    progress_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, source_path, save_path, app_name):
        super().__init__()
        self.source_path = source_path
        self.save_path = save_path
        self.app_name = app_name
    
    def run(self):
        """
        执行文件复制操作
        """
        try:
            # 根据文件类型执行不同的复制操作
            if os.path.isfile(self.source_path):
                # 复制单个文件
                destination_file = os.path.join(self.save_path, f'{self.app_name}.exe')
                
                # 使用分块复制并显示进度
                self.copy_file_with_progress(self.source_path, destination_file)
                
                # 创建一个简单的批处理文件来启动应用程序
                batch_file = os.path.join(self.save_path, f'启动{self.app_name}.cmd')
                with open(batch_file, 'w', encoding='utf-8') as f:
                    f.write(f'@echo off\n"{destination_file}"\npause')
            else:
                # 复制整个文件夹
                destination_folder = os.path.join(self.save_path, self.app_name)
                # 如果目标文件夹已存在，则先删除
                if os.path.exists(destination_folder):
                    shutil.rmtree(destination_folder)
                
                # 使用自定义的目录复制函数，支持进度反馈
                self.copy_directory_with_progress(self.source_path, destination_folder)
            
            self.finished.emit(True, f"复制完成！{self.app_name}已成功复制到指定路径。")
        except Exception as e:
            self.finished.emit(False, f"复制文件时出错: {str(e)}")
    
    def copy_file_with_progress(self, src, dst):
        """
        分块复制文件并显示进度
        """
        buffer_size = 65536  # 64KB缓冲区
        total_size = os.path.getsize(src)
        copied_size = 0
        
        with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
            while True:
                buffer = fsrc.read(buffer_size)
                if not buffer:
                    break
                fdst.write(buffer)
                copied_size += len(buffer)
                
                # 每复制一定量的数据后更新进度
                if copied_size % (buffer_size * 10) == 0:
                    progress_percent = min(100, int(copied_size / total_size * 100))
                    self.progress_updated.emit(
                        f"正在复制文件到 {self.save_path}... {progress_percent}%"
                    )
    
    def copy_directory_with_progress(self, src, dst):
        """
        复制目录并显示进度
        """
        # 先计算总文件大小，用于显示进度
        total_size = 0
        for root, _, files in os.walk(src):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        
        # 创建目标目录
        os.makedirs(dst)
        
        # 复制文件
        copied_size = 0
        for root, dirs, files in os.walk(src):
            # 创建对应的子目录
            for dir_name in dirs:
                src_dir = os.path.join(root, dir_name)
                rel_path = os.path.relpath(src_dir, src)
                dst_dir = os.path.join(dst, rel_path)
                os.makedirs(dst_dir, exist_ok=True)
            
            # 复制文件
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, src)
                dst_file = os.path.join(dst, rel_path)
                
                # 使用分块复制
                buffer_size = 65536  # 64KB缓冲区
                file_size = os.path.getsize(src_file)
                
                with open(src_file, 'rb') as fsrc, open(dst_file, 'wb') as fdst:
                    while True:
                        buffer = fsrc.read(buffer_size)
                        if not buffer:
                            break
                        fdst.write(buffer)
                        copied_size += len(buffer)
                        
                        # 每复制一定量的数据后更新进度
                        if copied_size % (buffer_size * 10) == 0:
                            progress_percent = min(100, int(copied_size / total_size * 100))
                            self.progress_updated.emit(
                                f"正在复制文件到 {self.save_path}... {progress_percent}%"
                            )
    
    def save_settings(self):
        """
        保存用户设置到配置文件，并显示保存成功提示
        """
        try:
            # 确保配置文件目录存在
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                self.status_label.setText(f"创建配置目录: {self.config_dir}")
                QApplication.processEvents()
                
            # 收集设置信息
            settings = {
                "app_name": self.name_input.text().strip(),
                "save_path": self.save_path,
                "is_single_file": self.single_file_radio.isChecked(),
                "python_file": getattr(self, 'python_file', ''),
                "spec_file": getattr(self, 'spec_file', ''),
                "use_existing_spec": getattr(self, 'use_existing_spec', False),
                "overwrite_output": getattr(self, 'overwrite_output', True)
            }
            
            # 保存设置到文件
            with open(self.config_file, 'wb') as f:
                pickle.dump(settings, f)
                
            self.status_label.setText("设置已成功保存")
            QMessageBox.information(self, "成功", "设置已成功保存到配置文件")
            return True
        except Exception as e:
            self.status_label.setText(f"保存设置时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存设置时出错: {str(e)}")
            return False
            
    def load_settings(self):
        """
        从配置文件加载用户设置
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'rb') as f:
                    settings = pickle.load(f)
                    
                # 恢复设置
                if "app_name" in settings and settings["app_name"]:
                    self.name_input.setText(settings["app_name"])
                
                if "python_file" in settings and settings["python_file"]:
                    self.python_file = settings["python_file"]
                    self.file_input.setText(settings["python_file"])
                
                if "save_path" in settings and settings["save_path"]:
                    self.save_path = settings["save_path"]
                    self.path_input.setText(settings["save_path"])
                
                if "is_single_file" in settings:
                    if settings["is_single_file"]:
                        self.single_file_radio.setChecked(True)
                    else:
                        self.folder_radio.setChecked(True)
                        
                # 恢复spec文件相关设置
                if "spec_file" in settings:
                    self.spec_file = settings["spec_file"]
                    self.spec_input.setText(settings["spec_file"])
                    
                if "use_existing_spec" in settings:
                    self.use_existing_spec = settings["use_existing_spec"]
                    self.spec_checkbox.setChecked(settings["use_existing_spec"])
                    # 触发toggle_spec_selection以正确设置UI状态
                    self.toggle_spec_selection(
                        Qt.CheckState.Checked.value if settings["use_existing_spec"] else Qt.CheckState.Unchecked.value
                    )
                
                # 恢复覆盖输出目录设置
                if "overwrite_output" in settings:
                    self.overwrite_output = settings["overwrite_output"]
                    self.overwrite_checkbox.setChecked(settings["overwrite_output"])
                        
                self.status_label.setText("已加载保存的设置")
        except Exception as e:
            self.status_label.setText(f"加载设置失败，将使用默认设置")
    
    def save_settings(self):
        """
        保存用户设置到配置文件并显示保存成功提示
        """
        try:
            # 确保配置文件目录存在
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                self.status_label.setText(f"创建配置目录: {self.config_dir}")
                QApplication.processEvents()
                
            # 收集设置信息
            settings = {
                "app_name": self.name_input.text().strip(),
                "save_path": self.save_path,
                "is_single_file": self.single_file_radio.isChecked(),
                "python_file": getattr(self, 'python_file', ''),
                "spec_file": getattr(self, 'spec_file', ''),
                "use_existing_spec": getattr(self, 'use_existing_spec', False),
                "overwrite_output": getattr(self, 'overwrite_output', True)
            }
            
            # 保存设置到文件
            with open(self.config_file, 'wb') as f:
                pickle.dump(settings, f)
                
            self.status_label.setText("设置已成功保存")
            QMessageBox.information(self, "成功", "设置已成功保存到配置文件")
            return True
        except Exception as e:
            self.status_label.setText(f"保存设置时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存设置时出错: {str(e)}")
            return False
    
    def start_package(self):
        """
        开始打包流程
        """
        # 保存当前设置
        self.save_settings()
        
        # 启动打包流程（在线程中执行）
        self.package_app()
        # 注意：打包完成后，会在on_packaging_finished中自动处理复制到指定路径的操作



# ===== 应用程序设置对话框 =====
class SettingsDialog(QDialog):
    """
    应用程序设置对话框
    用于配置应用程序的各种设置选项
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("应用设置")
        self.setMinimumSize(400, 300)
        main_layout = QVBoxLayout(self)
        
        # 创建设置分组
        general_group = QGroupBox("通用设置")
        general_layout = QFormLayout()
        
        # 启动时显示欢迎信息选项
        self.show_welcome_check = QComboBox()
        self.show_welcome_check.addItems(["是", "否"])
        general_layout.addRow("启动时显示欢迎信息:", self.show_welcome_check)
        
        # 自动保存设置选项
        self.auto_save_check = QComboBox()
        self.auto_save_check.addItems(["是", "否"])
        general_layout.addRow("自动保存设置:", self.auto_save_check)
        
        # 最小化窗口选项
        self.minimize_to_tray_check = QComboBox()
        self.minimize_to_tray_check.addItems(["是", "否"])
        general_layout.addRow("最小化时隐藏到托盘:", self.minimize_to_tray_check)
        
        general_group.setLayout(general_layout)
        main_layout.addWidget(general_group)
        
        # 创建日志设置分组
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout()
        
        # 日志级别选择
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("日志级别:", self.log_level_combo)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        
        # 保存按钮
        save_button = QPushButton("保存设置")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        # 取消按钮
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # 加载设置
        self.load_settings()
        # 设置样式
        self.setup_styles()
        
    def setup_styles(self):
        """设置对话框样式，使其与日志查看器风格一致"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                min-width: 100px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
    def load_settings(self):
        """加载保存的设置，确保从infor文件夹读取"""
        try:
            # 确保infor文件夹存在
            if not os.path.exists(CONFIG_DIR):
                try:
                    os.makedirs(CONFIG_DIR)
                except Exception as e:
                    print(f"创建配置目录失败: {e}")
                    # 使用默认设置
                    self._apply_default_settings()
                    return
            
            # 尝试加载设置
            if os.path.exists(APP_SETTINGS_FILE):
                try:
                    with open(APP_SETTINGS_FILE, 'rb') as f:
                        settings = pickle.load(f)
                except Exception as e:
                    print(f"加载设置文件失败: {e}")
                    settings = {}
            else:
                settings = {}

            
            # 应用设置
            self.show_welcome_check.setCurrentIndex(0 if settings.get('show_welcome', True) else 1)
            self.auto_save_check.setCurrentIndex(0 if settings.get('auto_save', True) else 1)
            self.minimize_to_tray_check.setCurrentIndex(0 if settings.get('minimize_to_tray', True) else 1)
            
            # 设置日志级别
            log_level = settings.get('log_level', 'INFO')
            index = self.log_level_combo.findText(log_level)
            if index >= 0:
                self.log_level_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"加载设置失败: {e}")
            # 使用默认设置
            self._apply_default_settings()
            
    def _apply_default_settings(self):
        """应用默认设置"""
        self.show_welcome_check.setCurrentIndex(0)
        self.auto_save_check.setCurrentIndex(0)
        self.minimize_to_tray_check.setCurrentIndex(0)  # 默认允许最小化到托盘
        self.log_level_combo.setCurrentIndex(1)  # INFO级别
            
    def save_settings(self):
        """保存设置，确保保存到infor文件夹"""
        try:
            # 确保infor文件夹存在
            if not os.path.exists(CONFIG_DIR):
                try:
                    os.makedirs(CONFIG_DIR)
                    print(f"创建配置目录: {CONFIG_DIR}")
                except Exception as e:
                    print(f"创建配置目录失败: {e}")
                    QMessageBox.critical(self, "错误", f"无法创建配置目录: {str(e)}")
                    return
            
            # 收集设置
            settings = {
                'show_welcome': self.show_welcome_check.currentText() == '是',
                'auto_save': self.auto_save_check.currentText() == '是',
                'minimize_to_tray': self.minimize_to_tray_check.currentText() == '是',
                'log_level': self.log_level_combo.currentText()
            }
            
            # 保存到文件
            with open(APP_SETTINGS_FILE, 'wb') as f:
                pickle.dump(settings, f)
            
            # 应用日志级别设置
            log_level = getattr(logging, settings['log_level'])
            logger.setLevel(log_level)
            # 确保根日志记录器也应用相同的日志级别
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)
            
            # 显示保存成功消息
            QMessageBox.information(self, "成功", "设置已保存")
            
            # 关闭对话框
            self.accept()
        except Exception as e:
            print(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")


# ===== 日志查看器对话框类，用于显示应用日志 =====
class LogViewerDialog(QDialog):
    """日志查看器对话框类，用于显示应用日志"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("日志查看器")
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.load_logs()
        self.setup_styles()
        
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # 添加滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.log_text)
        
        main_layout.addWidget(scroll_area)
        
        # 创建按钮区域
        button_layout = QHBoxLayout()
        
        # 刷新按钮
        refresh_button = QPushButton("刷新日志")
        refresh_button.clicked.connect(self.load_logs)
        button_layout.addWidget(refresh_button)
        
        # 清空按钮
        clear_button = QPushButton("清空日志")
        clear_button.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_button)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        main_layout.addLayout(button_layout)
        
    def setup_styles(self):
        """设置对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QTextEdit {
                background-color: #ffffff;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
    def load_logs(self):
        """加载日志文件，支持解密加密的日志"""
        try:
            # 检查日志文件是否存在
            if os.path.exists(APP_LOG_FILE):
                # 使用加密工具读取和解密日志文件
                log_content = read_encrypted_logs(APP_LOG_FILE)
                         
                # 显示日志内容
                self.log_text.setPlainText(log_content)
                # 滚动到底部
                self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
            else:
                self.log_text.setPlainText("日志文件不存在")
        except Exception as e:
            print(f"加载日志失败: {e}")
            self.log_text.setPlainText(f"加载日志失败: {str(e)}")
            
    def clear_logs(self):
        """清空日志文件"""
        try:
            # 显示确认对话框
            reply = QMessageBox.question(
                self,
                "确认清空",
                "确定要清空所有日志吗？此操作不可恢复。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 清空日志文件
                if os.path.exists(APP_LOG_FILE):
                    open(APP_LOG_FILE, 'w').close()
                
                # 清空显示
                self.log_text.clear()
                
                # 记录清空操作
                logger.info("用户清空了日志文件")
        except Exception as e:
            print(f"清空日志失败: {e}")
            QMessageBox.critical(self, "错误", f"清空日志失败: {str(e)}")


# ===== 版本历史对话框 =====
class VersionHistoryDialog(QDialog):
    """
    版本历史对话框
    用于显示应用程序的版本更新历史
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("版本历史")
        self.setMinimumSize(500, 400)
        self.init_ui()
        self.setup_styles()
        
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建版本历史显示区域
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        
        # 添加滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.history_text)
        
        main_layout.addWidget(scroll_area)
        
        # 创建关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        # 填充版本历史
        self.fill_version_history()
        
    def setup_styles(self):
        """设置对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QTextEdit {
                background-color: #ffffff;
                font-family: SimHei, Microsoft YaHei, sans-serif;
                font-size: 13px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
    def fill_version_history(self):
        """填充版本历史信息"""
        history_content = []
        
        # 从全局变量中获取版本历史
        for version_info in VERSION_HISTORY:
            version = version_info["version"]
            date = version_info["date"]
            features = version_info["features"]
            
            # 添加版本信息
            history_content.append(f"=== 版本 {version} ({date}) ===\n")
            
            # 添加更新特性
            for i, feature in enumerate(features, 1):
                history_content.append(f"{i}. {feature}\n")
            
            # 添加空行分隔
            history_content.append("\n")
        
        # 设置内容
        self.history_text.setPlainText(''.join(history_content))



# ===== 主程序入口 =====
if __name__ == '__main__':
    # 创建应用程序实例
    app = QApplication(sys.argv)
    # 创建启动器窗口
    launcher = AppLauncher()
    # 显示窗口
    launcher.show()
    # 运行应用程序的主循环
    sys.exit(app.exec())