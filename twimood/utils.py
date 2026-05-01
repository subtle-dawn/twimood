import json
from pathlib import Path

def load_ytd_archive(filepath):
    """
    Twitterアーカイブファイル（window.YTD.tweets.part0 = [...]）からツイートを抽出する関数
    """
    archive_path = Path(filepath)
    if not archive_path.exists():
        raise FileNotFoundError(f"Xアーカイブファイルが見つかりません: {archive_path}")

    raw_text = archive_path.read_text(encoding="utf-8").strip()

    # プレフィックスを除去してからJSONとして読み込む
    prefix = "window.YTD.tweets.part0 = "
    if raw_text.startswith(prefix):
        raw_text = raw_text[len(prefix):]
    if raw_text.endswith(";"):
        raw_text = raw_text[:-1].strip()

    data = json.loads(raw_text)
    tweets = [item["tweet"] for item in data]
    return tweets
