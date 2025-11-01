#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说下载器 - 单一文件版本
功能：下载网络小说，支持自动章节识别、批量下载
作者：wwq
"""

import sys
import os
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, QGroupBox,
    QListWidget, QAbstractItemView, QComboBox, QFileDialog, QMessageBox,
    QSplitter, QSizePolicy, QDialog, QDialogButtonBox, QSpinBox
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSettings, QCoreApplication,
    QUrl, QObject
)
from PyQt6.QtGui import (
    QFont, QPalette, QColor, QIcon, QTextDocument
)

# 自定义对话框类
class CustomDialog(QDialog):
    """
    自定义对话框类，提供简洁的消息显示界面
    """
    def __init__(self, message, title="提示", button_text="确定", cancel_text=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # 设置布局
        layout = QVBoxLayout(self)
        
        # 消息标签
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        # 按钮箱
        button_box = QDialogButtonBox(self)
        
        # 添加确定按钮
        self.ok_button = button_box.addButton(button_text, QDialogButtonBox.ButtonRole.AcceptRole)
        
        # 添加取消按钮（如果提供）
        if cancel_text:
            self.cancel_button = button_box.addButton(cancel_text, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_box)
        
        # 连接信号
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # 设置窗口大小和样式
        self.setMinimumWidth(300)
        self.setStyleSheet("""
            QWidget {
                font-family: "Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei";
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
        """)

# 下载线程类
class DownloadThread(QThread):
    """
    下载线程类，负责实际的小说下载工作
    """
    progress_updated = pyqtSignal(int)
    message_received = pyqtSignal(str)
    download_completed = pyqtSignal(bool, str)
    download_timing = pyqtSignal(str, str)
    
    def __init__(self, url, tag, attr_dict, choose_dict, file_path, total_chapters=None, parent=None):
        super().__init__(parent)
        self.url = url
        self.tag = tag
        self.attr_dict = attr_dict
        self.choose_dict = choose_dict
        self.file_path = file_path
        self.total_chapters = total_chapters
        self.is_stopped = False
        self.start_time = 0
    
    def run(self):
        """
        线程运行函数，执行小说下载流程
        """
        try:
            self.start_time = time.time()
            self.message_received.emit(f"开始下载小说: {self.url}")
            
            # 创建会话以保持连接
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            current_url = self.url
            chapters_downloaded = 0
            all_content = []
            
            # 打开文件准备写入
            with open(self.file_path, 'w', encoding='utf-8') as f:
                # 下载循环
                while current_url and not self.is_stopped:
                    try:
                        # 发送请求获取页面
                        self.message_received.emit(f"正在下载章节: {current_url}")
                        response = session.get(current_url, timeout=30)
                        response.encoding = response.apparent_encoding
                        
                        # 解析页面
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 查找章节标题
                        chapter_title = self._extract_chapter_title(soup)
                        if chapter_title:
                            all_content.append(chapter_title)
                            f.write(chapter_title + '\n\n')
                            self.message_received.emit(f"已获取章节: {chapter_title}")
                        
                        # 查找内容
                        content_elements = soup.find_all(self.tag, self.attr_dict)
                        if content_elements:
                            for element in content_elements:
                                # 提取文本内容
                                content = element.get_text(separator='\n', strip=True)
                                if content:
                                    all_content.append(content)
                                    f.write(content + '\n\n')
                            
                            chapters_downloaded += 1
                            self.message_received.emit(f"已下载第 {chapters_downloaded} 章")
                        else:
                            self.message_received.emit(f"未找到内容元素: {self.tag} {self.attr_dict}")
                        
                        # 更新进度
                        self._update_progress(chapters_downloaded)
                        
                        # 查找下一章链接
                        current_url = self._find_next_chapter(soup, response.url)
                        if not current_url:
                            self.message_received.emit("未找到下一章链接，下载完成")
                            break
                        
                        # 短暂暂停，避免对服务器造成过大压力
                        time.sleep(1)
                        
                    except Exception as e:
                        self.message_received.emit(f"处理页面时出错: {str(e)}")
                        # 尝试继续下载下一章
                        current_url = self._find_next_chapter(None, current_url)  # 尝试从当前URL推断
                        if not current_url:
                            break
            
            if self.is_stopped:
                self.download_completed.emit(False, "下载已取消")
                # 如果文件已创建但未完成，删除文件
                if os.path.exists(self.file_path) and os.path.getsize(self.file_path) == 0:
                    os.remove(self.file_path)
            else:
                self.download_completed.emit(True, f"下载成功！共下载 {chapters_downloaded} 章")
                
        except Exception as e:
            self.message_received.emit(f"下载过程中出错: {str(e)}")
            self.download_completed.emit(False, f"下载失败: {str(e)}")
            # 清理未完成的文件
            if os.path.exists(self.file_path):
                try:
                    os.remove(self.file_path)
                except:
                    pass
    
    def stop(self):
        """
        停止下载
        """
        self.is_stopped = True
    
    def _extract_chapter_title(self, soup):
        """
        提取章节标题
        """
        # 尝试常见的标题标签和位置
        title_selectors = ['h1', 'h2', 'h3', '.title', '#title', '.chapter-title', '.bookname h1']
        
        for selector in title_selectors:
            try:
                # 先尝试CSS选择器
                try:
                    title_element = soup.select_one(selector)
                    if title_element:
                        title = title_element.get_text(strip=True)
                        if title:
                            return title
                except:
                    pass
                
                # 再尝试标签名
                if selector.startswith('.'):
                    # class选择器
                    class_name = selector[1:]
                    title_elements = soup.find_all(class_=class_name)
                    for elem in title_elements:
                        title = elem.get_text(strip=True)
                        if title and len(title) < 200:  # 避免获取过长的文本
                            return title
                elif selector.startswith('#'):
                    # id选择器
                    id_name = selector[1:]
                    title_element = soup.find(id=id_name)
                    if title_element:
                        title = title_element.get_text(strip=True)
                        if title:
                            return title
                else:
                    # 标签名
                    title_elements = soup.find_all(selector)
                    for elem in title_elements:
                        title = elem.get_text(strip=True)
                        if title and len(title) < 200:  # 避免获取过长的文本
                            return title
            except:
                continue
        
        # 如果找不到合适的标题，返回空
        return ""
    
    def _find_next_chapter(self, soup, current_url):
        """
        查找下一章链接
        """
        if not soup:
            return None
        
        # 尝试通过文本查找下一章链接
        next_links = []
        
        # 使用用户提供的下一章按钮文字
        for text in self.choose_dict:
            if text:
                # 查找包含特定文本的链接
                for link in soup.find_all('a', text=lambda t: t and text in t):
                    next_links.append(link)
                
                # 查找包含特定文本的按钮或其他元素中的链接
                for element in soup.find_all(text=lambda t: t and text in t):
                    link = element.find_parent('a')
                    if link:
                        next_links.append(link)
        
        # 如果没有找到，尝试常见的下一章链接标识
        if not next_links:
            common_next_texts = ['下一章', '下一页', '下节', 'next', 'Next']
            for text in common_next_texts:
                for link in soup.find_all('a', text=lambda t: t and text in t):
                    next_links.append(link)
        
        # 如果找到了链接，返回绝对URL
        if next_links:
            href = next_links[0].get('href')
            if href:
                return urljoin(current_url, href)
        
        # 如果找不到，尝试从URL模式推断
        try:
            parsed = urlparse(current_url)
            path = parsed.path
            
            # 尝试匹配数字章节URL
            numbers = re.findall(r'\d+', path)
            if numbers:
                # 获取最后一组数字
                last_number = numbers[-1]
                # 尝试递增数字来获取下一章URL
                next_number = str(int(last_number) + 1)
                next_path = path.replace(last_number, next_number)
                return urljoin(current_url, next_path)
        except:
            pass
        
        return None
    
    def _update_progress(self, chapters_downloaded):
        """
        更新下载进度和计时信息
        """
        # 计算进度
        if self.total_chapters and self.total_chapters > 0:
            progress = min(int((chapters_downloaded / self.total_chapters) * 100), 100)
        else:
            # 如果没有设置总章节数，使用估算进度
            progress = min(chapters_downloaded * 5, 95)  # 最多95%，留5%给最后处理
        
        # 计算时间
        elapsed_time = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed_time)
        
        # 估算剩余时间
        if chapters_downloaded > 0:
            avg_time_per_chapter = elapsed_time / chapters_downloaded
            if self.total_chapters and self.total_chapters > 0:
                remaining_chapters = self.total_chapters - chapters_downloaded
                estimated_time = avg_time_per_chapter * remaining_chapters
            else:
                # 假设总共30章
                remaining_chapters = max(0, 30 - chapters_downloaded)
                estimated_time = avg_time_per_chapter * remaining_chapters
            estimated_str = self._format_time(estimated_time)
        else:
            estimated_str = "--"
        
        # 发送信号
        self.progress_updated.emit(progress)
        self.download_timing.emit(elapsed_str, estimated_str)
    
    def _format_time(self, seconds):
        """
        格式化时间为可读字符串
        """
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes, seconds = divmod(seconds, 60)
            return f"{int(minutes)}分{int(seconds)}秒"
        else:
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}时{int(minutes)}分"

# 文件打开线程类
class FileOpenThread(QThread):
    """
    文件打开线程类，负责在后台打开和读取文件
    """
    message_received = pyqtSignal(str)
    file_opened = pyqtSignal(bool, str, str)
    
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
    
    def run(self):
        """
        线程运行函数，打开并读取文件
        """
        try:
            self.message_received.emit(f"正在打开文件: {self.file_path}")
            
            # 检查文件大小
            file_size = os.path.getsize(self.file_path)
            self.message_received.emit(f"文件大小: {self._format_size(file_size)}")
            
            # 读取文件内容
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.message_received.emit("文件打开成功")
            self.file_opened.emit(True, "文件打开成功", content)
            
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(self.file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                self.message_received.emit("文件使用GBK编码打开成功")
                self.file_opened.emit(True, "文件打开成功", content)
            except Exception as e:
                self.message_received.emit(f"文件编码错误: {str(e)}")
                self.file_opened.emit(False, f"无法打开文件: 文件编码不支持", "")
        except Exception as e:
            self.message_received.emit(f"打开文件时出错: {str(e)}")
            self.file_opened.emit(False, f"无法打开文件: {str(e)}", "")
    
    def _format_size(self, size_bytes):
        """
        格式化文件大小
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

# 下载管理器类
class DownloadManager(QObject):
    """
    下载管理器类，管理多个下载任务
    """
    all_downloads_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.download_threads = []
        self.active_downloads = 0
        self.batch_mode = False
    
    def add_download(self, url, tag, attr_dict, choose_dict, file_path, total_chapters=None):
        """
        添加下载任务
        """
        thread = DownloadThread(url, tag, attr_dict, choose_dict, file_path, total_chapters)
        thread.message_received.connect(self._on_thread_message)
        thread.download_completed.connect(self._on_thread_completed)
        self.download_threads.append(thread)
        return thread
    
    def start_all(self, batch_mode=False):
        """
        启动所有下载任务
        """
        self.batch_mode = batch_mode
        self.active_downloads = len(self.download_threads)
        for thread in self.download_threads:
            thread.start()
    
    def stop_all(self):
        """
        停止所有下载任务
        """
        for thread in self.download_threads:
            if thread.isRunning():
                thread.stop()
        
        # 等待所有线程结束
        for thread in self.download_threads:
            if thread.isRunning():
                thread.wait()
        
        self.active_downloads = 0
        if self.parent:
            self.parent.on_all_downloads_completed()
    
    def clear_tasks(self):
        """
        清空所有任务
        """
        # 先停止所有任务
        self.stop_all()
        # 清空列表
        self.download_threads.clear()
    
    def is_any_running(self):
        """
        检查是否有下载任务正在运行
        """
        return self.active_downloads > 0
    
    def _on_thread_message(self, message):
        """
        处理线程消息
        """
        if self.parent and hasattr(self.parent, 'append_log'):
            self.parent.append_log(message)
    
    def _on_thread_completed(self, success, message):
        """
        处理线程完成
        """
        self.active_downloads -= 1
        
        if self.parent and hasattr(self.parent, 'append_log'):
            self.parent.append_log(message)
        
        # 检查是否所有下载都已完成
        if self.active_downloads <= 0 and self.batch_mode:
            self.active_downloads = 0
            self.all_downloads_completed.emit()
            if self.parent and hasattr(self.parent, 'on_all_downloads_completed'):
                self.parent.on_all_downloads_completed()

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
        # 检查是否有下载正在进行
        if hasattr(self, 'download_manager') and self.download_manager.is_any_running():
            reply = QMessageBox.question(
                self, '确认关闭', 
                '当前有下载任务正在进行，确定要关闭窗口吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                # 停止所有下载
                self.download_manager.stop_all()
        
        # 保存设置
        if hasattr(self, 'save_settings'):
            self.save_settings()
        
        # 调用父类的closeEvent以确保正常关闭流程
        super().closeEvent(event)
        # 窗口关闭后会自动触发destroyed信号

# 应用程序主函数
def main():
    """
    应用程序主入口点
    """
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("小说下载器")
    app.setOrganizationName("wwq")
    app.setOrganizationDomain("wwq.example.com")
    
    # 创建小说下载窗口
    novel_window = NovelDownloadWindow()
    novel_window.show()
    
    # 运行应用程序主循环
    sys.exit(app.exec())

# 确保当直接运行此脚本时，执行main函数
if __name__ == "__main__":
    main()

