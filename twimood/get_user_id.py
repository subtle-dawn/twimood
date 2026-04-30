import requests
import os
from dotenv import load_dotenv

# .envファイルから BEARER_TOKEN を読み込む
load_dotenv()

BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USERNAME = os.getenv("X_USER_NAME")

def get_user_id(username):
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["id"]

if __name__ == "__main__":
    user_id = get_user_id(USERNAME)
    print(f"ユーザー名：{USERNAME}")
    print(f"ユーザーID（数値）：{user_id}")
