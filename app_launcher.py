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
    QToolButton, QSystemTrayIcon, QStyle, QMenu, QScrollArea
    
)
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor , QIcon , QPixmap, QGuiApplication, QRadialGradient, QPalette, QTextDocument
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QThread, pyqtSignal,QSettings, QRectF, QPointF

# ===== 设置日志配置 =====
import os
import sys
import logging
import pickle

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
            config_dir = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', 'C:\Temp')), 'app_infor')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
    
    return config_dir

# 初始化配置目录
CONFIG_DIR = get_config_dir()

# 配置文件路径
APP_LOG_FILE = os.path.join(CONFIG_DIR, 'app_log.txt')
APP_SETTINGS_FILE = os.path.join(CONFIG_DIR, 'app_settings.pkl')
GAME2048_HIGH_SCORE_FILE = os.path.join(CONFIG_DIR, '2048_high_score.txt')
SNAKE_HIGH_SCORE_FILE = os.path.join(CONFIG_DIR, 'snake_high_score.pickle')
DINO_GAME_SCORES_FILE = os.path.join(CONFIG_DIR, 'dino_game_scores.pkl')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(APP_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== 版本历史信息 =====
VERSION_HISTORY = [
    {
        "version": "1.0.0",
        "date": "2024-04-25",
        "features": [
            "优化俄罗斯方块游戏性能",
            "移除俄罗斯方块游戏音效功能",
            "优化游戏界面响应速度",
            "修复若干已知bug"
        ]
    },
    {
        "version": "0.95",
        "date": "2023-07-15",
        "features": [
            "添加小恐龙游戏",
            "添加俄罗斯方块游戏",
            "优化应用程序启动速度",
            "修复小说下载器的若干bug"
        ]
    },
    {
        "version": "0.90",
        "date": "2023-06-30",
        "features": [
            "添加小说下载器功能",
            "改进2048游戏界面",
            "优化贪吃蛇游戏控制"
        ]
    },
    {
        "version": "0.85",
        "date": "2023-06-15",
        "features": [
            "添加2048游戏",
            "添加贪吃蛇游戏",
            "基础框架搭建"
        ]
    }
]

# =======================================================
# 小恐龙游戏实现
# =======================================================
class DinoGame(QWidget):
    """
    小恐龙游戏主窗口类
    实现了简单的跳跃躲避游戏，玩家控制恐龙跳跃躲避障碍物，获取分数。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("小恐龙游戏")
        self.setMinimumSize(800, 400)
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
        self.game_canvas.setMinimumSize(800, 300)
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
            if hasattr(self, 'parent') and self.parent:
                save_path = DINO_GAME_SCORES_FILE
            if os.path.exists(save_path):
                with open(save_path, 'rb') as f:
                    self.high_score = pickle.load(f)
                    self.high_score_label.setText(f"最高分: {self.high_score}")
        except Exception as e:
            print(f"加载最高分失败: {e}")
            
    def save_high_score(self):
        """保存最高分记录"""
        try:
            import pickle
            if hasattr(self, 'parent') and self.parent:
                save_path = DINO_GAME_SCORES_FILE
            with open(save_path, 'wb') as f:
                pickle.dump(self.high_score, f)
        except Exception as e:
            print(f"保存最高分失败: {e}")
            
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
        self.last_score_time = current_time
        
        # 更新父窗口的分数显示
        if hasattr(self.parent, 'update_score'):
            self.parent.update_score(self.score)
        
        # 随着分数增加，增加游戏难度 - 提高速度增加的幅度
        self.game_speed = 6 + self.score // 800  # 每得800分增加一点速度，提高初始速度
        
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

# =======================================================
# 俄罗斯方块游戏实现
# =======================================================
class TetrisGame(QWidget):
    """
    俄罗斯方块游戏主窗口类
    实现了经典的俄罗斯方块游戏，玩家控制方块下落并填满行以消除得分。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("俄罗斯方块")
        self.setMinimumSize(600, 600)
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
        
        # 显示游戏结束对话框
        reply = QMessageBox.question(
            self,
            "游戏结束",
            f"游戏结束！\n你的分数: {self.score}\n消除行数: {self.lines}\n是否重新开始？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.restart_game()
            
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
        """更新分数显示"""
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

class AppLauncher(QMainWindow):
    """
    应用程序启动器主窗口类
    提供界面让用户选择要运行的应用程序
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
        """初始化用户界面"""
        # 设置窗口标题和尺寸
        self.setWindowTitle('Python_box_designed_by_wwq')
        self.setGeometry(100, 100, 500, 500)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建垂直布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建标题标签
        title_label = QLabel('Python_box')
        title_label.setFont(QFont("SimHei", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建游戏按钮组
        games_group = QGroupBox("游戏")
        games_layout = QVBoxLayout()
        games_group.setLayout(games_layout)
        games_layout.setSpacing(10)
        
        # 创建2048游戏按钮
        self.game2048_button = QPushButton('2048游戏')
        self.game2048_button.setFont(self.font)
        self.game2048_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
        self.game2048_button.clicked.connect(self.run_game2048)
        games_layout.addWidget(self.game2048_button)
        
        # 创建贪吃蛇游戏按钮
        self.snake_button = QPushButton('贪吃蛇游戏')
        self.snake_button.setFont(self.font)
        self.snake_button.setStyleSheet("background-color: #2196F3; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
        self.snake_button.clicked.connect(self.run_snake)
        games_layout.addWidget(self.snake_button)
        
        # 创建小恐龙游戏按钮
        if DinoGame:
            self.dino_button = QPushButton('小恐龙游戏')
            self.dino_button.setFont(self.font)
            self.dino_button.setStyleSheet("background-color: #9C27B0; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
            self.dino_button.clicked.connect(self.run_dino_game)
            games_layout.addWidget(self.dino_button)
        
        # 创建俄罗斯方块游戏按钮
        if TetrisGame:
            self.tetris_button = QPushButton('俄罗斯方块')
            self.tetris_button.setFont(self.font)
            self.tetris_button.setStyleSheet("background-color: #F44336; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
            self.tetris_button.clicked.connect(self.run_tetris_game)
            games_layout.addWidget(self.tetris_button)
        
        main_layout.addWidget(games_group)
        
        # 创建工具按钮组
        tools_group = QGroupBox("工具")
        tools_layout = QVBoxLayout()
        tools_group.setLayout(tools_layout)
        tools_layout.setSpacing(10)
        
        # 创建小说下载器按钮
        self.novel_downloader_button = QPushButton('小说下载器')
        self.novel_downloader_button.setFont(self.font)
        self.novel_downloader_button.setStyleSheet("background-color: #FF9800; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
        self.novel_downloader_button.clicked.connect(self.run_novel_downloader)
        tools_layout.addWidget(self.novel_downloader_button)
        
        main_layout.addWidget(tools_group)
        
        # 创建设置和日志按钮组
        settings_group = QGroupBox("设置与帮助")
        settings_layout = QHBoxLayout()
        settings_group.setLayout(settings_layout)
        
        # 创建设置按钮
        self.settings_button = QPushButton('设置')
        self.settings_button.setFont(self.font)
        self.settings_button.setStyleSheet("background-color: #607D8B; color: white; padding: 10px; border-radius: 5px; font-size: 14px;")
        self.settings_button.clicked.connect(self.show_settings)
        settings_layout.addWidget(self.settings_button)
        
        # 创建日志按钮
        self.log_button = QPushButton('查看日志')
        self.log_button.setFont(self.font)
        self.log_button.setStyleSheet("background-color: #607D8B; color: white; padding: 10px; border-radius: 5px; font-size: 14px;")
        self.log_button.clicked.connect(self.show_log)
        settings_layout.addWidget(self.log_button)
        
        # 创建版本历史按钮
        self.version_button = QPushButton('版本历史')
        self.version_button.setFont(self.font)
        self.version_button.setStyleSheet("background-color: #607D8B; color: white; padding: 10px; border-radius: 5px; font-size: 14px;")
        self.version_button.clicked.connect(self.show_version_history)
        settings_layout.addWidget(self.version_button)
        
        main_layout.addWidget(settings_group)
        
        # 创建状态栏
        self.statusBar().showMessage("欢迎使用Python_box")
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 连接窗口关闭事件
        self.closeEvent = self.on_close_event
        
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
                    # 如果设置不允许最小化到托盘，直接关闭程序
                    logger.info("应用程序根据设置直接关闭")
                    self.close()
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
        self._button_clicked_feedback(self.game2048_button)
        try:
            # 创建进度条窗口
            self.create_progress_window("启动2048游戏")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建2048游戏窗口，保留主窗口可见
            self.game2048_window = Game2048()
            
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
            self._reset_button_style(self.game2048_button, "#4CAF50")
        
    def run_snake(self):
        """运行贪吃蛇游戏，保留主窗口并显示进度条"""
        self._button_clicked_feedback(self.snake_button)
        try:
            # 创建进度条窗口
            self.create_progress_window("启动贪吃蛇游戏")
            
            # 启动进度更新
            self.update_progress()
            
            # 创建贪吃蛇游戏窗口，保留主窗口可见
            self.snake_window = SnakeGame()
            
            # 完成进度显示
            self.finalize_progress()
            
            # 显示游戏窗口
            self.snake_window.show()
        except Exception as e:
            # 如果出现异常，确保进度窗口关闭
            if self.progress_window:
                self.progress_window.close()
            QMessageBox.critical(self, '错误', f'无法运行贪吃蛇游戏: {str(e)}')
            self._reset_button_style(self.snake_button, "#2196F3")
        
    def run_novel_downloader(self):
        """运行小说下载器，保留主窗口并显示进度条"""
        self._button_clicked_feedback(self.novel_downloader_button)
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
            self._reset_button_style(self.novel_downloader_button, "#FF9800")
            # 记录错误日志
            self.log_action(error_msg, "error")
        
    def run_dino_game(self):
        """运行小恐龙游戏，保留主窗口并显示进度条"""
        if not DinoGame:
            QMessageBox.warning(self, "警告", "小恐龙游戏模块不可用，请确保dino_game.py文件存在且可导入。")
            return
        
        self._button_clicked_feedback(self.dino_button)
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
            self._reset_button_style(self.dino_button, "#9C27B0")
            # 记录错误日志
            self.log_action(error_msg, "error")
        
    def run_tetris_game(self):
        """运行俄罗斯方块游戏，保留主窗口并显示进度条"""
        if not TetrisGame:
            QMessageBox.warning(self, "警告", "俄罗斯方块游戏模块不可用，请确保tetris_game.py文件存在且可导入。")
            return
        
        self._button_clicked_feedback(self.tetris_button)
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
            self._reset_button_style(self.tetris_button, "#F44336")
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
        从app_settings.pkl文件中加载保存的设置
        返回: 包含设置的字典
        """
        try:
            import pickle
            
            # 尝试加载设置
            if os.path.exists(APP_SETTINGS_FILE):
                with open(APP_SETTINGS_FILE, 'rb') as f:
                    settings = pickle.load(f)
                logging.info("成功加载应用设置")
                return settings
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
            log_viewer = LogViewer(self)
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
        self.setWindowTitle('2048游戏')
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
        self.setWindowTitle('贪吃蛇游戏')
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
    # 定义信号：下载计时（传递已用时间和预估时间，单位为秒）
    download_timing = pyqtSignal(float, float)
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
        self.setWindowTitle("小说下载器")
        self.setMinimumSize(600 , 600)
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
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12 , 12 , 12 , 12)  # 减小内边距
        main_layout.setSpacing(12)  # 减小间距
        
        # 创建设置区域分组
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        
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
        self.total_chapters_input.setRange(0 , 9999)
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
        
        # 将设置组添加到主布局
        settings_layout.addWidget(chapter_group)
        settings_layout.addWidget(download_group)
        main_layout.addLayout(settings_layout)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 5, 0, 5)
        
        self.download_button = QPushButton("开始下载")
        self.download_button.setIcon(QIcon.fromTheme("download"))
        self.download_button.setMinimumHeight(36)
        self.download_button.clicked.connect(self.start_download)
        
        self.stop_button = QPushButton("停止下载")
        self.stop_button.setIcon(QIcon.fromTheme("process-stop"))
        self.stop_button.setMinimumHeight(36)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_download)
        
        self.open_file_button = QPushButton("打开已下载文件")
        self.open_file_button.setIcon(QIcon.fromTheme("document-open"))
        self.open_file_button.setMinimumHeight(36)
        self.open_file_button.clicked.connect(self.open_downloaded_file)
        
        button_layout.addWidget(self.download_button, 1)  # 均分空间
        button_layout.addWidget(self.stop_button, 1)      # 均分空间
        button_layout.addWidget(self.open_file_button, 1) # 均分空间
        main_layout.addLayout(button_layout)
        
        # 进度条 - 显示下载进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("准备中...")
        main_layout.addWidget(self.progress_bar)
        
        # 下载计时信息
        timing_layout = QHBoxLayout()
        timing_layout.setSpacing(20)
        self.elapsed_time_label = QLabel("已用时间: --")
        self.estimated_time_label = QLabel("预估时间: --")
        timing_layout.addWidget(self.elapsed_time_label)
        timing_layout.addWidget(self.estimated_time_label)
        main_layout.addLayout(timing_layout)
        
        # 日志显示框 - 显示下载过程中的信息和错误
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setPlaceholderText("下载日志将显示在这里...")
        # 设置较小的字体
        font = QFont()
        font.setPointSize(9)
        self.log_display.setFont(font)
        # 设置日志区域为可拉伸
        self.log_display.setSizePolicy(QSizePolicy.Policy.Expanding , QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.log_display)
        
        # 文件内容显示窗口
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        self.content_display.setPlaceholderText("已打开的文件内容将显示在这里...")
        self.content_display.setSizePolicy(QSizePolicy.Policy.Expanding , QSizePolicy.Policy.Expanding)
        self.content_display.setVisible(False)  # 初始隐藏
        main_layout.addWidget(self.content_display)
        
        self.setLayout(main_layout)
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

