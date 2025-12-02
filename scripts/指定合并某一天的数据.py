import sqlite3
import os
from datetime import datetime

def merge_databases(main_db_path, update_db_path, start_date=None, end_date=None):
    """将更新数据库中指定日期范围的数据合并到主数据库"""
    
    # 验证日期格式和范围
    date_format = "%Y%m%d"
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, date_format)
            end_dt = datetime.strptime(end_date, date_format)
            if start_dt > end_dt:
                print("❌ 错误：开始日期不能晚于结束日期")
                return False
        except ValueError:
            print("❌ 错误：日期格式应为YYYYMMDD")
            return False
    
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
        
        # 获取更新数据统计
        cursor = update_conn.cursor()
        
        # 根据日期范围构建查询条件
        date_condition = ""
        if start_date and end_date:
            date_condition = f"WHERE date BETWEEN '{start_date}' AND '{end_date}'"
            print(f"📅 更新日期范围: {start_date} 至 {end_date}")
        
        cursor.execute(f"SELECT date, COUNT(*) FROM daily_price {date_condition} GROUP BY date")
        update_stats = cursor.fetchall()
        
        if not update_stats:
            print("⚠️ 更新数据库中没有找到匹配的数据")
            return False
        
        print("更新数据库统计:")
        for date, count in update_stats:
            print(f"  {date}: {count} 条记录")
        
        # 合并数据
        main_cursor = main_conn.cursor()
        
        # 使用ATTACH方式合并
        main_cursor.execute(f"ATTACH DATABASE '{update_db_path}' AS update_db")
        
        # 先删除主数据库中指定日期的旧数据
        if start_date and end_date:
            delete_query = f"DELETE FROM main.daily_price WHERE date BETWEEN '{start_date}' AND '{end_date}'"
            main_cursor.execute(delete_query)
            print(f"已删除主数据库中{start_date}至{end_date}的旧数据")
        
        # 插入或更新数据
        insert_query = f'''
        INSERT OR REPLACE INTO main.daily_price 
        SELECT * FROM update_db.daily_price
        {date_condition}
        '''
        main_cursor.execute(insert_query)
        
        main_conn.commit()
        
        # 统计合并结果
        stats_condition = "WHERE date IN (SELECT DISTINCT date FROM update_db.daily_price)"
        if start_date and end_date:
            stats_condition = f"WHERE date BETWEEN '{start_date}' AND '{end_date}'"
        
        main_cursor.execute(f"SELECT date, COUNT(*) FROM daily_price {stats_condition} GROUP BY date")
        merged_stats = main_cursor.fetchall()
        
        print("\n合并后统计:")
        for date, count in merged_stats:
            print(f"  {date}: {count} 条记录")
        
        main_conn.close()
        update_conn.close()
        
        print(f"\n✅ 数据库合并完成! 更新了{len(merged_stats)}天的数据")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 数据库合并失败: {e}")
        return False

def main():
    """主函数"""
    # 数据库路径配置
    main_db_path = r'数据库\data\a_stock.db'  # 您的主数据库
    update_db_path = r"C:\Users\LYY\Downloads\daily_price_update (8).db"  # 更新数据库
    
    # 用户指定的日期范围 (格式: YYYYMMDD)
    start_date = "20251102"  # 示例开始日期
    end_date = "20251105"    # 示例结束日期
    
    print("开始合并数据库...")
    print(f"主数据库: {main_db_path}")
    print(f"更新数据库: {update_db_path}")
    
    success = merge_databases(main_db_path, update_db_path, start_date, end_date)
    
    if success:
        print("\n🎉 所有操作完成!")
    else:
        print("\n💥 合并过程中出现错误!")

if __name__ == "__main__":
    main()
