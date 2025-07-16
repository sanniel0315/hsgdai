# 每日設備日誌自動下載與解析工具

這是一個自動化 Python 腳本，旨在每日定時執行，從多個指定的 IP 設備下載日誌數據，並將其處理、解析、清洗後，輸出為結構化的 CSV 檔案，方便後續的數據分析與歸檔。

---

## 🚀 功能特點

- **自動化下載**：透過 Selenium 自動登入多個設備網頁後台，並下載日誌壓縮檔 (`.tar.gz`)。
- **平行處理**：使用多執行緒 (`ThreadPoolExecutor`) 同時對多台設備進行下載，大幅提升執行效率。
- **錯誤容錯機制**：當遇到設備連線異常或下載逾時，程式會自動等待並重試一次，增加執行的穩定性。
- **每日排程設計**：程式會自動處理**前一天**的完整資料，確保每日數據報告的獨立與準確性。
- **彈性化設定**：透過外部的 `device_config.json` 檔案，可以靈活地設定不同設備或檢測項目的對應類型。
- **清晰的檔案管理**：
  - 每次執行的任務會以當天日期建立獨立的資料夾。
  - 最終產出的 CSV 與原始 TXT 檔案會以其**資料日期**命名，方便追溯。
  - 自動處理 Excel 中文亂碼問題 (使用 `UTF-8-SIG` 編碼)。

---

## 🛠️ 技術棧

- **Python 3**
- **Selenium**: 用於自動化網頁瀏覽器操作。
- **ChromeDriver**: Selenium 控制 Chrome 瀏覽器的驅動程式。

---

## ⚙️ 環境設定與安裝

### 🪟 Windows 環境

1. **安裝 Git 並複製專案**

   ```bash
   git clone [https://github.com/sanniel0315/hsgdai.git](https://github.com/sanniel0315/hsgdai.git)
   cd hsgdai
   ```
2. **安裝必要的 Python 套件**

   ```bash
   pip install selenium
   ```

   (建議使用虛擬環境 `python -m venv venv` 來管理套件)
3. **下載並設定 ChromeDriver**

   - **檢查版本**：在您的 Chrome 瀏覽器網址列輸入 `chrome://settings/help` 查看版本號。
   - **下載驅動**：前往 [Chrome for Testing 下載頁面](https://googlechromelabs.github.io/chrome-for-testing/)，下載與您瀏覽器版本**完全對應**的 `chromedriver-win64.zip`。
   - **放置檔案**：將解壓縮後的 `chromedriver.exe` 放入專案中的 `drivers/` 資料夾。
4. **設定腳本參數**

   - 打開 `daily_job.py` 檔案，修改最上方的「設定」區塊（`IPS`, `USERNAME`, `PASSWORD`, `DOWNLOAD_DIR`, `CHROMEDRIVER_PATH` 等）。
5. **編輯 `device_config.json`**

   - 根據您的設備與檢測需求，編輯此檔案。詳細說明請見下一節。

### 🐧 Ubuntu 環境 (支援離線安裝)

若要在無網路連線的 Ubuntu 主機上部署，請先在有網路的開發機上準備好所有檔案。

#### 步驟一：在有網路的機器上準備檔案

1. 下載 [Google Chrome for Debian/Ubuntu (.deb)](https://www.google.com/chrome/)。
2. 下載對應 Chrome 版本的 [ChromeDriver for Linux64 (.zip)](https://googlechromelabs.github.io/chrome-for-testing/)。
3. 將 `google-chrome-stable_current_amd64.deb` 和 `chromedriver-linux64.zip` 檔案，連同整個 `hsgdai` 專案資料夾，一起傳輸到目標 Ubuntu 主機（例如使用 `scp` 或隨身碟）。

#### 步驟二：在目標 Ubuntu 主機上進行安裝

1. **安裝 Chrome**

   ```bash
   # 進入存放檔案的目錄
   sudo dpkg -i google-chrome-stable_current_amd64.deb
   sudo apt-get -f install # 安裝可能缺少的依賴項
   ```
2. **安裝 ChromeDriver**

   ```bash
   unzip chromedriver-linux64.zip
   sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
   sudo chmod +x /usr/local/bin/chromedriver
   ```
3. **確認安裝**

   ```bash
   google-chrome --version
   chromedriver --version
   ```
4. **安裝 Selenium**

   ```bash
   pip3 install selenium
   ```
5. **執行腳本**

   ```bash
   cd /path/to/hsgdai
   python3 daily_job.py
   ```

---

## 📄 `device_config.json` 設定檔案說明

此檔案用於定義「檢測類型 (`detection_type`)」的對應規則。

### 簡單對應 (依設備名稱)

如果一台設備只會有一種檢測類型：

```json
{
    "T61-FQH-S-CAM-SP-01": "人",
    "T61-FQH-N-CAM-SP-03": "車"
}
```


### 複雜對應 (依 SpecDirName 區分)

如果一台設備會根據不同的 `SpecDirName` 有多種檢測類型：

**JSON**

```
{
    "T15-GNGS-S-CAM-SP-03": {
        "105": "人",
        "106": "車"
    }
}
```

---

## 📅 建議排程 (Crontab)

可透過 `crontab` 設定每日自動執行，例如在凌晨 2:00 執行，並將日誌輸出到 `daily_job.log`。

1. 編輯排程表：
   **Bash**

   ```
   crontab -e
   ```
2. 在檔案最下方新增一行（請將路徑修改為您專案的實際路徑）：
   **程式碼片段**

   ```
   0 2 * * * /usr/bin/python3 /path/to/hsgdai/daily_job.py >> /path/to/hsgdai/daily_job.log 2>&1
   ```

   * `>>`：將標準輸出附加到日誌檔。
   * `2>&1`：將錯誤輸出也一併導向到日.誌檔。

---

🎉 祝您順利完成每日自動化任務！
