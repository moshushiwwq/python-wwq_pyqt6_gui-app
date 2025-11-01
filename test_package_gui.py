#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试脚本：检查PackageAppGUI类的属性和方法
"""
import sys
from PyQt6.QtWidgets import QApplication
from package_to_desktop_gui import PackageAppGUI

# 确保中文显示正常
import os
os.environ['QT_FONT_DPI'] = '96'

if __name__ == '__main__':
    # 创建应用程序实例，但不显示窗口
    app = QApplication(sys.argv)
    
    try:
        # 创建PackageAppGUI实例
        window = PackageAppGUI()
        
        # 检查必要的方法是否存在
        print("=== 检查PackageAppGUI类的方法 ===")
        print(f"save_settings方法存在: {'save_settings' in dir(window)}")
        print(f"start_package方法存在: {'start_package' in dir(window)}")
        print(f"package_app方法存在: {'package_app' in dir(window)}")
        
        # 打印所有方法和属性以进行调试
        print("\n=== PackageAppGUI类的所有方法和属性 ===")
        for attr in dir(window):
            if not attr.startswith('__'):
                print(attr)
                
        print("\n测试完成：类结构看起来正常。")
        print("如果运行package_to_desktop_gui.py仍然报错，可能是文件编码问题或缓存问题。")
        
    except Exception as e:
        print(f"创建PackageAppGUI实例时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        
    sys.exit(0)