import datetime
import time
import os
import tarfile
import csv
import json
import re # 匯入 re 模組來解析檔名
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor, as_completed

# ====== 設定 ======
IPS = [
    "10.161.74.50", "10.161.74.51", "10.161.74.52", "10.161.74.53",
    "10.161.74.54", "10.161.74.55", "10.161.74.56", "10.161.74.57",
    "10.161.74.58", "10.161.74.59", "10.161.74.60", "10.161.74.61",
]
MAX_WORKERS = 2

USERNAME = "admin"
PASSWORD = "PiXoRd168"
DOWNLOAD_DIR = r"C:\Users\AIVT-LPR\Downloads\aidata_downloads"
CHROMEDRIVER_PATH = os.path.join(os.path.dirname(__file__), 'drivers', 'chromedriver.exe')

# ====== 日期定義 ======
run_date = datetime.date.today()
data_date = run_date - datetime.timedelta(days=1)
run_date_str = run_date.strftime("%Y%m%d")
data_date_str_for_filter = data_date.strftime("%Y-%m-%d")
data_date_str_for_filename = data_date.strftime("%Y-%m-%d")

# ====== 載入設備偵測設定 ======
try:
    with open(os.path.join(os.path.dirname(__file__), "device_config.json"), encoding="utf-8") as f:
        DEVICE_CONFIG = json.load(f)
except FileNotFoundError:
    print("❌ 錯誤：找不到 device_config.json 設定檔！")
    DEVICE_CONFIG = {}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def setup_driver():
    """設定並回傳一個 Chrome driver instance"""
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {"download.default_directory": DOWNLOAD_DIR})
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--log-level=3")
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=chrome_options)

def process_logs(folder, ip, target_date_str, target_filename_date_str):
    """解析日誌檔案，處理所有找到的檢測結果。"""
    print(f"🔷 [{ip}] 開始解析 {target_date_str} 的資料…")
    # ... 此函式內容與前一版完全相同，此處省略以保持簡潔 ...
    # (請參考前一回答中的完整 process_logs 函式內容)
    for root, _, files in os.walk(folder):
        for fname in files:
            if not fname.lower().endswith(".txt"):
                continue
            
            inp = os.path.join(root, fname)
            try:
                with open(inp, 'r', encoding="utf-8") as fin:
                    first_line = fin.readline().strip()
                    if not first_line: continue
                    device_name = first_line.split("~")[0]
                
                out_csv = os.path.join(root, f"data_{device_name}_{target_filename_date_str}_clean.csv")
                out_txt = os.path.join(root, f"data_{device_name}_{target_filename_date_str}_original.txt")

                processed_lines = 0
                with open(inp, 'r', encoding="utf-8") as fin, \
                     open(out_csv, "w", newline="", encoding="utf-8-sig") as fout:
                    writer = csv.writer(fout)
                    writer.writerow(["device", "timestamp", "SpecDirName", "status", "detection_type"])
                    
                    fin.seek(0)
                    for line in fin:
                        parts = line.strip().split("~")
                        if len(parts) < 3: continue
                        
                        device, ts = parts[0], parts[1]
                        if not ts.startswith(target_date_str):
                            continue
                        
                        processed_lines += 1
                        try:
                            data = json.loads(parts[-2])
                        except json.JSONDecodeError: data = {}

                        keys_to_use = list(data.keys())
                        for key in keys_to_use:
                            spec_dir_name = data.get(key, {}).get("SpecDirName", "")
                            status = data.get(key, {}).get("status", "")
                            
                            config_value = DEVICE_CONFIG.get(device, "未知")
                            if isinstance(config_value, str): detection_type = config_value
                            elif isinstance(config_value, dict): detection_type = config_value.get(spec_dir_name, "未知")
                            else: detection_type = "未知"
                                
                            writer.writerow([device, ts, spec_dir_name, status, detection_type])
                
                if processed_lines > 0:
                    if os.path.exists(out_txt): os.remove(out_txt)
                    os.rename(inp, out_txt)
                    print(f"✅ [{ip}] 已輸出 ({processed_lines} 筆資料):\n    - CSV: {out_csv}\n    - TXT: {out_txt}")
                else:
                    os.remove(out_csv)
                    print(f"ℹ️ [{ip}] 在 {fname} 中未找到 {target_date_str} 的資料，已跳過。")

            except Exception as e:
                print(f"❌ [{ip}] 解析檔案 {fname} 時發生錯誤: {e}")

