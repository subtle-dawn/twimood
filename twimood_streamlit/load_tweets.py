import json
import pandas as pd
import re

def load_tweets_from_js(path="data/tweets.js"):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    json_text = re.sub(r"^.*?=\s*", "", raw, count=1)
    tweets_data = json.loads(json_text)
    tweets = [
        {
            "date": t["tweet"]["created_at"],
            "text": t["tweet"].get("full_text") or t["tweet"].get("text")
        }
        for t in tweets_data
    ]
    df = pd.DataFrame(tweets)
    df["date"] = pd.to_datetime(df["date"])
    return df
