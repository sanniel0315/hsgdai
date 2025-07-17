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

hsgdai/
├── daily_job.py # 主程式
├── config.json # 設定檔（IP、帳密、輸出路徑）
├── device_config.json # 設備與檢測項對應設定檔
├── requirements.txt # Python 套件清單
├── Dockerfile # Docker 映像檔描述
├── README.md # 專案說明
├── daily_job.log # 執行日誌（執行後產生）
└── logs/ # 下載及報表輸出路徑（config 設定）

---

## ⚙️ 安裝與執行

### 📦 安裝 Python 依賴

```bash
pip install -r requirements.txt
```

### 🖥️ 編輯 config.json

json
{
    "devices": {
        "ips": ["10.0.0.1", "10.0.0.2"],
        "credentials": {
            "username": "admin",
            "password": "password"
        }
    },
    "execution": {
        "max_workers": 4
    },
    "paths": {
        "download_dir": "/path/to/logs"
    }
}


* ips：設備 IP 列表
* credentials：設備登入帳號密碼

* max_workers：並行下載數
* download_dir：報表輸出與臨時檔案目錄

### 🖥️ 執行

bash

python daily_job.py

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

### 🗓️ 建議排程

如果想在 Linux 主機上每日凌晨 2:00 執行，可加入 crontab：

bash

crontab -e
新增：

bash

0 2 * * * /usr/bin/python3 /path/to/hsgdai/daily_job.py >> /path/to/hsgdai/daily_job.log 2>&1
📄 執行結果
執行紀錄會寫入：daily_job.log

下載檔案、解壓縮、CSV 報表會存放在 download_dir 指定的目錄

執行完成後會自動刪除壓縮檔與解壓縮臨時目錄

### 📜 版本資訊

版本號： 2.0.1
維護者： sanniel
更新日期： 2024-07

🎉 祝順利完成每日自動化任務！
