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
6. 自动保存最高记录功能
7. 蛇头和蛇身图像显示
8. 额外食物和炸弹功能
9. 美观的游戏界面（圆润的蛇身、美化的食物外观、明显的边界等）
"""
import sys
import random
import math
import pickle
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox)
from PyQt6.QtGui import (QPainter, QColor, QPen, QFont, QIcon, QPixmap, QBrush,
                        QRadialGradient, QGuiApplication)
from PyQt6.QtCore import Qt, QTimer, QRect, QPoint, QRectF, QPointF

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
        """将窗口显示在屏幕中央"""
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, 
                  (screen.height() - size.height()) // 2)
    
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