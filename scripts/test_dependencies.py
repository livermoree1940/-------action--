#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def test_dependencies():
    """测试所有必要的依赖包"""
    dependencies = [
        ('akshare', 'akshare'),
        ('pandas', 'pandas'),
        ('requests', 'requests'),
        ('sqlite3', 'sqlite3')  # 标准库，应该总是可用
    ]
    
    print("🔍 测试项目依赖...")
    print("=" * 50)
    
    all_ok = True
    for name, import_name in dependencies:
        try:
            __import__(import_name)
            version = "内置" if import_name == 'sqlite3' else get_version(import_name)
            print(f"✅ {name}: {version}")
        except ImportError as e:
            print(f"❌ {name}: 未安装 - {e}")
            all_ok = False
    
    print("=" * 50)
    if all_ok:
        print("🎉 所有依赖检查通过！")
    else:
        print("💥 有依赖未安装，请运行: pip install akshare pandas requests")
    
    return all_ok

def get_version(module_name):
    """获取模块版本"""
    try:
        module = __import__(module_name)
        return getattr(module, '__version__', '未知版本')
    except:
        return '未知版本'

if __name__ == "__main__":
    test_dependencies()