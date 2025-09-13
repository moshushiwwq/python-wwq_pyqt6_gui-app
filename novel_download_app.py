#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说下载器应用
功能：允许用户输入小说章节URL、内容标签和属性，自动下载小说章节并保存到本地文件
"""
import sys
import time
import os
import random
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# PyQt6导入
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QTextEdit, QFileDialog, QDialog, QFormLayout,
    QSpinBox, QSizePolicy, QGroupBox
)
from PyQt6.QtGui import QPalette, QFont, QColor, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSettings
# 设置中文字体支持
font = QFont()
font.setFamily("SimHei")

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
        main_layout.setContentsMargins(15 , 15 , 15 , 15)
        main_layout.setSpacing(15)
        # 创建输入区域组
        input_group = QGroupBox("下载设置")
        input_layout = QVBoxLayout()
        input_group.setLayout(input_layout)
        # 使用表单布局组织输入控件
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(12)
        # URL 输入框 - 用于输入小说起始页URL
        self.url_input = QLineEdit()
        form_layout.addRow("小说起始 URL:" , self.url_input)
        # 标签输入框 - 用于指定小说章节内容的HTML标签
        self.tag_input = QLineEdit()
        form_layout.addRow("章节内容标签:" , self.tag_input)
        # 属性输入框 - 用于指定章节内容标签的属性
        self.attr_input = QLineEdit()
        form_layout.addRow("章节内容属性:" , self.attr_input)
        # 选择器输入框 - 用于指定章节下一章按钮标签
        self.choose_input = QLineEdit()
        form_layout.addRow("章节下一章按钮文字:" , self.choose_input)
        # 保存路径选择
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        form_layout.addRow("保存路径:" , path_layout)
        # 文件名设置
        self.filename_input = QLineEdit()
        self.filename_input.setText("小说.txt")
        form_layout.addRow("保存文件名:" , self.filename_input)
        # 总章节数设置 - 设置为0表示自动估算总章节数
        self.total_chapters_input = QSpinBox()
        self.total_chapters_input.setRange(0 , 9999)
        self.total_chapters_input.setSuffix(" 章")
        self.total_chapters_input.setToolTip("设置为0表示自动估算总章节数")
        form_layout.addRow("总章节数:" , self.total_chapters_input)
        input_layout.addLayout(form_layout)
        # 保存设置按钮
        save_settings_button = QPushButton("保存设置")
        save_settings_button.setIcon(QIcon.fromTheme("document-save"))
        save_settings_button.clicked.connect(self.save_settings)
        input_layout.addWidget(save_settings_button)
        main_layout.addWidget(input_group)
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        self.download_button = QPushButton("开始下载")
        self.download_button.setIcon(QIcon.fromTheme("download"))
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self.start_download)
        self.stop_button = QPushButton("停止下载")
        self.stop_button.setIcon(QIcon.fromTheme("process-stop"))
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_download)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.stop_button)
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
    更新进度条显示
    Args:
        value: 进度值(0-100)
    """
    def update_progress(self , value) :
        self.progress_bar.setValue(value)
        if value < 100 :
            self.progress_bar.setFormat(f"下载中: {value}%")
        else :
            self.progress_bar.setFormat("下载完成!")
    """
     添加日志信息到日志显示框，并自动滚动到底部
      Args:
         message: 要添加的日志消息
     """
    def append_log(self , message) :
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
    def download_finished(self , success , message) :
        self.download_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setValue(100 if success else 0)
        self.append_log(message)
        if success :
            dialog = CustomDialog(f"{message}\n文件已保存至: {self.full_file_path}" , title = "成功" ,
                                  button_text = "OK" , parent = self)
            dialog.exec()
        else :
            dialog = CustomDialog(message , title = "失败" , button_text = "知道了" , parent = self)
            dialog.exec()

# 自定义对话框类
class CustomDialog(QDialog):
    """
    自定义对话框类，用于显示各种消息提示
    """
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
        self.setStyleSheet(""".
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

# 主函数入口
if __name__ == "__main__":
    """
    应用程序入口函数，创建并显示主窗口
    """
    app = QApplication(sys.argv)
    # 设置全局字体，确保中文显示正常
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 创建并显示小说下载窗口
    novel_window = NovelDownloadWindow()
    novel_window.show()
    
    # 运行应用程序主循环
    sys.exit(app.exec())
