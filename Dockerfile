
# 使用 Python 3.10 slim 基礎映像
FROM python:3.10-slim

# 工作目錄
WORKDIR /app

# 複製依賴清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 預設執行
CMD ["python", "daily_job.py"]
