#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def merge_databases(main_db_path, update_db_path):
    """将更新数据库合并到主数据库"""
    
    if not os.path.exists(update_db_path):
        print(f"更新数据库不存在: {update_db_path}")
        return False
    
    if not os.path.exists(main_db_path):
        print(f"主数据库不存在: {main_db_path}")
        return False
    
    try:
        # 连接两个数据库
        main_conn = sqlite3.connect(main_db_path)
        update_conn = sqlite3.connect(update_db_path)
        
        # 获取更新数据
        cursor = update_conn.cursor()
        cursor.execute("SELECT date, COUNT(*) FROM daily_price GROUP BY date")
        update_stats = cursor.fetchall()
        
        print("更新数据库统计:")
        for date, count in update_stats:
            print(f"  {date}: {count} 条记录")
        
        # 合并数据
        main_cursor = main_conn.cursor()
        
        # 使用ATTACH方式合并
        main_cursor.execute(f"ATTACH DATABASE '{update_db_path}' AS update_db")
        
        # 插入或更新数据
        main_cursor.execute('''
        INSERT OR REPLACE INTO main.daily_price 
        SELECT * FROM update_db.daily_price
        ''')
        
        main_conn.commit()
        
        # 统计合并结果
        main_cursor.execute("SELECT date, COUNT(*) FROM daily_price WHERE date IN (SELECT DISTINCT date FROM update_db.daily_price) GROUP BY date")
        merged_stats = main_cursor.fetchall()
        
        print("\n合并后统计:")
        for date, count in merged_stats:
            print(f"  {date}: {count} 条记录")
        
        main_conn.close()
        update_conn.close()
        
        print(f"\n✅ 数据库合并完成!")
        return True
        
    except Exception as e:
        print(f"❌ 数据库合并失败: {e}")
        return False

def main():
    """主函数"""
    # 数据库路径配置
    main_db_path = r'C:\Users\LYY\Desktop\数据库\data\a_stock.db'  # 您的主数据库
    update_db_path = r"C:\Users\LYY\Downloads\daily_price_update (2).db"  # GitHub Action生成的更新数据库
    
    print("开始合并数据库...")
    print(f"主数据库: {main_db_path}")
    print(f"更新数据库: {update_db_path}")
    
    success = merge_databases(main_db_path, update_db_path)
    
    if success:
        print("\n🎉 所有操作完成!")
    else:
        print("\n💥 合并过程中出现错误!")

if __name__ == "__main__":
    main()