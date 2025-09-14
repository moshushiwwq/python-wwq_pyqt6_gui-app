import os

# 获取桌面路径
desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
print(f"桌面路径: {desktop}")