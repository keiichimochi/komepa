# KomePa - お米価格比較サイト

お米の価格比較・情報集約ウェブアプリケーションです。Gemini APIを使用してECサイトから商品情報を収集し、Cloudflare Workers + D1で提供します。

## アーキテクチャ

- **フロントエンド/バックエンド**: Cloudflare Workers (Hono framework)
- **データベース**: Cloudflare D1
- **画像ストレージ**: Cloudflare R2
- **スクレイピング**: Google Gemini API (Dockerコンテナで実行)

## セットアップ

### 1. Cloudflare Workersのセットアップ

```bash
# 依存関係のインストール
npm install

# D1データベースの作成
npm run create-db

# wrangler.tomlのdatabase_idを更新後、スキーマを適用
npm run init-db

# 開発サーバーの起動
npm run dev

# デプロイ
npm run deploy
```

### 2. Geminiスクレイパーのセットアップ

```bash
cd scraper

# .envファイルの作成
cp .env.example .env
# .envファイルを編集して必要な情報を設定

# Dockerコンテナの起動
docker-compose up -d
```

## 必要な環境変数

### Cloudflare Workers

`wrangler.toml`で設定:
- `database_id`: D1データベースのID
- `bucket_name`: R2バケット名（画像保存用）

### Geminiスクレイパー

`.env`ファイルで設定:
- `GEMINI_API_KEY`: Google Gemini APIキー
- `CF_ACCOUNT_ID`: CloudflareアカウントID
- `CF_DATABASE_ID`: D1データベースID
- `CF_API_TOKEN`: Cloudflare APIトークン

## Cloudflare APIトークンの取得

1. Cloudflareダッシュボードにログイン
2. 「My Profile」→「API Tokens」に移動
3. 「Create Token」をクリック
4. 以下の権限を持つトークンを作成:
   - Account: D1:Edit
   - Account: Workers R2 Storage:Edit

## 開発

### ローカルでの動作確認

```bash
# Workersの開発サーバー起動
npm run dev

# ブラウザで http://localhost:8787 にアクセス
```

### データベーススキーマの更新

`schema/schema.sql`を編集後:

```bash
npm run init-db
```

## デプロイ

```bash
npm run deploy
```

## ライセンス

ISC