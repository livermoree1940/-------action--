#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os

def install_requirements():
    """自动安装项目依赖"""
    print("正在安装项目依赖...")
    
    try:
        # 安装requirements.txt中的包
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖安装完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def check_environment():
    """检查环境配置"""
    print("检查Python环境...")
    
    try:
        import akshare
        import pandas
        import requests
        import sqlite3
        
        print("✅ 所有核心依赖已安装")
        print(f"   akshare版本: {akshare.__version__}")
        print(f"   pandas版本: {pandas.__version__}")
        print(f"   requests版本: {requests.__version__}")
        
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("A股数据收集项目环境设置")
    print("=" * 50)
    
    # 检查当前环境
    if not check_environment():
        print("\n开始安装依赖...")
        if install_requirements():
            print("\n重新检查环境...")
            if check_environment():
                print("\n🎉 环境设置完成！")
            else:
                print("\n💥 环境设置失败，请手动检查")
        else:
            print("\n💥 依赖安装失败")
    else:
        print("\n✅ 环境已就绪！")

if __name__ == "__main__":
    main()