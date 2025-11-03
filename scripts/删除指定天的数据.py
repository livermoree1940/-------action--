import sqlite3
import os
from datetime import datetime


def rollback_by_date(main_db_path: str, target_date: str) -> bool:
    """
    删除主数据库 daily_price 表中指定日期的全部数据
    :param main_db_path: 主数据库路径
    :param target_date:  要删除的日期，格式 'YYYY-MM-DD'
    :return: True 删除成功，False 删除失败或文件不存在
    """
    if not os.path.exists(main_db_path):
        print(f"主数据库不存在: {main_db_path}")
        return False

    try:
        main_conn = sqlite3.connect(main_db_path)
        main_cursor = main_conn.cursor()

        # 先看看这一天有没有数据
        main_cursor.execute("SELECT COUNT(*) FROM daily_price WHERE date = ?", (target_date,))
        if main_cursor.fetchone()[0] == 0:
            print(f"主数据库中未找到日期为 {target_date} 的数据，无需删除。")
            return True

        print(f"准备删除主数据库中日期为 {target_date} 的数据...")
        main_cursor.execute("DELETE FROM daily_price WHERE date = ?", (target_date,))
        main_conn.commit()

        # 二次确认
        main_cursor.execute("SELECT COUNT(*) FROM daily_price WHERE date = ?", (target_date,))
        remaining = main_cursor.fetchone()[0]

        if remaining == 0:
            print(f"✅ 已成功删除主数据库中 {target_date} 的所有数据。")
            result = True
        else:
            print(f"⚠️ 删除后仍有 {remaining} 条记录，可能删除失败。")
            result = False

        main_conn.close()
        return result

    except Exception as e:
        print(f"❌ 删除失败: {e}")
        return False


def main():
    main_db_path = r'数据库\data\a_stock.db'

    # 让用户输入要回滚的日期
    target = input("请输入要删除的日期 (格式 2025-11-03): ").strip()
    try:
        # 简单校验一下格式
        datetime.strptime(target, '%Y-%m-%d')
    except ValueError:
        print("日期格式错误，应为 YYYY-MM-DD")
        return

    rollback_by_date(main_db_path, target)


if __name__ == '__main__':
    main()