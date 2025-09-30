"""
start_move.py

这是一个PyQt6应用程序的启动动画模块，展示一个动态绘制的百宝箱启动画面。
该模块创建一个带有动画效果的启动屏幕，可以在主应用程序加载时显示。

作者: moshushiwwq
日期: 2023
"""
import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF

class TreasureBoxSplash(QSplashScreen):
    """
    百宝箱启动画面类
    
    该类创建一个自定义的启动画面，展示一个动画绘制的百宝箱，并在动画结束后显示作者信息。
    继承自QSplashScreen，使用PyQt6的绘图API实现动画效果。
    """
    def __init__(self):
        """
        初始化百宝箱启动画面
        设置窗口属性、动画参数和定时器
        """
        super().__init__()
        # 设置窗口属性
        self.setFixedSize(400, 400)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 动画相关参数
        self.animation_step = 0
        self.max_steps = 20  # 总绘制步骤，增加动画细腻度
        self.author_displayed = False
        self.opacity = 1.0  # 透明度参数
        self.rotation_angle = 0  # 旋转角度，用于装饰元素
        
        # 设置定时器控制动画
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(80)  # 每80毫秒更新一次，加快动画节奏
        
        # 颜色常量定义
        self.MAIN_COLOR = QColor(50, 150, 255)
        self.ACCENT_COLOR = QColor(255, 165, 0)
        self.FILL_COLOR = QColor(240, 240, 255, 100)  # 半透明填充色
    
    def update_animation(self):
        """
        更新动画状态
        控制动画步骤、透明度和旋转角度
        """
        if self.animation_step < self.max_steps:
            self.animation_step += 1
            # 添加旋转效果
            self.rotation_angle = (self.rotation_angle + 3) % 360
            self.update()
        elif not self.author_displayed:
            # 绘制完成后等待一会儿显示作者信息
            QTimer.singleShot(300, self.show_author)
            self.author_displayed = True
        else:
            # 全部完成后添加淡出效果
            if self.opacity > 0:
                self.opacity -= 0.05
                self.setWindowOpacity(self.opacity)
                self.update()
            else:
                self.close()
    
    def show_author(self):
        """
        显示作者信息前的更新
        """
        self.update()
    
    def paintEvent(self, event):
        """
        绘制事件处理函数
        使用QPainter绘制百宝箱和动画效果
        
        参数:
            event: QPaintEvent对象，包含绘制事件信息
        """
        painter = QPainter(self)
        # 设置渲染提示，提高绘图质量
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 设置画笔
        pen = QPen(self.MAIN_COLOR, 4, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        # 增大百宝箱尺寸使其更饱满，并确保居中
        box_size = 280
        x = (self.width() - box_size) // 2
        y = (self.height() - box_size) // 2 + 20  # 适当下移使整体更居中
        
        # 绘制背景渐变效果
        if self.animation_step >= 1:
            gradient_rect = QRectF(0, 0, self.width(), self.height())
            # 创建圆形渐变
            painter.setBrush(self.FILL_COLOR)
            painter.drawEllipse(gradient_rect)
        
        # 逐步绘制百宝箱
        # 步骤1-2: 绘制底部矩形
        if self.animation_step >= 2:
            painter.drawLine(x, y + box_size, x + box_size, y + box_size)  # 底边
        if self.animation_step >= 3:
            painter.drawLine(x, y, x, y + box_size)  # 左边
            painter.drawLine(x + box_size, y, x + box_size, y + box_size)  # 右边
        
        # 步骤3-5: 绘制顶部
        if self.animation_step >= 4:
            painter.drawLine(x, y, x + box_size//4, y - box_size//5)  # 调整顶部倾斜度
        if self.animation_step >= 5:
            painter.drawLine(x + box_size, y, x + 3*box_size//4, y - box_size//5)  # 调整顶部倾斜度
        if self.animation_step >= 6:
            painter.drawLine(x + box_size//4, y - box_size//5, x + 3*box_size//4, y - box_size//5)  # 顶边
        
        # 步骤6-8: 绘制装饰线条
        if self.animation_step >= 7:
            painter.drawLine(x + box_size//4, y, x + box_size//4, y + box_size)  # 左分隔线
        if self.animation_step >= 8:
            painter.drawLine(x + 3*box_size//4, y, x + 3*box_size//4, y + box_size)  # 右分隔线
        if self.animation_step >= 9:
            painter.drawLine(x, y + box_size//2, x + box_size, y + box_size//2)  # 中间水平线
        
        # 步骤9-12: 绘制宝箱细节
        if self.animation_step >= 10:
            # 锁的位置
            lock_x = x + box_size//2
            lock_y = y + box_size//2
            painter.setBrush(self.ACCENT_COLOR)
            painter.drawEllipse(QRectF(lock_x - 12, lock_y - 12, 24, 24))  # 增大锁的尺寸
            painter.setBrush(Qt.BrushStyle.NoBrush)  # 恢复无填充
        if self.animation_step >= 11:
            painter.drawLine(lock_x, lock_y + 12, lock_x, lock_y + 40)  # 延长锁的垂直线
        if self.animation_step >= 12:
            painter.drawLine(x + 20, y + 20, x + 40, y + 20)  # 调整左上角装饰位置
        if self.animation_step >= 13:
            painter.drawLine(x + box_size - 40, y + 20, x + box_size - 20, y + 20)  # 调整右上角装饰位置
        
        # 步骤13-15: 绘制底部装饰
        if self.animation_step >= 14:
            painter.drawLine(x + 40, y + box_size, x + 60, y + box_size + 15)  # 调整底部装饰
        if self.animation_step >= 15:
            painter.drawLine(x + box_size - 60, y + box_size + 15, x + box_size - 40, y + box_size)  # 调整底部装饰
        if self.animation_step >= 16:
            painter.drawLine(x + box_size//2 - 15, y + box_size, x + box_size//2 + 15, y + box_size + 20)  # 调整底部中间装饰
        
        # 添加额外装饰元素 - 闪烁的星星
        if self.animation_step >= 17:
            self.draw_stars(painter, x, y, box_size)
        
        # 添加额外装饰元素 - 旋转的钥匙
        if self.animation_step >= 18:
            self.draw_rotating_key(painter, x, y, box_size)
        
        # 显示作者信息
        if self.author_displayed:
            # 设置支持中文的字体
            font = QFont("SimHei", 14, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(50, 50, 50))  # 使用深色文字提高可读性
            painter.drawText(0, self.height() - 40, self.width(), 40, 
                            Qt.AlignmentFlag.AlignCenter, "作者: moshushiwwq")
            
            # 添加版本信息
            small_font = QFont("SimHei", 10)
            painter.setFont(small_font)
            painter.drawText(0, self.height() - 20, self.width(), 20, 
                            Qt.AlignmentFlag.AlignCenter, "迷你应用集合 v1.0")
    
    def draw_stars(self, painter, x, y, box_size):
        """
        绘制闪烁的星星装饰
        
        参数:
            painter: QPainter对象
            x: 百宝箱x坐标
            y: 百宝箱y坐标
            box_size: 百宝箱尺寸
        """
        # 星星位置列表
        star_positions = [
            (x - 30, y - 20),
            (x + box_size + 20, y + 30),
            (x + box_size//2 - 50, y - 40),
            (x - 10, y + box_size + 10),
            (x + box_size + 10, y + box_size - 20)
        ]
        
        # 根据动画步骤设置星星可见性
        visible_stars = min(self.animation_step - 16, len(star_positions))
        
        for i in range(visible_stars):
            pos_x, pos_y = star_positions[i]
            # 星星大小随动画变化
            size = 3 + (self.animation_step % 3)
            
            # 绘制五角星
            painter.save()
            painter.translate(pos_x, pos_y)
            painter.rotate(self.rotation_angle * 2)
            
            # 创建星形路径
            path = QPainterPath()
            points = []
            for j in range(10):
                angle = 0.5 * j * 3.14159 / 5
                radius = size if j % 2 == 0 else size * 0.5
                points.append(QPointF(radius * 3.14159 / 2 * angle, 
                                     -radius * 3.14159 / 2 * angle))
            
            path.moveTo(points[0])
            for j in range(1, 10):
                path.lineTo(points[j])
            path.closeSubpath()
            
            painter.setBrush(self.ACCENT_COLOR)
            painter.drawPath(path)
            painter.restore()
    
    def draw_rotating_key(self, painter, x, y, box_size):
        """
        绘制旋转的钥匙装饰
        
        参数:
            painter: QPainter对象
            x: 百宝箱x坐标
            y: 百宝箱y坐标
            box_size: 百宝箱尺寸
        """
        # 钥匙位置
        key_x = x + box_size + 40
        key_y = y + box_size//2
        
        painter.save()
        painter.translate(key_x, key_y)
        painter.rotate(self.rotation_angle)
        
        # 绘制钥匙
        painter.setPen(QPen(self.MAIN_COLOR, 3))
        # 钥匙柄
        painter.drawRect(-10, -15, 20, 30)
        # 钥匙齿
        painter.drawLine(10, -15, 30, -15)
        painter.drawLine(10, 15, 25, 15)
        painter.drawLine(10, 0, 20, 0)
        
        painter.restore()

if __name__ == "__main__":
    """
    主程序入口
    创建应用程序实例和启动画面，并运行主循环
    """
    app = QApplication(sys.argv)
    
    # 确保中文显示正常
    font = QFont("SimHei")
    app.setFont(font)
    
    # 显示启动动画
    splash = TreasureBoxSplash()
    splash.show()
    
    # 这里可以添加主应用的初始化代码
    # ...
    
    sys.exit(app.exec())
