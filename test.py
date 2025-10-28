import adata
import adata
df = adata.fund.market.get_market_etf(fund_code='515450')#中证红利低波50etf
df = adata.fund.market.get_market_etf(fund_code='510210')#上证指数etf

print(df)