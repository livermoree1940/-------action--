#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd
import sqlite3
import os
from datetime import datetime
import sys
import requests
import time

def create_database_schema(conn):
    """创建与您数据库结构相同的表"""
    cursor = conn.cursor()
    
    # 创建与您数据库结构相同的daily_price表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_price (
        code TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        amount REAL,
        update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (code, date)
    )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_date ON daily_price(code, date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON daily_price(date)')
    
    conn.commit()
    print("数据库表结构创建完成")

def get_stock_data_akshare():
    """使用akshare获取股票数据 - 主接口"""
    print(f"开始使用akshare获取A股实时数据 - {datetime.now()}")
    
    try:
        # 使用akshare的实时数据接口
        stock_df = ak.stock_zh_a_spot()
        print(f"akshare成功获取 {len(stock_df)} 条股票数据")
        
        # 处理数据以匹配您的数据库结构
        processed_data = []
        
        for _, row in stock_df.iterrows():
            # 提取并格式化数据
            code = row['代码']
            # 确保代码格式正确（去掉市场前缀，只保留数字）
            if code.startswith(('sh', 'sz', 'bj')):
                code = code[2:]  # 去掉市场前缀
            
            # 获取当前日期
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # 构建数据记录
            record = {
                'code': code,
                'date': current_date,
                'open': float(row['今开']) if pd.notna(row['今开']) else None,
                'high': float(row['最高']) if pd.notna(row['最高']) else None,
                'low': float(row['最低']) if pd.notna(row['最低']) else None,
                'close': float(row['最新价']) if pd.notna(row['最新价']) else None,
                'amount': float(row['成交额']) if pd.notna(row['成交额']) else None
            }
            processed_data.append(record)
        
        return processed_data
        
    except Exception as e:
        print(f"akshare获取数据失败: {e}")
        return None

def get_stock_data_sina():
    """使用新浪接口获取股票数据 - 备用接口"""
    print(f"开始使用新浪接口获取A股实时数据 - {datetime.now()}")
    
    try:
        # 新浪财经A股列表接口
        url = "http://hq.sinajs.cn/list=sh000001,sz399001"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            print("新浪接口连接成功")
            # 这里只是示例，实际需要更复杂的解析逻辑
            # 由于新浪接口的限制，我们主要依赖akshare
            
            # 返回空数据，表示新浪接口可用但数据需要另外处理
            return []
        else:
            print(f"新浪接口请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"新浪接口获取数据失败: {e}")
        return None

def save_to_database(data, db_path):
    """保存数据到SQLite数据库"""
    if not data:
        print("没有有效数据可保存")
        return False
        
    try:
        conn = sqlite3.connect(db_path)
        
        # 创建表结构（如果不存在）
        create_database_schema(conn)
        
        # 插入数据
        cursor = conn.cursor()
        inserted_count = 0
        
        for record in data:
            try:
                cursor.execute('''
                INSERT OR REPLACE INTO daily_price 
                (code, date, open, high, low, close, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record['code'],
                    record['date'],
                    record['open'],
                    record['high'],
                    record['low'],
                    record['close'],
                    record['amount']
                ))
                inserted_count += 1
            except Exception as e:
                print(f"插入数据失败 {record['code']}: {e}")
                continue
        
        conn.commit()
        print(f"成功保存 {inserted_count} 条记录到数据库")
        
        # 显示统计信息
        cursor.execute("SELECT COUNT(*) FROM daily_price WHERE date = ?", 
                      (datetime.now().strftime('%Y-%m-%d'),))
        today_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(date), MAX(date) FROM daily_price")
        date_range = cursor.fetchone()
        
        print(f"\n数据库统计信息:")
        print(f"今日新增记录: {today_count}")
        print(f"数据日期范围: {date_range[0]} 至 {date_range[1]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"保存到数据库失败: {e}")
        return False

def main():
    """主函数"""
    # 创建数据目录
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    
    # 使用新的数据库文件名，避免与您的主数据库冲突
    db_path = os.path.join(data_dir, 'daily_price_update.db')
    
    # 首先尝试使用akshare获取数据
    data = get_stock_data_akshare()
    
    # 如果akshare失败，尝试新浪接口
    if data is None:
        print("akshare接口失败，尝试新浪接口...")
        data = get_stock_data_sina()
    
    if data is not None:
        # 保存到数据库
        success = save_to_database(data, db_path)
        
        if success:
            print("数据收集完成！")
            
            # 生成导入说明
            generate_import_instructions(db_path)
        else:
            print("数据保存失败！")
            sys.exit(1)
    else:
        print("所有数据接口都失败了！")
        sys.exit(1)

def generate_import_instructions(db_path):
    """生成数据库导入说明"""
    instructions = f"""
    📋 数据更新完成 - {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    📁 数据库文件: {db_path}
    
    🔄 导入到主数据库的SQL命令:
    
    -- 方法1: 使用ATTACH数据库
    ATTACH DATABASE '{db_path}' AS update_db;
    
    -- 插入或更新数据到主表
    INSERT OR REPLACE INTO main.daily_price 
    SELECT * FROM update_db.daily_price;
    
    -- 方法2: 直接导入（如果数据库在同一目录）
    INSERT OR REPLACE INTO daily_price 
    SELECT * FROM daily_price_update.daily_price;
    
    📊 数据特征:
    - 股票代码: 6位数字格式
    - 价格数据: 实际价格（未复权）
    - 成交额: 元为单位
    - 数据日期: {datetime.now().strftime('%Y-%m-%d')}
    """
    
    print(instructions)
    
    # 保存说明到文件
    instructions_file = os.path.join('data', 'import_instructions.txt')
    with open(instructions_file, 'w', encoding='utf-8') as f:
        f.write(instructions)
    print(f"📝 导入说明已保存至: {instructions_file}")

if __name__ == "__main__":
    main()