# 📊 每日設備日誌自動下載與解析工具

這是一個自動化 Python 腳本，旨在每日定時執行，從多個指定的 IP 設備下載日誌數據，並將其處理、解析、清洗後，輸出為結構化的 CSV 檔案，方便後續的數據分析與歸檔。

---

## 🚀 功能特點

✅ 直接使用 HTTP Digest 認證下載設備日誌檔案
✅ 支援多執行緒平行處理，提高下載速度
✅ 自動解析壓縮檔、清洗資料、產生各設備報表
✅ 進度條顯示下載進度
✅ 自動清理臨時檔案、避免磁碟空間浪費
✅ 每日自動執行並記錄執行日誌 (`daily_job.log`)

---

## 🛠️ 技術棧

- **Python 3.10+**
- [requests](https://docs.python-requests.org/)
- [tqdm](https://tqdm.github.io/)
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)

---

## 📁 專案結構

本專案包含以下主要檔案與資料夾：

- `hsgdai/` (專案根目錄)
  - `daily_job.py`: 主程式腳本，包含了所有自動化邏輯。
  - `config.json`: **核心設定檔**。存放 IP、帳號密碼、輸出路徑等需要客製化的資訊。
  - `device_config.json`: **設備對應檔**。用於設定設備名稱與檢測類型的對應關係。
  - `requirements.txt`: 記錄專案所需的 Python 套件清單 (`requests`, `tqdm` 等)。
  - `Dockerfile`: 用於建立 Docker 映像檔的描述檔。
  - `README.md`: 專案說明文件 (就是您正在看的這份)。
  - `.gitignore`: 告訴 Git 哪些檔案或資料夾不需要被版本控制。
  - `daily_job.log`: **(執行後自動產生)** 每日執行的日誌記錄檔。
  - `logs/`: **(執行後自動產生)** 由 `config.json` 中 `download_dir` 指定的報表與臨時檔案輸出目錄。


## ⚙️ 安裝與執行

### 1. 安裝 Python 依賴
在終端機中，執行以下指令來安裝所有必要的套件：

```bash
pip install -r requirements.txt
```
2. 編輯 config.json
這個檔案是整個腳本的核心設定
```bash
{
  "devices": {
    "ips": ["10.0.0.1", "10.0.0.2"],
    "credentials": {
      "username": "admin",
      "password": "your_password"
    }
  },
  "execution": {
    "max_workers": 4
  },
  "paths": {
    "download_dir": "/path/to/your/logs"
  }
}
```

* ips：設備 IP 列表
* credentials：設備登入帳號密碼

* max_workers：並行下載數
* download_dir：報表輸出與臨時檔案目錄

###3. 執行腳本 
```bash

python daily_job.py
```

執行後會在 logs/ 目錄下產生各設備當天的 .csv 報表。

### 🐳 使用 Docker

📦 建立映像檔
bash
docker build -t spider-automation:1.0.1 .


🚀 執行容器
bash

docker run -v /your/logs:/app/logs spider-automation:1.0.1


-v 可將容器內 /app/logs 掛載到主機路徑，方便取出報表

📝 device_config.json 範例
單一檢測類型
```
json
{
    "DEVICE001": "人",
    "DEVICE002": "車"
}
多檢測類型
json
{
    "DEVICE003": {
        "105": "人",
        "106": "車"
    }
}
```
### 🗓️ 建議排程

如果想在 Linux 主機上每日凌晨 2:00 執行，可加入 crontab：

```bash

crontab -e
```
** 新增：

```bash

0 2 * * * /usr/bin/python3 /path/to/hsgdai/daily_job.py >> /path/to/hsgdai/daily_job.log 2>&1
```
📄 執行結果
執行紀錄會寫入：daily_job.log

下載檔案、解壓縮、CSV 報表會存放在 download_dir 指定的目錄

執行完成後會自動刪除壓縮檔與解壓縮臨時目錄
---
### 📜 版本資訊

版本號： 2.0.1
維護者： sanniel
更新日期： 2024-07
---
🎉 祝順利完成每日自動化任務！