class SettingsDialog(QDialog):
    """
    应用程序设置对话框
    用于配置应用程序的各种设置选项
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("应用设置")
        self.setMinimumSize(400, 300)
        self.init_ui()
        self.load_settings()
        self.setup_styles()
        
    def init_ui(self):
        """初始化用户界面"""
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
        
    def setup_styles(self):
        """设置对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
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
        """加载保存的设置"""
        try:
            # 尝试加载设置
                if os.path.exists(APP_SETTINGS_FILE):
                    with open(APP_SETTINGS_FILE, 'rb') as f:
                        settings = pickle.load(f)

                    
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
            self.show_welcome_check.setCurrentIndex(0)
            self.auto_save_check.setCurrentIndex(0)
            self.minimize_to_tray_check.setCurrentIndex(0)  # 默认允许最小化到托盘
            self.log_level_combo.setCurrentIndex(1)  # INFO级别
            
    def save_settings(self):
        """保存设置"""
        try:
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
            
            # 显示保存成功消息
            QMessageBox.information(self, "成功", "设置已保存")
            
            # 关闭对话框
            self.accept()
        except Exception as e:
            print(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")

class LogViewer(QDialog):
    """
    日志查看器对话框
    用于查看应用程序的日志信息
    """
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
        """加载日志文件"""
        try:
            # 检查日志文件是否存在
            if os.path.exists(APP_LOG_FILE):
                # 尝试使用不同的编码方式读取日志文件
                encodings = ['utf-8', 'gbk', 'latin-1']
                log_content = ""
                for encoding in encodings:
                    try:
                        with open(APP_LOG_FILE, 'r', encoding=encoding) as f:
                            log_content = f.read()
                        # 如果成功读取，记录使用的编码方式
                        print(f"成功使用{encoding}编码读取日志文件")
                        break
                    except UnicodeDecodeError:
                        continue
                        
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