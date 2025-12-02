import os, requests
from tqdm import tqdm

url = ("https://raw.githubusercontent.com/livermoree1940/"
       "-------action--/main/data/daily_price_update.db")
file_name = "daily_price_update.db"
# 不走代理下的快一点
# # 1. 改成 Clash 实际监听的端口
# os.environ["HTTP_PROXY"]  = "http://127.0.0.1:7897"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7897"
# print("开始下载（走 Clash 代理）…")
resp = requests.get(url, stream=True, timeout=60)
resp.raise_for_status()

total = int(resp.headers.get("content-length", 0))
with open(file_name, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=file_name) as bar:
    for chunk in resp.iter_content(chunk_size=1024*64):
        if chunk:
            f.write(chunk)
            bar.update(len(chunk))

print(f"✅ 已保存到：{os.path.abspath(file_name)}")