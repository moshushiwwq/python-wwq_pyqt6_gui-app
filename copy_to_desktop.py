#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将打包后的可执行文件复制到用户桌面的脚本
"""
import os
import shutil
import sys


def get_desktop_path():
    """
    获取当前用户的桌面路径
    
    Returns:
        str: 用户桌面的绝对路径
    """
    if sys.platform == 'win32':
        # Windows系统
        return os.path.join(os.environ['USERPROFILE'], 'Desktop')
    elif sys.platform == 'darwin':
        # macOS系统
        return os.path.join(os.environ['HOME'], 'Desktop')
    else:
        # Linux或其他系统
        return os.path.join(os.environ['HOME'], 'Desktop')


def main():
    """
    主函数：复制应用程序启动器到桌面
    """
    try:
        # 获取桌面路径
        desktop_path = get_desktop_path()
        print(f"桌面路径: {desktop_path}")
        
        # 源文件路径
        source_file = os.path.join(os.getcwd(), 'dist', '应用程序启动器.exe')
        
        # 目标文件路径
        destination_file = os.path.join(desktop_path, '应用程序启动器.exe')
        
        # 检查源文件是否存在
        if not os.path.exists(source_file):
            print(f"错误: 源文件 '{source_file}' 不存在")
            sys.exit(1)
        
        # 复制文件
        print(f"正在复制文件到桌面: {destination_file}")
        shutil.copy2(source_file, destination_file)
        
        # 创建一个简单的批处理文件来启动应用程序（可选）
        batch_file = os.path.join(desktop_path, '启动应用程序.cmd')
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(f'@echo off\n"{destination_file}"\npause')
        
        print("复制完成！应用程序启动器已成功复制到桌面。")
        print("您可以双击桌面上的'应用程序启动器.exe'或'启动应用程序.cmd'来运行程序。")
        
    except Exception as e:
        print(f"复制文件时出错: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()