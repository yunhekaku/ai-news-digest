# AIニュースまとめアプリ 設計書 v0.1

## 1. 概要

本アプリは、AI関連ニュースを定期収集し、記事本文を抽出してLLMで要約・タグ付けし、Web UIで一覧・閲覧できる個人用アプリである。

主目的:
1. 個人用のAIニュース収集・閲覧基盤を作る
2. GCP / React / FastAPI / GitHub Actions の学習

---

## 2. スコープ

### MVPで実装
- AIニュース記事の定期収集
- 記事メタデータ保存
- 本文抽出
- LLM要約
- タグ付け
- 記事一覧表示
- 記事詳細表示
- GitHub Actionsによる定期実行
- Cloud Storage保存

### MVPではやらない
- ユーザー認証
- SNS投稿
- レコメンド
- 通知
- 課金

---

## 3. 技術構成

- Frontend: React + TypeScript
- Backend: FastAPI
- Hosting: Cloud Run
- Database: Supabase Postgres
- Storage: Cloud Storage
- CI/CD & Batch: GitHub Actions
- LLM: 外部API

---

## 4. アーキテクチャ概要

- React → FastAPI APIを呼ぶ
- FastAPI → DB保存
- FastAPI → Cloud Storage保存
- GitHub Actions → 定期実行
- LLM → 要約・タグ生成

---

## 5. 機能要件

### 記事収集
- RSS中心
- 新規記事のみ取得

### 保存データ
- source_name
- article_url
- title
- published_at
- fetched_at

### 重複判定
- URLベース

### 本文抽出
- HTML → テキスト
- 失敗時はログ

### 要約
- 日本語3〜5文

### タグ
例:
- LLM
- Agent
- Coding
- OpenAI
- Google
- OSS
- Research

---

## 6. 非機能要件

### コスト
- 低コスト（無料〜数千円）

### 保守性
- 型安全
- 責務分離

### 拡張性
- 通知
- スコアリング
- 多言語

---

## 7. データモデル

### articles
- id
- source_name
- article_url
- title
- published_at
- summary
- status
- created_at

### tags
- id
- name

### article_tags
- article_id
- tag_id

### ingestion_runs
- id
- started_at
- status
- total_inserted
- total_failed

---

## 8. API

### GET /api/articles
記事一覧

### GET /api/articles/{id}
記事詳細

### POST /api/admin/ingest
手動実行

### GET /health
ヘルスチェック

---

## 9. バッチ処理

1. RSS取得
2. 重複排除
3. 本文抽出
4. Storage保存
5. LLM要約
6. DB保存

---

## 10. フロント

### 一覧
- タイトル
- 要約
- タグ

### 詳細
- 要約
- 元記事リンク

---

## 11. ディレクトリ構成
repo/
├─ frontend/
├─ backend/
├─ docs/
└─ .github/

---

## 12. 環境変数
ANTHROPIC_API_KEY
LLM_API_KEY
SUPABASE_DB_URL
GCP_PROJECT_ID
GCS_BUCKET_NAME
VITE_API_BASE_URL

---

## 13. 実装方針

- シンプル優先
- MVP優先
- 過度な抽象化禁止

---

## 14. 優先順

1. 構成作成
2. API
3. UI
4. バッチ

---

## 15. Claude Code指示

- monorepo構成作成
- React + FastAPI
- DBモデル作成
- API作成
- UI作成
- GitHub Actions雛形作成

---

## 16. 初期タスク

- プロジェクト構成作成
- DBモデル
- API
- UI
- CI/CD