# ====== 函式重構：拆分為下載和處理 ======

def download_archive(ip):
    """階段一：只負責從單一IP下載檔案，成功後回傳檔案路徑。"""
    max_attempts = 2
    retry_delay = 60

    for attempt in range(max_attempts):
        driver = None
        try:
            print(f"📥 [{ip}] 開始下載 (第 {attempt + 1} 次嘗試)...")
            driver = setup_driver()
            
            url = f"https://{USERNAME}:{PASSWORD}@{ip}/pixord/model/aidataexport_3dago.php"
            src = os.path.join(DOWNLOAD_DIR, "aidata.tar.gz")
            if os.path.exists(src): os.remove(src)
                
            driver.get(url)
            
            download_wait_timeout = 30
            wait_start_time = time.time()
            download_complete = False
            while time.time() - wait_start_time < download_wait_timeout:
                if os.path.exists(src):
                    time.sleep(1)
                    download_complete = True
                    break
                time.sleep(0.5)
            
            if not download_complete:
                raise Exception(f"等待下載逾時 ({download_wait_timeout}秒)")

            dst = os.path.join(DOWNLOAD_DIR, f"aidata_{ip.replace('.', '_')}_{run_date_str}.tar.gz")
            if os.path.exists(dst): os.remove(dst)
            os.rename(src, dst)
            print(f"✅ [{ip}] 下載完成：{dst}")
            
            return dst # 成功時回傳檔案路徑

        except Exception as e:
            print(f"⚠️ [{ip}] 第 {attempt + 1} 次嘗試下載失敗: {e}")
            if attempt < max_attempts - 1:
                print(f"⏰ [{ip}] 等待 {retry_delay} 秒後重試…")
                time.sleep(retry_delay)
            else:
                print(f"❌ [{ip}] 下載重試失敗，跳過此 IP。")
                return None # 最終失敗時回傳 None
        finally:
            if driver:
                driver.quit()

def process_downloaded_file(archive_path):
    """階段二：處理單一已下載的壓縮檔。"""
    if not archive_path:
        return

    # 從檔名中解析出 IP 位址
    filename = os.path.basename(archive_path)
    match = re.search(r'aidata_(.*?)_\d{8}\.tar\.gz', filename)
    if not match:
        print(f"❌ 無法從檔名 {filename} 解析出 IP 位址。")
        return
        
    ip_with_underscores = match.group(1)
    ip = ip_with_underscores.replace('_', '.')
    
    print(f"⚙️ [{ip}] 開始處理檔案：{filename}")
    try:
        ext_dir = os.path.join(DOWNLOAD_DIR, f"{ip}_{run_date_str}")
        os.makedirs(ext_dir, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as t:
            t.extractall(ext_dir)
        print(f"📂 [{ip}] 解壓至：{ext_dir}")
        
        process_logs(ext_dir, ip, data_date_str_for_filter, data_date_str_for_filename)
        print(f"✔️ [{ip}] 檔案處理完畢。")
    except Exception as e:
        print(f"❌ [{ip}] 處理檔案 {filename} 時發生錯誤: {e}")

# ====== 主程式：採用兩階段執行流程 ======

if __name__ == "__main__":
    start_time = time.time()
    print(f"🚀 開始執行自動化腳本 (執行日: {run_date}, 資料日: {data_date})")

    # --- 第一階段：平行下載所有檔案 ---
    print("\n===== 階段一：開始平行下載所有檔案 =====")
    downloaded_files = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_ip = {executor.submit(download_archive, ip): ip for ip in IPS}
        
        for future in as_completed(future_to_ip):
            result_path = future.result()
            if result_path: # 如果下載成功 (回傳路徑)，就加入清單
                downloaded_files.append(result_path)

    # --- 第二階段：循序處理已下載的檔案 ---
    print(f"\n===== 階段二：開始處理 {len(downloaded_files)} 個已下載的檔案 =====")
    for archive_path in downloaded_files:
        process_downloaded_file(archive_path)
            
    end_time = time.time()
    print(f"\n🎉 全部完成！總耗時: {end_time - start_time:.2f} 秒")