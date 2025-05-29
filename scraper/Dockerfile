FROM python:3.11-slim

# 作業ディレクトリの設定
WORKDIR /app

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# 非rootユーザーの作成
RUN useradd -m -u 1000 scraper && chown -R scraper:scraper /app
USER scraper

# スクリプトの実行
CMD ["python", "scraper.py"]