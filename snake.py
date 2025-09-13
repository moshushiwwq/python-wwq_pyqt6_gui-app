#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
贪吃蛇游戏
使用PyQt6开发的经典贪吃蛇游戏，具有以下功能：
1. 游戏主界面展示
2. 贪吃蛇移动控制
3. 食物生成与得分计算
4. 碰撞检测与游戏结束判定
5. 游戏状态控制（开始、暂停、重新开始）
"""
import sys
import random
import math
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QIcon
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint

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
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和尺寸
        self.setWindowTitle('贪吃蛇游戏')
        self.setGeometry(100, 100, self.width, self.height)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建垂直布局
        main_layout = QVBoxLayout(central_widget)
        
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
        self.score_label.setText(f'分数: {self.score}')
        
        # 生成食物
        self.generate_food()
        
        # 更新UI状态
        self.game_started = False
        self.game_paused = False
        self.start_button.setText('开始游戏')
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.restart_button.setEnabled(False)
        
        # 停止计时器
        self.timer.stop()
        
        # 重绘游戏画布
        self.game_canvas.update()
    
    def start_game(self):
        """开始或继续游戏"""
        if not self.game_started:
            self.game_started = True
            self.start_button.setText('继续')
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
    
    def generate_food(self):
        """在随机位置生成食物"""
        # 计算可用的网格数量
        max_x = (self.width - self.grid_size) // self.grid_size
        max_y = (self.height - 100) // self.grid_size  # 减去控制区域的高度
        
        # 生成不在蛇身上的随机位置
        while True:
            food_x = random.randint(1, max_x - 1) * self.grid_size
            food_y = random.randint(1, max_y - 1) * self.grid_size
            food_point = QPoint(food_x, food_y)
            
            # 检查食物是否生成在蛇身上
            if food_point not in self.snake:
                self.food = food_point
                break
    
    def keyPressEvent(self, event):
        """处理键盘事件，控制蛇的移动方向"""
        key = event.key()
        
        # 如果游戏未开始，可以按空格键开始
        if not self.game_started and key == Qt.Key.Key_Space:
            self.start_game()
            return
        
        # 只有在游戏开始且未暂停时才处理方向键
        if self.game_started and not self.game_paused:
            # 确保不能直接反向移动
            if (key == Qt.Key.Key_Up and self.direction != Qt.Key.Key_Down) or\
               (key == Qt.Key.Key_Down and self.direction != Qt.Key.Key_Up) or\
               (key == Qt.Key.Key_Left and self.direction != Qt.Key.Key_Right) or\
               (key == Qt.Key.Key_Right and self.direction != Qt.Key.Key_Left):
                self.next_direction = key
            
            # 按空格键暂停游戏
            elif key == Qt.Key.Key_Space:
                self.pause_game()
    
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
            if (new_head.x() < 0 or new_head.x() >= self.width or
                new_head.y() < 0 or new_head.y() >= self.height - 100):  # 减去控制区域的高度
                self.game_over()
                return
            
            # 检查是否撞到自己
            if new_head in self.snake:
                self.game_over()
                return
            
            # 将新的头部添加到蛇的身体
            self.snake.insert(0, new_head)
            
            # 检查是否吃到食物
            if new_head == self.food:
                # 增加分数
                self.score += 10
                self.score_label.setText(f'分数: {self.score}')
                
                # 生成新的食物
                self.generate_food()
                
                # 随着分数增加，提高游戏速度
                if self.score % 50 == 0 and self.game_speed > 50:
                    self.game_speed -= 10
                    self.timer.setInterval(self.game_speed)
            else:
                # 如果没有吃到食物，移除尾部
                self.snake.pop()
            
            # 重绘游戏画布
            self.game_canvas.update()
    
    def game_over(self):
        """游戏结束处理"""
        # 停止计时器
        self.timer.stop()
        
        # 显示游戏结束消息
        QMessageBox.information(self, '游戏结束', f'游戏结束！\n你的分数是: {self.score}')
        
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
        self.setStyleSheet("background-color: #f0f0f0;")
    
    def paintEvent(self, event):
        """绘制游戏元素"""
        painter = QPainter(self)
        
        # 绘制网格（可选）
        self.draw_grid(painter)
        
        # 绘制蛇
        self.draw_snake(painter)
        
        # 绘制食物
        self.draw_food(painter)
        
        # 如果游戏未开始，显示提示信息
        if not self.parent.game_started:
            self.draw_start_message(painter)
        elif self.parent.game_paused:
            self.draw_pause_message(painter)
    
    def draw_grid(self, painter):
        """绘制游戏网格"""
        pen = QPen(QColor(200, 200, 200), 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        # 绘制垂直线
        for x in range(0, self.width(), self.parent.grid_size):
            painter.drawLine(x, 0, x, self.height())
        
        # 绘制水平线
        for y in range(0, self.height(), self.parent.grid_size):
            painter.drawLine(0, y, self.width(), y)
    
    def draw_snake(self, painter):
        """绘制蛇的身体"""
        # 绘制蛇身
        for i, point in enumerate(self.parent.snake):
            rect = QRect(point.x(), point.y(), self.parent.grid_size, self.parent.grid_size)
            
            # 蛇头使用不同的颜色
            if i == 0:
                painter.fillRect(rect, QColor(0, 150, 0))  # 绿色头
            else:
                painter.fillRect(rect, QColor(0, 200, 0))  # 浅绿色身体
            
            # 添加边框
            painter.drawRect(rect)
    
    def draw_food(self, painter):
        """绘制食物"""
        # 绘制红色的食物
        painter.fillRect(
            QRect(self.parent.food.x(), self.parent.food.y(), 
                  self.parent.grid_size, self.parent.grid_size), 
            QColor(255, 0, 0)
        )
    
    def draw_start_message(self, painter):
        """绘制游戏开始提示信息"""
        # 设置字体
        font = painter.font()
        font.setPointSize(24)
        painter.setFont(font)
        
        # 设置文本颜色
        painter.setPen(QColor(0, 0, 255))
        
        # 绘制提示文本
        text = "按空格键开始游戏！"
        text_rect = painter.boundingRect(0, 0, self.width(), self.height(), 
                                         Qt.AlignmentFlag.AlignCenter, text)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)
    
    def draw_pause_message(self, painter):
        """绘制游戏暂停提示信息"""
        # 设置字体
        font = painter.font()
        font.setPointSize(24)
        painter.setFont(font)
        
        # 设置文本颜色
        painter.setPen(QColor(255, 165, 0))
        
        # 绘制暂停文本
        text = "游戏暂停！"
        text_rect = painter.boundingRect(0, 0, self.width(), self.height(), 
                                         Qt.AlignmentFlag.AlignCenter, text)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

if __name__ == '__main__':
    """主程序入口"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建游戏窗口
    game = SnakeGame()
    
    # 运行应用程序
    sys.exit(app.exec())