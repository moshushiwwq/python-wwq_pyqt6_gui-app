#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取用户桌面路径的工具脚本
"""
import os
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


if __name__ == '__main__':
    desktop_path = get_desktop_path()
    print(f"桌面路径: {desktop_path}")