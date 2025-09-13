#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2048游戏
使用PyQt6开发的经典2048数字拼图游戏，具有以下特点：
1. 随机生成新数字
2. 键盘控制方块移动
3. 方块合并与分数计算
4. 游戏状态检测（胜利、失败）
5. 美观的UI设计和动画效果
6. 游戏历史记录和最高分
"""
import sys
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
                             QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
                             QMessageBox, QFrame)
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QCoreApplication

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

if __name__ == '__main__':
    """主程序入口"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建游戏窗口
    game = Game2048()
    
    # 运行应用程序
    sys.exit(app.exec())