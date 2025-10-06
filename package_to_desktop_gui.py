#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包app_launcher.py并提供图形界面选择保存路径和打包方式的脚本
"""
import os
import sys
import shutil
import subprocess
import pickle
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QWidget, 
    QRadioButton, QGroupBox, QButtonGroup, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QMetaObject, Q_ARG
from PyQt6.QtGui import QPalette, QColor


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
                # 添加优化参数以减少exe启动时间
                cmd = [
                    sys.executable, '-m', 'PyInstaller', self.python_file,
                    '--name', self.app_name, '--windowed',
                    '--optimize=2',  # 启用最大优化级别
                    '--noupx',       # 不使用UPX压缩，加快启动速度
                    '--clean',       # 清理临时文件，确保每次打包都是全新的
                    '--workpath', os.path.join(package_infor_dir, "build"),  # 指定临时文件路径
                    '--distpath', os.path.join(package_infor_dir, "dist"),    # 指定输出目录路径
                    '--specpath', package_infor_dir                           # 指定spec文件路径
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
        self.package_button.clicked.connect(self.start_package)
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
        将打包后的文件复制到选择的保存路径
        
        Args:
            source_path: 源文件路径
            
        Returns:
            bool: 复制是否成功
        """
        try:
            app_name = self.name_input.text().strip()
            
            # 检查源文件是否存在
            if not os.path.exists(source_path):
                QMessageBox.critical(self, "错误", f"源文件 '{source_path}' 不存在")
                return False
            
            self.status_label.setText(f"正在复制文件到 {self.save_path}...")
            QApplication.processEvents()  # 更新UI
            
            # 根据文件类型执行不同的复制操作
            if os.path.isfile(source_path):
                # 复制单个文件
                destination_file = os.path.join(self.save_path, f'{app_name}.exe')
                shutil.copy2(source_path, destination_file)
                
                # 创建一个简单的批处理文件来启动应用程序
                batch_file = os.path.join(self.save_path, f'启动{app_name}.cmd')
                with open(batch_file, 'w', encoding='utf-8') as f:
                    f.write(f'@echo off\n"{destination_file}"\npause')
                
            else:
                # 复制整个文件夹
                destination_folder = os.path.join(self.save_path, app_name)
                # 如果目标文件夹已存在，则先删除
                if os.path.exists(destination_folder):
                    shutil.rmtree(destination_folder)
                shutil.copytree(source_path, destination_folder)
            
            self.status_label.setText(f"复制完成！{app_name}已成功复制到指定路径。")
            QMessageBox.information(
                self, "成功", 
                f"应用程序已成功打包并复制到\n{self.save_path}\n\n" +
                f"您可以前往该目录运行{app_name}。"
            )
            return True
        except Exception as e:
            self.status_label.setText(f"复制文件时出错")
            QMessageBox.critical(self, "错误", f"复制文件时出错: {str(e)}")
            return False
    
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
    
    def start_package(self):
        """
        开始打包流程
        """
        # 保存当前设置
        self.save_settings()
        
        # 启动打包流程（在线程中执行）
        self.package_app()
        # 注意：打包完成后，会在on_packaging_finished中自动处理复制到指定路径的操作


def main():
    """
    主函数：创建并运行图形界面应用
    """
    app = QApplication(sys.argv)
    window = PackageAppGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()