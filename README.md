# A股日线数据自动更新

这个项目使用GitHub Actions每天自动收集A股日线数据，生成与您主数据库结构兼容的更新文件。

## 主要特性

- 🕒 每天下午3:05（北京时间）自动运行
- 📊 收集所有A股股票的日线数据
- 💾 生成与您主数据库结构完全兼容的SQLite文件
- 🔄 支持多种数据接口（akshare主接口 + 新浪备用接口）
- 📈 数据格式与您的 `data/a_stock.db` 完全一致

## 数据库结构

生成的数据库包含与您主数据库相同的表结构：

### daily_price 表
- `code` TEXT - 股票代码（6位数字）
- `date` TEXT - 交易日期（YYYY-MM-DD）
- `open` REAL - 开盘价
- `high` REAL - 最高价  
- `low` REAL - 最低价
- `close` REAL - 收盘价
- `amount` REAL - 成交额
- `update_time` TIMESTAMP - 更新时间

## 使用方法

### 自动运行
- 每天下午3:05自动执行
- 数据保存到 `data/daily_price_update.db`

### 手动运行
1. 在GitHub仓库页面进入 "Actions"
2. 选择 "Daily A-Share Data Collection"
3. 点击 "Run workflow"

### 本地数据合并
```bash
# 合并到您的主数据库
python scripts/merge_databases.py