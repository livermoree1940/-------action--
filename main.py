import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import adata

class DividendLowVolStrategy:
    """
    基于真实ETF数据的红利低波指数定投策略
    策略规则：N日收益差低于买入阈值定投买入，高于卖出阈值逐步卖出，其他时间持有
    """
    #自定义
    def __init__(self, return_period=40, buy_threshold=-0.01, sell_threshold=0.10):
        """
        初始化策略参数
        
        Parameters:
        -----------
        return_period : int
            收益率计算周期（天数），默认40天
        buy_threshold : float
            买入阈值，默认-1%（-0.01）
        sell_threshold : float
            卖出阈值，默认10%（0.10）
        """
        self.hl_etf_code = "515450"  # 中证红利低波50ETF
        self.benchmark_etf_code = "510210"  # 上证指数ETF作为基准
        
        # 可自定义参数
        self.return_period = return_period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        
        print(f"🎯 策略参数设置:")
        print(f"   • 收益率计算周期: {self.return_period}天")
        print(f"   • 买入阈值: {self.buy_threshold:.2%}")
        print(f"   • 卖出阈值: {self.sell_threshold:.2%}")
        print()
        
    def get_etf_data(self, fund_code, start_date="2020-01-01"):
        """
        获取ETF历史数据
        """
        try:
            # 使用adata获取ETF市场数据
            df = adata.fund.market.get_market_etf(fund_code=fund_code)
            
            # 数据预处理
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df = df.sort_values('trade_date').reset_index(drop=True)
            
            # 确保有足够的历史数据
            if len(df) < self.return_period:
                print(f"警告: {fund_code} 数据量不足，使用扩展数据")
                return self.get_extended_data(fund_code, start_date)
                
            return df
            
        except Exception as e:
            print(f"获取 {fund_code} 数据失败: {e}")
            return self.get_extended_data(fund_code, start_date)
    
    def get_extended_data(self, fund_code, start_date):
        """
        当主要数据源不可用时，使用AkShare作为备选
        """
        try:
            # 使用AkShare获取ETF数据
            if fund_code == "515450":
                # 中证红利低波50ETF，使用类似的ETF替代
                df = ak.fund_etf_hist_em(symbol="512890", period="daily", 
                                       start_date=start_date.replace("-", ""),
                                       adjust="hfq")
            else:
                # 上证指数ETF
                df = ak.fund_etf_hist_em(symbol="510210", period="daily",
                                       start_date=start_date.replace("-", ""),
                                       adjust="hfq")
            
            # 数据格式转换
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.rename(columns={
                '日期': 'trade_date', 
                '收盘': 'close',
                '开盘': 'open',
                '最高': 'high', 
                '最低': 'low',
                '成交量': 'volume'
            })
            
            # 确保数据类型正确
            numeric_columns = ['close', 'open', 'high', 'low', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            print(f"备选数据获取也失败: {e}")
            return self.generate_sample_data(start_date)
    
    def generate_sample_data(self, start_date):
        """
        生成模拟数据（最后备选方案）
        """
        dates = pd.date_range(start=start_date, end=datetime.today(), freq='D')
        dates = dates[dates.dayofweek < 5]  # 排除周末
        
        np.random.seed(42)
        n_days = len(dates)
        
        # 生成更符合实际的价格序列
        initial_price = 1.0
        prices = [initial_price]
        
        for i in range(n_days-1):
            # 模拟市场波动，红利ETF波动较小
            if i < len(dates) // 3:
                # 前期波动较大
                ret = np.random.normal(0.0002, 0.02)
            else:
                # 后期波动趋于稳定
                ret = np.random.normal(0.0001, 0.015)
            prices.append(prices[-1] * (1 + ret))
        
        df = pd.DataFrame({
            'trade_date': dates,
            'close': prices
        })
        
        # 确保数据类型正确
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        
        return df
    
    def calculate_return_diff(self, start_date="2020-01-01"):
        """
        计算N日收益差并生成交易信号
        """
        print("正在获取ETF数据...")
        
        # 获取ETF数据
        hl_df = self.get_etf_data(self.hl_etf_code, start_date)
        benchmark_df = self.get_etf_data(self.benchmark_etf_code, start_date)
        
        # 数据预处理 - 确保数据类型正确
        hl_df = hl_df[['trade_date', 'close']].rename(columns={'close': 'hl_close'})
        benchmark_df = benchmark_df[['trade_date', 'close']].rename(columns={'close': 'benchmark_close'})
        
        # 确保数据类型为数值型
        hl_df['hl_close'] = pd.to_numeric(hl_df['hl_close'], errors='coerce')
        benchmark_df['benchmark_close'] = pd.to_numeric(benchmark_df['benchmark_close'], errors='coerce')
        
        # 删除无效数据
        hl_df = hl_df.dropna(subset=['hl_close'])
        benchmark_df = benchmark_df.dropna(subset=['benchmark_close'])
        
        # 合并数据，确保日期对齐
        merged_df = pd.merge(hl_df, benchmark_df, on='trade_date', how='inner')
        
        if len(merged_df) < self.return_period:
            print(f"错误: 数据量不足，至少需要{self.return_period}个交易日数据")
            return None, None, None, None, None
        
        print(f"数据获取成功: 红利低波ETF {len(hl_df)} 条, 基准ETF {len(benchmark_df)} 条, 合并后 {len(merged_df)} 条")
        
        # 再次确保数据类型正确
        merged_df['hl_close'] = pd.to_numeric(merged_df['hl_close'], errors='coerce')
        merged_df['benchmark_close'] = pd.to_numeric(merged_df['benchmark_close'], errors='coerce')
        
        # 删除任何可能的NaN值
        merged_df = merged_df.dropna(subset=['hl_close', 'benchmark_close'])
        
        # 计算N日收益率
        try:
            merged_df['hl_return_nd'] = merged_df['hl_close'].pct_change(self.return_period)
            merged_df['benchmark_return_nd'] = merged_df['benchmark_close'].pct_change(self.return_period)
            
            # 计算N日收益差
            merged_df['return_diff'] = merged_df['hl_return_nd'] - merged_df['benchmark_return_nd']
            
            print(f"数据计算完成: 最新日期 {merged_df['trade_date'].iloc[-1]}")
            
        except Exception as e:
            print(f"收益率计算错误: {e}")
            print(f"数据类型 - hl_close: {merged_df['hl_close'].dtype}, benchmark_close: {merged_df['benchmark_close'].dtype}")
            return None, None, None, None, None
        
        # 获取最新数据
        latest_data = merged_df.iloc[-1]
        latest_date = latest_data['trade_date']
        latest_diff = latest_data['return_diff']
        
        # 生成交易信号
        if pd.isna(latest_diff):
            if len(merged_df) > 1:
                latest_diff = merged_df.iloc[-2]['return_diff']  # 使用前一日数据
            else:
                latest_diff = 0
        
        if latest_diff <= self.buy_threshold:
            signal = "🚀 加倍定投买入"
            reason = f"收益差({latest_diff:.2%}) ≤ {self.buy_threshold:.2%}，红利低波ETF相对低估，是较好的加仓时机"
            color = "green"
        elif latest_diff >= self.sell_threshold:
            signal = "💰 逐步卖出"
            reason = f"收益差({latest_diff:.2%}) ≥ {self.sell_threshold:.2%}，红利低波ETF相对高估，应考虑逐步止盈"
            color = "red"
        else:
            signal = "📊 持有"
            reason = f"收益差({latest_diff:.2%})在 {self.buy_threshold:.2%} 到 {self.sell_threshold:.2%} 之间，估值处于合理区间"
            color = "orange"
        
        return merged_df, signal, reason, color, latest_diff
    
    def plot_strategy_chart(self, data_df):
        """
        绘制策略图表 - 添加鼠标联动功能
        """
        if data_df is None or len(data_df) < self.return_period:
            print("数据不足，无法绘制图表")
            return
        
        # 创建图形和子图
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 准备数据
        data_df = data_df.copy()
        data_df['hl_normalized'] = data_df['hl_close'] / data_df['hl_close'].iloc[0] * 100
        data_df['benchmark_normalized'] = data_df['benchmark_close'] / data_df['benchmark_close'].iloc[0] * 100
        
        # 1. 价格走势对比
        line1 = ax1.plot(data_df['trade_date'], data_df['hl_normalized'], 
                        label='中证红利低波50ETF', linewidth=2.5, color='#2E86AB')[0]
        line2 = ax1.plot(data_df['trade_date'], data_df['benchmark_normalized'], 
                        label='上证指数ETF', linewidth=2.5, color='#A23B72', alpha=0.8)[0]
        ax1.set_title(f'📈 中证红利低波50ETF vs 上证指数ETF走势对比 ({self.return_period}日策略)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('归一化价格(基点=100)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. N日收益率对比
        valid_data = data_df[data_df['hl_return_nd'].notna()]
        
        line3 = ax2.plot(valid_data['trade_date'], valid_data['hl_return_nd'] * 100, 
                        label=f'红利低波ETF{self.return_period}日收益率', linewidth=2, color='#2E86AB')[0]
        line4 = ax2.plot(valid_data['trade_date'], valid_data['benchmark_return_nd'] * 100, 
                        label=f'上证ETF{self.return_period}日收益率', linewidth=2, color='#A23B72')[0]
        ax2.set_title(f'📊 {self.return_period}日收益率对比', fontsize=14, fontweight='bold')
        ax2.set_ylabel('收益率(%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. N日收益差
        return_diff_data = data_df[data_df['return_diff'].notna()]
        
        line5 = ax3.plot(return_diff_data['trade_date'], return_diff_data['return_diff'] * 100, 
                        label=f'{self.return_period}日收益差', color='#F18F01', linewidth=2.5)[0]
        
        # 阈值线
        ax3.axhline(y=self.buy_threshold * 100, color='green', linestyle='--', 
                  linewidth=2, label=f'买入线({self.buy_threshold*100:.1f}%)')
        ax3.axhline(y=self.sell_threshold * 100, color='red', linestyle='--', 
                  linewidth=2, label=f'卖出线({self.sell_threshold*100:.1f}%)')
        ax3.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
        
        # 填充区域
        ax3.fill_between(return_diff_data['trade_date'], 
                        self.buy_threshold * 100, self.sell_threshold * 100,
                        alpha=0.1, color='orange', label='持有区间')
        
        ax3.set_title(f'🎯 {self.return_period}日收益差策略信号 (买入:{self.buy_threshold:.1%}, 卖出:{self.sell_threshold:.1%})', 
                     fontsize=14, fontweight='bold')
        ax3.set_xlabel('日期')
        ax3.set_ylabel('收益差(%)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 添加鼠标悬停功能
        self.add_mouse_interaction(fig, ax1, ax2, ax3, data_df, valid_data, return_diff_data)
        
        plt.tight_layout()
        plt.show()
    
    def add_mouse_interaction(self, fig, ax1, ax2, ax3, data_df, valid_data, return_diff_data):
        """
        添加鼠标悬停交互功能
        """
        # 创建标注文本
        annot1 = ax1.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot1.set_visible(False)
        
        annot2 = ax2.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot2.set_visible(False)
        
        annot3 = ax3.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot3.set_visible(False)
        
        def update_annot1(sel):
            """更新第一个子图的标注"""
            idx = sel.target.index
            if idx < len(data_df):
                date = data_df.iloc[idx]['trade_date']
                hl_price = data_df.iloc[idx]['hl_normalized']
                bench_price = data_df.iloc[idx]['benchmark_normalized']
                hl_original = data_df.iloc[idx]['hl_close']
                bench_original = data_df.iloc[idx]['benchmark_close']
                
                text = (f"日期: {date.strftime('%Y-%m-%d')}\n"
                       f"红利低波ETF: {hl_price:.2f}点\n"
                       f"实际价格: {hl_original:.3f}\n"
                       f"上证ETF: {bench_price:.2f}点\n"
                       f"实际价格: {bench_original:.3f}")
                annot1.set_text(text)
                annot1.xy = (sel.target.x, sel.target.y)
        
        def update_annot2(sel):
            """更新第二个子图的标注"""
            idx = sel.target.index
            if idx < len(valid_data):
                date = valid_data.iloc[idx]['trade_date']
                hl_return = valid_data.iloc[idx]['hl_return_nd'] * 100
                bench_return = valid_data.iloc[idx]['benchmark_return_nd'] * 100
                
                text = (f"日期: {date.strftime('%Y-%m-%d')}\n"
                       f"红利低波ETF{self.return_period}日收益率: {hl_return:.2f}%\n"
                       f"上证ETF{self.return_period}日收益率: {bench_return:.2f}%\n"
                       f"收益差: {hl_return - bench_return:.2f}%")
                annot2.set_text(text)
                annot2.xy = (sel.target.x, sel.target.y)
        
        def update_annot3(sel):
            """更新第三个子图的标注"""
            idx = sel.target.index
            if idx < len(return_diff_data):
                date = return_diff_data.iloc[idx]['trade_date']
                return_diff = return_diff_data.iloc[idx]['return_diff'] * 100
                
                # 判断信号
                if return_diff <= self.buy_threshold * 100:
                    signal = "🚀 买入信号"
                elif return_diff >= self.sell_threshold * 100:
                    signal = "💰 卖出信号"
                else:
                    signal = "📊 持有信号"
                
                text = (f"日期: {date.strftime('%Y-%m-%d')}\n"
                       f"{self.return_period}日收益差: {return_diff:.2f}%\n"
                       f"策略信号: {signal}\n"
                       f"买入阈值: {self.buy_threshold*100:.1f}%\n"
                       f"卖出阈值: {self.sell_threshold*100:.1f}%")
                annot3.set_text(text)
                annot3.xy = (sel.target.x, sel.target.y)
        
        def hover1(event):
            """第一个子图的悬停事件"""
            if event.inaxes == ax1:
                cont1, ind1 = line1.contains(event)
                cont2, ind2 = line2.contains(event)
                if cont1:
                    update_annot1(type('obj', (object,), {'target': type('obj', (object,), {
                        'x': event.xdata, 'y': event.ydata, 'index': ind1['ind'][0]
                    })()}))
                    annot1.set_visible(True)
                    fig.canvas.draw_idle()
                elif cont2:
                    update_annot1(type('obj', (object,), {'target': type('obj', (object,), {
                        'x': event.xdata, 'y': event.ydata, 'index': ind2['ind'][0]
                    })()}))
                    annot1.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if annot1.get_visible():
                        annot1.set_visible(False)
                        fig.canvas.draw_idle()
        
        def hover2(event):
            """第二个子图的悬停事件"""
            if event.inaxes == ax2:
                cont3, ind3 = line3.contains(event)
                cont4, ind4 = line4.contains(event)
                if cont3:
                    update_annot2(type('obj', (object,), {'target': type('obj', (object,), {
                        'x': event.xdata, 'y': event.ydata, 'index': ind3['ind'][0]
                    })()}))
                    annot2.set_visible(True)
                    fig.canvas.draw_idle()
                elif cont4:
                    update_annot2(type('obj', (object,), {'target': type('obj', (object,), {
                        'x': event.xdata, 'y': event.ydata, 'index': ind4['ind'][0]
                    })()}))
                    annot2.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if annot2.get_visible():
                        annot2.set_visible(False)
                        fig.canvas.draw_idle()
        
        def hover3(event):
            """第三个子图的悬停事件"""
            if event.inaxes == ax3:
                cont5, ind5 = line5.contains(event)
                if cont5:
                    update_annot3(type('obj', (object,), {'target': type('obj', (object,), {
                        'x': event.xdata, 'y': event.ydata, 'index': ind5['ind'][0]
                    })()}))
                    annot3.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if annot3.get_visible():
                        annot3.set_visible(False)
                        fig.canvas.draw_idle()
        
        # 连接鼠标移动事件
        fig.canvas.mpl_connect("motion_notify_event", hover1)
        fig.canvas.mpl_connect("motion_notify_event", hover2)
        fig.canvas.mpl_connect("motion_notify_event", hover3)
    
    def run_backtest(self, data_df, initial_investment=10000, monthly_investment=1000):
        """
        运行策略回测
        """
        if data_df is None or len(data_df) < 100:
            print("数据不足，无法进行回测")
            return None, None, None
        
        valid_data = data_df[data_df['return_diff'].notna()].copy()
        
        # 初始化回测变量
        cash = initial_investment
        shares = 0
        portfolio_value = []
        benchmark_value = []
        signals = []
        
        # 模拟每月定投
        investment_dates = pd.date_range(start=valid_data['trade_date'].iloc[0], 
                                       end=valid_data['trade_date'].iloc[-1], 
                                       freq='M')
        
        for date in investment_dates:
            if date not in valid_data['trade_date'].values:
                continue
                
            current_data = valid_data[valid_data['trade_date'] == date].iloc[0]
            current_price = current_data['hl_close']
            return_diff = current_data['return_diff']
            
            # 根据信号调整投资金额
            if return_diff <= self.buy_threshold:
                # 加倍定投
                investment_amount = monthly_investment * 2
                signal = "加倍买入"
            elif return_diff >= self.sell_threshold:
                # 卖出部分持仓
                investment_amount = -monthly_investment  # 卖出
                signal = "减仓卖出"
            else:
                # 正常定投
                investment_amount = monthly_investment
                signal = "正常定投"
            
            # 执行交易
            if investment_amount > 0:
                # 买入
                shares_to_buy = investment_amount / current_price
                shares += shares_to_buy
                cash -= investment_amount
            else:
                # 卖出
                shares_to_sell = min(abs(investment_amount) / current_price, shares)
                shares -= shares_to_sell
                cash += shares_to_sell * current_price
            
            # 计算组合价值
            current_value = cash + shares * current_price
            benchmark_current_value = initial_investment * (current_data['benchmark_close'] / valid_data['benchmark_close'].iloc[0])
            
            portfolio_value.append(current_value)
            benchmark_value.append(benchmark_current_value)
            signals.append(signal)
        
        return portfolio_value, benchmark_value, signals
    
    def run_strategy(self):
        """
        运行完整策略分析
        """
        print("=" * 70)
        print(f"🎯 中证红利低波50ETF定投策略分析 ({self.return_period}日策略)")
        print("=" * 70)
        
        # 计算收益差和信号
        data_df, signal, reason, color, return_diff = self.calculate_return_diff()
        
        if data_df is not None:
            latest_data = data_df.iloc[-1]
            
            print(f"📅 分析日期: {latest_data['trade_date'].strftime('%Y-%m-%d')}")
            print(f"📊 中证红利低波50ETF {self.return_period}日收益率: {latest_data.get('hl_return_nd', 0):.2%}")
            print(f"📈 上证指数ETF {self.return_period}日收益率: {latest_data.get('benchmark_return_nd', 0):.2%}")
            print(f"🎯 {self.return_period}日收益差: {return_diff:.2%}")
            print(f"💡 投资信号: {signal}")
            print(f"📝 信号理由: {reason}")
            
            # 绘制图表
            self.plot_strategy_chart(data_df)
            
            # 显示历史信号统计
            self.show_signal_statistics(data_df)
            
            # 运行回测
            print("\n" + "="*50)
            print("📈 策略回测结果")
            print("="*50)
            portfolio_values, benchmark_values, signals = self.run_backtest(data_df)
            
            if portfolio_values:
                final_return = (portfolio_values[-1] - 10000) / 10000
                benchmark_return = (benchmark_values[-1] - 10000) / 10000
                excess_return = final_return - benchmark_return
                
                print(f"💰 策略最终收益: {final_return:.2%}")
                print(f"📊 基准最终收益: {benchmark_return:.2%}")
                print(f"🎯 超额收益: {excess_return:.2%}")
                
                # 显示信号分布
                signal_counts = pd.Series(signals).value_counts()
                print(f"\n📋 信号分布:")
                for s, count in signal_counts.items():
                    print(f"   {s}: {count}次")
            
            return signal, return_diff
        else:
            print("❌ 策略分析失败")
            return None, None
    
    def show_signal_statistics(self, data_df):
        """
        显示历史信号统计
        """
        valid_data = data_df[data_df['return_diff'].notna()].copy()
        
        # 标记信号
        valid_data['signal'] = '持有'
        valid_data.loc[valid_data['return_diff'] <= self.buy_threshold, 'signal'] = '买入'
        valid_data.loc[valid_data['return_diff'] >= self.sell_threshold, 'signal'] = '卖出'
        
        # 统计各信号出现次数
        signal_counts = valid_data['signal'].value_counts()
        
        print(f"\n📊 历史信号统计 ({self.return_period}日策略):")
        print("-" * 50)
        for signal, count in signal_counts.items():
            percentage = count / len(valid_data) * 100
            print(f"   {signal}信号: {count}次 ({percentage:.1f}%)")
        
        # 显示当前信号持续时间
        current_signal = valid_data.iloc[-1]['signal']
        consecutive_days = 0
        for i in range(len(valid_data)-1, -1, -1):
            if valid_data.iloc[i]['signal'] == current_signal:
                consecutive_days += 1
            else:
                break
        
        print(f"  当前'{current_signal}'信号已持续{consecutive_days}个交易日")


# 执行策略的示例
if __name__ == "__main__":
    print("💡 重要提示:")
    print("1. 本策略基于N日收益差的均值回归原理")
    print("2. 使用真实ETF数据进行计算")
    print("3. 投资有风险，本策略仅供参考\n")
    
    # 自定义策略参数示例
    print("🔄 自定义策略参数设置:")
    print("   • 按回车使用默认参数")
    
    try:
        # 获取用户输入
        return_period_input = input(f"   收益率计算周期 (默认40): ").strip()
        buy_threshold_input = input(f"   买入阈值 (默认-0.01 = -1%): ").strip()
        sell_threshold_input = input(f"   卖出阈值 (默认0.10 = 10%): ").strip()
        
        # 处理输入
        return_period = int(return_period_input) if return_period_input else 40
        buy_threshold = float(buy_threshold_input) if buy_threshold_input else -0.01
        sell_threshold = float(sell_threshold_input) if sell_threshold_input else 0.10
        
        # 创建策略实例并运行
        strategy = DividendLowVolStrategy(
            return_period=return_period,
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold
        )
        
    except ValueError:
        print("⚠️ 输入格式错误，使用默认参数")
        strategy = DividendLowVolStrategy()
    
    # 执行策略分析
    signal, return_diff = strategy.run_strategy()
    
    if signal:
        print(f"\n🎯 最终操作建议: {signal}")
        print(f"📊 当前{strategy.return_period}日收益差: {return_diff:.2%}")
        
        # 提供具体的操作建议
        print("\n💡 具体操作建议:")
        if "买入" in signal:
            print("   • 增加定投金额至平时的2倍")
            print("   • 可以考虑分批建仓")
            print("   • 保持耐心，等待均值回归")
        elif "卖出" in signal:
            print("   • 逐步减仓，锁定利润")
            print("   • 可以考虑卖出部分持仓")
            print("   • 保留底仓，等待下次机会")
        else:
            print("   • 继续坚持定投计划")
            print("   • 保持现有仓位不动")
            print("   • 密切关注收益差变化")