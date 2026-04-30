import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH, override=True)

# API認証情報（Bearer Token と User ID）を環境変数から取得
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USER_ID = os.getenv("X_USER_ID")
X_API_BASE_URL = "https://api.x.com/2"


def _format_x_error(response):
    try:
        data = response.json()
    except ValueError:
        detail = response.text
    else:
        errors = data.get("errors") or []
        if errors:
            detail = "; ".join(
                error.get("detail") or error.get("title") or str(error)
                for error in errors
            )
        else:
            detail = data.get("detail") or data.get("title") or str(data)

    detail = (detail or "").strip()
    if len(detail) > 500:
        detail = detail[:500] + "..."
    return detail


def _raise_for_status(response):
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        detail = _format_x_error(response)
        if detail:
            exc.args = (f"{exc.args[0]} / X response: {detail}",)
        raise

# ✅ 認証ヘッダーを生成する関数
def create_headers():
    if not BEARER_TOKEN:
        raise ValueError(".envにX_BEARER_TOKENを設定してください。")
    return {"Authorization": f"Bearer {BEARER_TOKEN}"}

# ✅ Twitter APIからツイートを取得する関数（全件・429対応・ページネーション対応・16分待機）
def fetch_tweets_from_api(start_time: datetime, end_time: datetime, max_results=100):
    if not USER_ID:
        raise ValueError(".envにX_USER_IDを設定してください。")

    url = f"{X_API_BASE_URL}/users/{USER_ID}/tweets"
    headers = create_headers()

    all_tweets = []
    next_token = None
    retry_count = 0

    while True:
        params = {
            "max_results": max_results,
            "start_time": start_time.replace(microsecond=0).isoformat("T") + "Z",
            "end_time": end_time.replace(microsecond=0).isoformat("T") + "Z",
            "tweet.fields": "created_at,text",
        }
        if next_token:
            params["pagination_token"] = next_token

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 429:
            wait_time = 16 * 60  # 16分 = 960秒
            print(f"🚨 429 Too Many Requests. {wait_time}秒（16分）待機します。")
            time.sleep(wait_time)
            retry_count += 1
            if retry_count > 3:
                print("❌ リトライ回数超過。中断します。")
                break
            continue
        else:
            retry_count = 0  # 成功したらリセット

        _raise_for_status(response)
        json_response = response.json()

        tweets = json_response.get("data", [])
        if not tweets:
            break

        all_tweets.extend(tweets)

        meta = json_response.get("meta", {})
        next_token = meta.get("next_token")
        if not next_token:
            break

    if not all_tweets:
        print("⚠️ 全ページからツイートを取得できませんでした。")
        return pd.DataFrame(columns=["date", "text"])  # ← ✅ 空でもカラム明示

    print(f"✅ 総取得件数: {len(all_tweets)} 件")
    tweets = [{"date": t["created_at"], "text": t["text"]} for t in all_tweets]
    df = pd.DataFrame(tweets)
    df["date"] = pd.to_datetime(df["date"])
    return df

# ✅ 今日から過去１ヶ月のツイートをAPIから取得する関数
def load_tweets_from_api_1month(path=None):
    # 取得期間を設定（UTCで現在〜30日前）
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    # 上記期間でAPIからツイートを取得
    return fetch_tweets_from_api(start, end)

# ✅ 任意の期間のツイートを取得して返す関数
def load_tweets_from_api_range(start: datetime, end: datetime):
    return fetch_tweets_from_api(start, end)
