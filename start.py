#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动 Web 服务器"""
import sys
import os

# 切换到项目目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 导入并运行服务器
from scripts.web_server import main

if __name__ == '__main__':
    main()
