import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# .envファイルから BEARER_TOKEN を読み込む
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATHS = [
    BASE_DIR / ".env",
    Path(__file__).resolve().parent / ".env",
]
for env_path in ENV_PATHS:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USERNAME = os.getenv("X_USER_NAME")
X_API_BASE_URL = "https://api.x.com/2"


def _get_without_system_proxy(url, **kwargs):
    session = requests.Session()
    session.trust_env = False
    return session.get(url, **kwargs)


def get_user_id(username):
    if not BEARER_TOKEN:
        raise ValueError(".envにX_BEARER_TOKENを設定してください。")
    if not username:
        raise ValueError(".envにX_USER_NAMEを設定してください。")

    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    url = f"{X_API_BASE_URL}/users/by/username/{username}"
    response = _get_without_system_proxy(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["id"]

if __name__ == "__main__":
    user_id = get_user_id(USERNAME)
    print(f"ユーザー名：{USERNAME}")
    print(f"ユーザーID（数値）：{user_id}")
