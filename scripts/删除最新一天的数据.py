
import sqlite3
import os
from datetime import datetime





def rollback_last_update(main_db_path, update_db_path):
    """删除主数据库中最近更新的一天的数据（即 update_db 中的最新日期）"""
    
    if not os.path.exists(main_db_path):
        print(f"主数据库不存在: {main_db_path}")
        return False

    if not os.path.exists(update_db_path):
        print(f"更新数据库不存在: {update_db_path}")
        return False

    try:
        update_conn = sqlite3.connect(update_db_path)
        main_conn = sqlite3.connect(main_db_path)

        # 获取更新数据库中最新的日期
        cursor = update_conn.cursor()
        cursor.execute("SELECT MAX(date) FROM daily_price")
        latest_date = cursor.fetchone()[0]

        if not latest_date:
            print("更新数据库中没有数据，无法回滚。")
            return False

        print(f"准备删除主数据库中日期为 {latest_date} 的数据...")

        # 删除主数据库中该日期的数据
        main_cursor = main_conn.cursor()
        main_cursor.execute("DELETE FROM daily_price WHERE date = ?", (latest_date,))
        main_conn.commit()

        # 检查删除结果
        main_cursor.execute("SELECT COUNT(*) FROM daily_price WHERE date = ?", (latest_date,))
        remaining = main_cursor.fetchone()[0]

        if remaining == 0:
            print(f"✅ 已成功删除主数据库中 {latest_date} 的所有数据。")
            result = True
        else:
            print(f"⚠️ 删除后仍有 {remaining} 条记录，可能删除失败。")
            result = False

        update_conn.close()
        main_conn.close()
        return result

    except Exception as e:
        print(f"❌ 回滚失败: {e}")
        return False
def main():
    main_db_path = r'数据库\data\a_stock.db'
    update_db_path = r"C:\Users\LYY\Downloads\daily_price_update (6).db"

    print("开始回滚最近更新的一天数据...")
    rollback_last_update(main_db_path, update_db_path)
main()
