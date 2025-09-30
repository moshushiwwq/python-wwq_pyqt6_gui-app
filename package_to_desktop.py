#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包app_launcher.py并复制到桌面的脚本
"""
import os
import sys
import shutil
import subprocess


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


def package_app():
    """
    使用PyInstaller打包应用程序
    
    Returns:
        bool: 打包是否成功
    """
    try:
        print("开始打包应用程序...")
        
        # 使用PyInstaller打包，使用现有的spec文件
        subprocess.run(
            [sys.executable, '-m', 'PyInstaller', 'app_launcher.spec'],
            check=True,
            shell=True  # 在Windows上使用shell=True确保命令正确执行
        )
        
        print("应用程序打包成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"打包失败: {str(e)}")
        return False
    except Exception as e:
        print(f"打包过程中发生错误: {str(e)}")
        return False


def copy_to_desktop():
    """
    将打包后的可执行文件复制到桌面
    
    Returns:
        bool: 复制是否成功
    """
    try:
        # 获取桌面路径
        desktop_path = get_desktop_path()
        print(f"桌面路径: {desktop_path}")
        
        # 源文件路径
        source_file = os.path.join(os.getcwd(), 'dist', '应用程序启动器.exe')
        
        # 检查源文件是否存在
        if not os.path.exists(source_file):
            print(f"错误: 源文件 '{source_file}' 不存在")
            return False
        
        # 目标文件路径
        destination_file = os.path.join(desktop_path, '应用程序启动器.exe')
        
        # 复制文件
        print(f"正在复制文件到桌面: {destination_file}")
        shutil.copy2(source_file, destination_file)
        
        # 创建一个简单的批处理文件来启动应用程序
        batch_file = os.path.join(desktop_path, '启动应用程序.cmd')
        with open(batch_file, 'w', encoding='utf-8') as f:
            f.write(f'@echo off\n"{destination_file}"\npause')
        
        print("复制完成！应用程序启动器已成功复制到桌面。")
        print("您可以双击桌面上的'应用程序启动器.exe'或'启动应用程序.cmd'来运行程序。")
        
        return True
    except Exception as e:
        print(f"复制文件时出错: {str(e)}")
        return False


def main():
    """
    主函数：打包应用程序并复制到桌面
    """
    print("=== 应用程序打包与部署工具 ===")
    
    # 先打包应用程序
    if not package_app():
        print("打包失败，无法继续部署。")
        sys.exit(1)
    
    # 然后复制到桌面
    if not copy_to_desktop():
        print("复制到桌面失败，但应用程序已打包成功，可以在dist目录中找到可执行文件。")
        sys.exit(1)
    
    print("\n=== 任务完成！===\n")


if __name__ == '__main__':
    main()