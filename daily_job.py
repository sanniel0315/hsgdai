import datetime
import time
import os
import tarfile
import csv
import json
import re
import logging
from logging.handlers import TimedRotatingFileHandler
import shutil
import requests 
import glob
from tqdm import tqdm
from requests.auth import HTTPDigestAuth
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.exceptions import InsecureRequestWarning

# 停用 InsecureRequestWarning 警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ====== 日誌設定函式 ======
def setup_logging():
    """設定日誌記錄器，並設定保留一年的日誌輪替"""
    log_filename = "daily_job.log"
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    file_handler = TimedRotatingFileHandler(
        log_filename, when='midnight', backupCount=365, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(stream_handler)

# 在主邏輯開始前先設定好 logging
setup_logging()

# ====== 載入設定檔 ======
BASE_DIR = os.path.dirname(__file__)
try:
    with open(os.path.join(BASE_DIR, "config.json"), encoding="utf-8") as f:
        config = json.load(f)

    IPS = config['devices']['ips']
    USERNAME = config['devices']['credentials']['username']
    PASSWORD = config['devices']['credentials']['password']
    MAX_WORKERS = config['execution']['max_workers']
    DOWNLOAD_DIR = config['paths']['download_dir']

except FileNotFoundError:
    logging.critical("❌ 致命錯誤：找不到 config.json 設定檔！程式無法繼續執行。")
    exit()
except KeyError as e:
    logging.critical(f"❌ 致命錯誤：config.json 檔案中缺少必要的鍵值：{e}！程式無法繼續執行。")
    exit()

# ====== 日期時間定義 ======
run_datetime = datetime.datetime.now()
data_date = run_datetime.date() - datetime.timedelta(days=1)
run_date_str = run_datetime.strftime("%Y%m%d")
run_timestamp_str = run_datetime.strftime("%Y%m%d_%H%M")
data_date_str_for_filter = data_date.strftime("%Y-%m-%d")
data_date_str_for_filename = data_date.strftime("%Y-%m-%d")

# ====== 載入設備偵測設定 ======
try:
    with open(os.path.join(BASE_DIR, "device_config.json"), encoding="utf-8") as f:
        DEVICE_CONFIG = json.load(f)
except FileNotFoundError:
    logging.info("ℹ️ 注意：找不到 device_config.json，detection_type 將全部顯示為「未知」。")
    DEVICE_CONFIG = {}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ====== 函式定義 ======

def process_logs(folder, ip, target_date_str):
    """解析日誌檔案，將結果回傳為一個列表。"""
    logging.info(f"🔷 [{ip}] 開始解析資料夾: {folder}")
    all_rows = []
    summary = {}
    for root, _, files in os.walk(folder):
        for fname in files:
            if not fname.lower().endswith(".txt"): continue
            inp = os.path.join(root, fname)
            processed_lines_in_file = 0
            try:
                with open(inp, 'r', encoding="utf-8") as fin:
                    for line in fin:
                        parts = line.strip().split("~")
                        if len(parts) < 3: continue
                        device, ts = parts[0], parts[1]
                        if not ts.startswith(target_date_str): continue
                        try:
                            data = json.loads(parts[-2])
                        except json.JSONDecodeError: data = {}
                        for key in data.keys():
                            processed_lines_in_file += 1
                            spec_dir_name = data.get(key, {}).get("SpecDirName", "")
                            status = data.get(key, {}).get("status", "")
                            config_value = DEVICE_CONFIG.get(device, "未知")
                            if isinstance(config_value, str): detection_type = config_value
                            elif isinstance(config_value, dict): detection_type = config_value.get(spec_dir_name, "未知")
                            else: detection_type = "未知"
                            all_rows.append([device, ts, spec_dir_name, status, detection_type])
                summary[fname] = processed_lines_in_file
            except Exception:
                logging.exception(f"❌ [{ip}] 解析檔案 {fname} 時發生嚴重錯誤！")
                summary[fname] = "Error"
    total_lines = len(all_rows)
    logging.info(f"✅ [{ip}] 從 {folder} 中總共解析出 {total_lines} 筆資料。")
    return {"data": all_rows, "summary": summary}


def download_archive(ip):
    """階段一：使用 requests 函式庫直接從IP下載檔案，包含認證。"""
    max_attempts = 2
    retry_delay = 60
    
    url = f"https://{ip}/pixord/model/aidataexport_3dago.php"
    temp_download_path = os.path.join(DOWNLOAD_DIR, f"aidata_{ip}_temp.tar.gz")
    
    for attempt in range(max_attempts):
        try:
            logging.info(f"📥 [{ip}] 開始直接下載 (第 {attempt + 1} 次嘗試)...")

            # 在下載前，只清理屬於自己的那個臨時檔案
            if os.path.exists(temp_download_path):
                os.remove(temp_download_path)

            with requests.get(url, auth=HTTPDigestAuth(USERNAME, PASSWORD), stream=True, verify=False, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))
                with open(temp_download_path, 'wb') as f, tqdm(
                    total=total, unit='B', unit_scale=True, unit_divisor=1024,
                    desc=f"📦 [{ip}] 下載中", ncols=80, leave=False
                ) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
                        
            # 檢查臨時檔案是否存在，確保下載成功
            if not os.path.exists(temp_download_path):
                raise FileNotFoundError("下載後未找到臨時檔案，可能下載失敗。")

            # 重新命名最終檔案
            dst = os.path.join(
                DOWNLOAD_DIR, f"aidata_{ip.replace('.', '_')}_{run_date_str}.tar.gz")
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(temp_download_path, dst)

            logging.info(f"✅ [{ip}] 直接下載完成：{dst}")
            return dst

        except requests.exceptions.RequestException as e:
            logging.warning(f"⚠️ [{ip}] 第 {attempt + 1} 次嘗試下載失敗: {e}")
            if attempt < max_attempts - 1:
                logging.info(f"⏰ [{ip}] 等待 {retry_delay} 秒後重試…")
                time.sleep(retry_delay)
            else:
                logging.error(f"❌ [{ip}] 下載重試失敗，跳過此 IP。")
                return None
        except Exception as e:
            logging.error(f"❌ [{ip}] 處理下載時發生非預期錯誤: {e}")
            # 確保在發生非預期錯誤時也清理臨時檔案
            if os.path.exists(temp_download_path):
                os.remove(temp_download_path)
            return None


