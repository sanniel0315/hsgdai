# 每日設備日誌自動下載與解析工具

這是一個自動化 Python 腳本，旨在每日定時執行，從多個指定的 IP 設備下載日誌數據，並將其處理、解析、清洗後，輸出為結構化的 CSV 檔案，方便後續的數據分析與歸檔。

---

## 🚀 功能特點

* **自動化下載**：透過 Selenium 自動登入多個設備網頁後台，並下載日誌壓縮檔 (`.tar.gz`)。
* **平行處理**：使用多執行緒 (`ThreadPoolExecutor`) 同時對多台設備進行下載，大幅提升執行效率。
* **錯誤容錯機制**：當遇到設備連線異常或下載逾時，程式會自動等待並重試一次，增加執行的穩定性。
* **每日排程設計**：程式會自動處理**前一天**的完整資料，確保每日數據報告的獨立與準確性。
* **彈性化設定**：透過外部的 `device_config.json` 檔案，可以靈活地設定不同設備或檢測項目的對應類型。
* **清晰的檔案管理**：
  * 每次執行的任務會以當天日期建立獨立的資料夾。
  * 最終產出的 CSV 與原始 TXT 檔案會以其**資料日期**命名，方便追溯。
  * 自動處理 Excel 中文亂碼問題 (使用 `UTF-8-SIG` 編碼)。

---

## 🛠️ 技術棧

* **Python 3**
* **Selenium**: 用於自動化網頁瀏覽器操作。
* **ChromeDriver**: Selenium 控制 Chrome 瀏覽器的驅動程式。

---

## ⚙️ 環境設定與安裝

在執行此腳本前，請確保完成以下設定：

1. **安裝 Git 並複製專案**：

   ```bash
   git clone [https://github.com/sannie10515/hsgdai.git](https://github.com/sannie10515/hsgdai.git)
   cd hsgdai
   ```
2. **安裝必要的 Python 套件**：

   ```bash
   pip install selenium
   ```
3. **下載並設定 ChromeDriver**：

   * 檢查您電腦上的 Chrome 瀏覽器版本 (`chrome://settings/help`)。
   * 前往 [Chrome for Testing 下載頁面](https://googlechromelabs.github.io/chrome-for-testing/)，下載與您瀏覽器版本**完全對應**的 `chromedriver.exe`。
   * 將解壓縮後的 `chromedriver.exe` 放入專案中的 `drivers/` 資料夾。
4. **設定腳本參數**：
   打開 `daily_job.py` 檔案，修改最上方的「設定」區塊：

   * `IPS`: 要抓取資料的設備 IP 位址清單。
   * `MAX_WORKERS`: 同時執行的最大線程數，請依電腦效能調整。
   * `USERNAME`, `PASSWORD`: 登入設備的帳號密碼。
   * `DOWNLOAD_DIR`: 下載與輸出檔案的根目錄。
   * `CHROMEDRIVER_PATH`: 指向 `drivers/chromedriver.exe` 的路徑 (建議使用腳本中的相對路徑寫法)。
5. **設定 `device_config.json`**：
   請根據您的設備與檢測需求，編輯此檔案。詳細說明請見下一節。

---

## 📄 `device_config.json` 設定檔案說明

此檔案用於定義「檢測類型 (`detection_type`)」的對應規則。

**情境A：簡單對應 (依設備名稱)**
如果一台設備只會有一種檢測類型。

```json
{
    "T61-FQH-S-CAM-SP-01": "人",
    "T61-FQH-N-CAM-SP-03": "車"
}
```
