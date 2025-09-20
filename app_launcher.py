#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用程序启动器
用于启动以下三个应用程序：
1. 2048游戏
2. 贪吃蛇游戏
3. 小说下载器

该启动器将三个应用程序集成到一个界面中，通过按钮选择启动不同的应用。
"""
import sys
import os
import random
import time
import pickle
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QGridLayout, QProgressBar, QTextEdit,
    QFileDialog, QLineEdit, QDialog, QGroupBox,
    QFormLayout, QSpinBox, QSizePolicy, QFrame
    
)
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor , QIcon , QPixmap, QGuiApplication, QRadialGradient, QPalette
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QThread, pyqtSignal,QSettings, QRectF, QPointF

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
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和尺寸
        self.setWindowTitle('应用程序启动器')
        self.setGeometry(100, 100, 400, 300)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建垂直布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建标题标签
        title_label = QLabel('请选择要运行的应用程序')
        title_label.setFont(self.font)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建按钮布局
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        # 创建2048游戏按钮
        self.game2048_button = QPushButton('2048游戏')
        self.game2048_button.setFont(self.font)
        self.game2048_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
        self.game2048_button.clicked.connect(self.run_game2048)
        buttons_layout.addWidget(self.game2048_button)
        
        # 创建贪吃蛇游戏按钮
        self.snake_button = QPushButton('贪吃蛇游戏')
        self.snake_button.setFont(self.font)
        self.snake_button.setStyleSheet("background-color: #2196F3; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
        self.snake_button.clicked.connect(self.run_snake)
        buttons_layout.addWidget(self.snake_button)
        
        # 创建小说下载器按钮
        self.novel_downloader_button = QPushButton('小说下载器')
        self.novel_downloader_button.setFont(self.font)
        self.novel_downloader_button.setStyleSheet("background-color: #FF9800; color: white; padding: 15px; border-radius: 5px; font-size: 16px;")
        self.novel_downloader_button.clicked.connect(self.run_novel_downloader)
        buttons_layout.addWidget(self.novel_downloader_button)
        
        main_layout.addLayout(buttons_layout)
        
        # 创建说明标签
        info_label = QLabel('点击上方按钮启动相应的应用程序')
        info_label.setFont(self.font)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)
        
        # 居中显示窗口
        self.center_window()
        
    def center_window(self):
        """将窗口显示在屏幕中央偏上位置"""
        screen = self.screen().geometry()
        size = self.geometry()
        # 让窗口上移30像素，使视觉效果更好
        self.move((screen.width() - size.width()) // 2, 
                  ((screen.height() - size.height()) // 2) - 30)
    
    def run_game2048(self):
        """运行2048游戏，保留主窗口"""
        self._button_clicked_feedback(self.game2048_button)
        try:
            # 创建并显示2048游戏窗口，保留主窗口可见
            self.game2048_window = Game2048()
            self.game2048_window.show()
            # 显示后再次调用居中方法，确保窗口正确居中
            self.game2048_window.center_window()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法运行2048游戏: {str(e)}')
            self._reset_button_style(self.game2048_button, "#4CAF50")
        
    def run_snake(self):
        """运行贪吃蛇游戏，保留主窗口"""
        self._button_clicked_feedback(self.snake_button)
        try:
            # 创建并显示贪吃蛇游戏窗口，保留主窗口可见
            self.snake_window = SnakeGame()
            self.snake_window.show()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法运行贪吃蛇游戏: {str(e)}')
            self._reset_button_style(self.snake_button, "#2196F3")
        
    def run_novel_downloader(self):
        """运行小说下载器，保留主窗口"""
        self._button_clicked_feedback(self.novel_downloader_button)
        try:
            # 创建并显示小说下载器窗口，保留主窗口可见
            self.novel_window = NovelDownloadWindow()
            self.novel_window.show()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法运行小说下载器: {str(e)}')
            self._reset_button_style(self.novel_downloader_button, "#FF9800")
    
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
        else:
            return "#4CAF50"  # 默认颜色
    
    def _show_launcher(self):
        """重新显示启动器窗口"""
        # 确保所有子窗口都已关闭
        QTimer.singleShot(100, self.show)
        
    def _on_child_window_close(self, event):
        """处理子窗口关闭事件的回调函数"""
        # 确保事件被接受，窗口可以正常关闭
        event.accept()
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
            with open('2048_high_score.txt', 'w') as f:
                f.write(str(self.high_score))
        except Exception as e:
            # 如果保存失败，忽略错误
            pass
    
    def load_high_score(self):
        """从文件加载最高分"""
        try:
            with open('2048_high_score.txt', 'r') as f:
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
        self.high_score_file = 'snake_high_score.pickle'
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
        # 设置字体
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        
        # 设置文本颜色
        painter.setPen(QColor(255, 152, 0))
        
        # 创建半透明背景
        background_rect = QRectF(self.width() / 3, self.height() / 3, 
                               self.width() / 3, self.height() / 3)
        painter.fillRect(background_rect, QColor(0, 0, 0, 128))
        
        # 绘制暂停消息
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "游戏暂停")

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
        1. 从起始URL开始，依次下载每个章节内容
        2. 解析页面找到章节内容并写入文件
        3. 自动查找下一章链接，继续下载直到完成或被停止
        4. 通过信号实时反馈进度和状态
        """
        try :
            self.message_received.emit("开始下载小说...")
            url = self.start_url  # 初始化当前URL为起始URL
            # 打开文件准备写入（使用utf-8编码避免中文乱码）
            with open(self.file_path , 'w' , encoding = 'utf-8') as f :
                # 循环下载：当前URL有效且未收到停止请求时继续
                while url and not self.stop_requested :
                    c=0
                    wait_time = random.randint(10,20)/10
                    self.current_chapter += 1  # 章节计数递增
                    # 计算并发送进度
                    if self.total_chapters :
                        # 已知总章节数时，按实际比例计算进度（0-100）
                        progress = min(100 , int(self.current_chapter / self.total_chapters * 100))
                    else :
                        # 未知总章节数时，用当前章节数估算进度（最高99%，避免提前显示完成）
                        progress = min(99 , int(self.current_chapter / max(1 , self.current_chapter) * 100))
                    self.progress_updated.emit(progress)
                    # 发送当前下载状态日志
                    self.message_received.emit(f"正在下载第 {self.current_chapter} 章: {url}")
                    # 发送HTTP请求获取章节页面
                    response = requests.get(url)
                    # 自动识别页面编码，避免中文乱码
                    response.encoding = response.apparent_encoding
                    # 解析HTML内容
                    soup = BeautifulSoup(response.text , 'html.parser')
                    # 定位章节内容（根据指定的标签和属性）
                    content = soup.find(self.tag , self.attr_dict)
                    if content :
                        # 提取文本内容并写入文件，章节间添加空行分隔
                        chapter_text = content.get_text()
                        f.write(chapter_text + '\n\n')
                        self.message_received.emit(f"成功下载第 {self.current_chapter} 章")
                    else :
                        # 未找到内容时记录警告日志
                        self.message_received.emit(f"未找到第 {self.current_chapter} 章内容: {url}")
                    # 查找下一章链接
                    next_link = None
                    # 可能的"下一章"文本集合（支持多语言和符号）
                    next_texts = self.choose_dict
                    for next_text in next_texts :
                        # 精确匹配链接文本
                        next_link_element = soup.find('a' , string = next_text)
                        if next_link_element :
                            # 拼接相对URL为绝对URL
                            next_link = urljoin(url , next_link_element.get('href'))
                            break
                    # 如果未找到精确匹配的下一章链接，尝试模糊匹配
                    if not next_link :
                        # 获取所有<a>标签逐一检查
                        next_link_elements = soup.find_all('a')
                        for element in next_link_elements :
                            # 模糊匹配包含"下一章"或"next"的链接
                            if '下一章' in element.get_text() or 'next' in element.get_text().lower() :
                                next_link = urljoin(url , element.get('href'))
                                break
                    # 更新下一章URL，准备下一轮循环
                    url = next_link
                    # 延迟1-2秒，避免请求过于频繁被服务器拦截
                    self.message_received.emit(f"正在延迟请求{wait_time}秒")
                    time.sleep(wait_time)
            # 循环结束后判断退出原因
            if not self.stop_requested :
                # 正常完成下载
                self.download_completed.emit(True , f"小说下载完成！共下载 {self.current_chapter} 章")
            else :
                # 被用户停止下载
                self.download_completed.emit(False , "下载已取消")
        except Exception as e :
            # 下载过程中发生异常，发送失败信号
            self.download_completed.emit(False , f"下载失败: {str(e)}")
    """
    请求停止下载操作。
    通过设置停止标志位，让run()方法中的循环正常退出，避免线程强制终止导致的资源泄露。
    """
    def stop(self) :
        self.stop_requested = True

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
        self.url_input = QLineEdit()
        self.url_input.setToolTip("输入小说章节的起始URL")
        chapter_form.addWidget(self.url_input, 0, 1)
        
        # 标签输入框 - 用于指定小说章节内容的HTML标签
        chapter_form.addWidget(QLabel("内容标签:"), 0, 2)
        self.tag_input = QLineEdit()
        self.tag_input.setToolTip("输入包含章节内容的HTML标签名称")
        chapter_form.addWidget(self.tag_input, 0, 3)
        
        # 属性输入框 - 用于指定章节内容标签的属性
        chapter_form.addWidget(QLabel("内容属性:"), 1, 0)
        self.attr_input = QLineEdit()
        self.attr_input.setToolTip("输入内容标签的属性，格式为：属性名=属性值")
        chapter_form.addWidget(self.attr_input, 1, 1)
        
        # 选择器输入框 - 用于指定章节下一章按钮标签
        chapter_form.addWidget(QLabel("下一章按钮文字:"), 1, 2)
        self.choose_input = QLineEdit()
        self.choose_input.setToolTip("输入下一章按钮的文本内容，多个用逗号分隔")
        chapter_form.addWidget(self.choose_input, 1, 3)
        
        # 自动检测属性区域
        detect_layout = QHBoxLayout()
        detect_layout.setSpacing(8)
        
        # 关键词输入框 - 用于自动检测属性的关键词
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入章节中的部分文字")
        self.keyword_input.setToolTip("输入章节内容中包含的文字，用于自动检测属性")
        detect_layout.addWidget(QLabel("检测关键词:"), 0)
        detect_layout.addWidget(self.keyword_input, 1)  # 让输入框占据更多空间
        
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
        self.path_input = QLineEdit()
        browse_button = QPushButton("浏览...")
        browse_button.setMinimumWidth(80)
        browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_input, 1)  # 让输入框占据更多空间
        path_layout.addWidget(browse_button)
        download_form.addLayout(path_layout)
        
        # 文件名和章节数横向排列
        file_chapter_layout = QHBoxLayout()
        file_chapter_layout.setSpacing(15)
        
        # 文件名设置
        filename_sub_layout = QHBoxLayout()
        filename_sub_layout.addWidget(QLabel("保存文件名:"))
        self.filename_input = QLineEdit()
        self.filename_input.setText("小说.txt")
        self.filename_input.setToolTip("设置保存的小说文件名")
        self.filename_input.setMinimumWidth(150)
        filename_sub_layout.addWidget(self.filename_input)
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
        
        button_layout.addWidget(self.download_button, 1)  # 均分空间
        button_layout.addWidget(self.stop_button, 1)      # 均分空间
        main_layout.addLayout(button_layout)
        
        # 进度条 - 显示下载进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("准备中...")
        main_layout.addWidget(self.progress_bar)
        
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
        if value < 100:
            self.progress_bar.setFormat(f"下载中: {value}%")
        else:
            self.progress_bar.setFormat("下载完成!")
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
        self.append_log(message)
        if success:
            dialog = CustomDialog(f"{message}\n文件已保存至: {self.full_file_path}", title="成功",
                                  button_text="OK", parent=self)
            dialog.exec()
        else:
            dialog = CustomDialog(message, title="失败", button_text="知道了", parent=self)
            dialog.exec()
    
    def closeEvent(self, event):
        """处理窗口关闭事件，确保正确发出destroyed信号"""
        # 调用父类的closeEvent以确保正常关闭流程
        super().closeEvent(event)
        # 窗口关闭后会自动触发destroyed信号

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