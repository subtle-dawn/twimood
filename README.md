# Twimood

Twimood は、X（旧 Twitter）の投稿を取り込み、OpenAI API で感情・行動ラベルを付けて、カレンダーやグラフで振り返るための Django アプリです。

## 主な機能

- X アーカイブ `tweets.js` から投稿を取り込み
- X API v2 から期間指定で投稿を取り込み
- OpenAI API による投稿テキストのラベル分析
- ラベル別の月間カレンダー表示
- 週・月・年単位の時系列グラフ表示
- ラベルをクリックして該当投稿の一覧を確認

## 画面

- `/`  
  投稿データの取り込みと未分析投稿の分析を行うセットアップ画面
- `/calendar/`  
  日ごとの感情・行動ラベルを確認するカレンダー画面
- `/graph/`  
  ラベルカテゴリの推移を見るグラフ画面

## セットアップ

### 1. 仮想環境を作成

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

### 2. 依存パッケージをインストール

```powershell
pip install Django pandas requests python-dotenv openai python-dateutil
```

### 3. 環境変数を設定

`.env.example` をコピーして `.env` を作成します。

```powershell
Copy-Item .env.example .env
```

`.env` に必要な値を設定します。

```env
X_USER_NAME=your_x_user_name_here
X_USER_ID=your_x_user_id_here
X_BEARER_TOKEN=your_x_bearer_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

X アーカイブだけを使う場合、投稿の取り込みには X API の値は不要です。分析を実行する場合は `OPENAI_API_KEY` が必要です。

### 4. データベースを準備

`db.sqlite3` はローカル環境ごとに作成される開発用データベースです。Git には含めず、必要な環境で次のコマンドを実行して作成します。

```powershell
python manage.py migrate
```

### 5. 開発サーバーを起動

```powershell
python manage.py runserver
```

ブラウザで `http://127.0.0.1:8000/` を開きます。

## 外部サービスの準備

### X アーカイブを取得する

X の公式ヘルプに従って、アカウントのアーカイブをリクエストします。

- 公式ヘルプ: [How to download your X archive](https://help.x.com/managing-your-account/how-to-download-your-twitter-archive)
- Web では `Settings and privacy` → `Your account` → `Download an archive of your data` からリクエストします。
- アーカイブの準備ができると、X から通知またはメールが届きます。
- ダウンロードした zip を展開し、`data/tweets.js` をこのプロジェクトの `twimood/data/tweets.js` に配置します。

### OpenAI API キーを取得する

OpenAI API で投稿を分析するには API キーが必要です。

- 公式クイックスタート: [Developer quickstart](https://platform.openai.com/docs/quickstart)
- API キー管理画面で新しいキーを作成します。
- 作成したキーは再表示できないため、安全な場所に控えます。
- このプロジェクトでは、`.env` の `OPENAI_API_KEY` に設定します。

## X アーカイブから取り込む

X のアーカイブデータに含まれる `tweets.js` を、次の場所に配置します。

```text
twimood/data/tweets.js
```

その後、トップ画面 `/` で期間を選び、「X アーカイブから取得」を選択して投稿を取り込みます。

## X API から取り込む

`.env` に `X_USER_ID` と `X_BEARER_TOKEN` を設定したうえで、トップ画面 `/` で期間を選び、「X API から取得」を選択して投稿を取り込みます。

X API の利用プランや権限によっては、投稿取得時に `403 Forbidden` やレート制限が発生する場合があります。

## 投稿を分析する

トップ画面 `/` の「未分析ツイートを分析」から、`labels` が空の投稿を OpenAI API で分析します。

分析結果は `Tweet.labels` にカンマ区切りのラベルとして保存されます。分析後、カレンダー画面とグラフ画面に結果が反映されます。

## データモデル

現在の主なモデルは `Tweet` です。

| フィールド | 内容 |
| --- | --- |
| `date` | 投稿日時 |
| `text` | 投稿本文 |
| `labels` | 分析で付与されたラベル |

## 使用している主なライブラリ

- Django
- pandas
- requests
- python-dotenv
- openai
- python-dateutil
- Bootstrap
- FullCalendar
- Chart.js

## 注意

- `.env` には API キーや Bearer Token が含まれるため、Git にコミットしないでください。
- `db.sqlite3` はローカル開発用の SQLite データベースです。投稿データを含むため Git にコミットしないでください。
- OpenAI API の分析実行には利用料金が発生する場合があります。
- X API には取得可能期間、レート制限、権限などの制約があります。
