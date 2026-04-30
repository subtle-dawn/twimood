import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# .envファイルから BEARER_TOKEN を読み込む
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH, override=True)

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USERNAME = os.getenv("X_USER_NAME")
X_API_BASE_URL = "https://api.x.com/2"

def get_user_id(username):
    if not BEARER_TOKEN:
        raise ValueError(".envにX_BEARER_TOKENを設定してください。")
    if not username:
        raise ValueError(".envにX_USER_NAMEを設定してください。")

    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    url = f"{X_API_BASE_URL}/users/by/username/{username}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["id"]

if __name__ == "__main__":
    user_id = get_user_id(USERNAME)
    print(f"ユーザー名：{USERNAME}")
    print(f"ユーザーID（数値）：{user_id}")