def process_downloaded_file(archive_path):
    """階段二：處理單一已下載的壓縮檔，並回傳包含IP和資料的字典。"""
    if not archive_path: return None
    filename = os.path.basename(archive_path)
    match = re.search(r'aidata_(.*?)_(\d{8})\.tar\.gz', filename)
    if not match:
        logging.error(f"❌ 無法從檔名 {filename} 解析出 IP。")
        return None
    ip = match.group(1).replace('_', '.')
    run_date_from_name = match.group(2)
    logging.info(f"⚙️ [{ip}] 開始處理檔案：{filename}")
    try:
        ext_dir = os.path.join(DOWNLOAD_DIR, f"{ip}_{run_date_from_name}")
        os.makedirs(ext_dir, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as t:
            t.extractall(ext_dir)
        logging.info(f"📂 [{ip}] 解壓至：{ext_dir}")
        result = process_logs(ext_dir, ip, data_date_str_for_filter)
        parsed_data = result.get("data", [])
        summary = result.get("summary", {})
        logging.info(f"📊 [{ip}] 檔案處理筆數摘要：")
        if not summary:
            logging.info("   -> 未處理任何 .txt 檔案。")
        for txt_file, count in summary.items():
            logging.info(f"   -> {txt_file}: {count} 筆")
        logging.info(f"✔️ [{ip}] 檔案處理完畢。")
        return {"ip": ip, "data": parsed_data}
    except Exception:
        logging.exception(f"❌ [{ip}] 處理檔案 {filename} 時發生嚴重錯誤！")
        return None

if __name__ == "__main__":
    start_time = time.time()
    logging.info(f"🚀 開始執行自動化腳本 (執行時間: {run_datetime}, 資料日: {data_date})")
    logging.info("\n" + "="*20 + " 階段一：開始平行下載 " + "="*20)
    downloaded_files = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_ip = {executor.submit(download_archive, ip): ip for ip in IPS}
        for future in as_completed(future_to_ip):
            result_path = future.result()
            if result_path:
                downloaded_files.append(result_path)
    logging.info(f"\n" + "="*20 + f" 階段二：開始處理 {len(downloaded_files)} 個檔案並分類資料 " + "="*20)
    data_by_device = {}
    device_to_ip_map = {}
    for archive_path in downloaded_files:
        result = process_downloaded_file(archive_path)
        if not result: continue
        ip = result["ip"]
        data_from_file = result["data"]
        for row in data_from_file:
            device_name = row[0]
            if device_name not in data_by_device:
                data_by_device[device_name] = []
                device_to_ip_map[device_name] = ip
            data_by_device[device_name].append(row)
    logging.info("\n" + "="*20 + " 階段三：開始寫入各設備的獨立檔案 " + "="*20)
    if not data_by_device:
        logging.info("ℹ️ 沒有任何資料可供寫入，程序結束。")
    else:
        for device_name, rows in data_by_device.items():
            ip_address = device_to_ip_map.get(device_name, "UNKNOWN_IP")
            device_ip_folder = os.path.join(DOWNLOAD_DIR, ip_address)
            os.makedirs(device_ip_folder, exist_ok=True)
            final_csv_filename = f"{device_name}_{data_date_str_for_filename}_{run_timestamp_str}.csv"
            final_csv_path = os.path.join(device_ip_folder, final_csv_filename)
            try:
                with open(final_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["device", "timestamp", "SpecDirName", "status", "detection_type"])
                    writer.writerows(rows)
                logging.info(f"🎉 [{device_name}] 成功產生報表！共 {len(rows)} 筆資料。")
                logging.info(f"   報表路徑：{final_csv_path}")
            except Exception:
                logging.exception(f"❌ [{device_name}] 寫入最終 CSV 檔案時發生嚴重錯誤！")
                
    logging.info("\n" + "="*20 + " 階段四：開始清理臨時檔案 " + "="*20)
    for archive_path in downloaded_files:
        filename = os.path.basename(archive_path)
        match = re.search(r'aidata_(.*?)_(\d{8})\.tar\.gz', filename)
        if match:
            ip = match.group(1).replace('_', '.')
            run_date_from_name = match.group(2)
            ext_dir = os.path.join(DOWNLOAD_DIR, f"{ip}_{run_date_from_name}")
            try:
                if os.path.isdir(ext_dir):
                    shutil.rmtree(ext_dir)
                    logging.info(f"🗑️ 已刪除臨時資料夾: {ext_dir}")
            except Exception as e:
                logging.error(f"❌ 刪除資料夾 {ext_dir} 失敗: {e}")
        try:
            if os.path.exists(archive_path):
                os.remove(archive_path)
                logging.info(f"🗑️ 已刪除壓縮檔: {archive_path}")
        except Exception as e:
            logging.error(f"❌ 刪除檔案 {archive_path} 失敗: {e}")
    end_time = time.time()
    logging.info(f"\n🎉 全部完成！總耗時: {time.time() - start_time:.2f} 秒")