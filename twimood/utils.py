import json

def load_ytd_archive(filepath):
    """
    Twitterアーカイブファイル（window.YTD.tweets.part0 = [...]）からツイートを抽出する関数
    """
    with open(filepath, encoding='utf-8') as f:
        raw_text = f.read()

    # プレフィックスを除去してからJSONとして読み込む
    prefix = "window.YTD.tweets.part0 = "
    if raw_text.startswith(prefix):
        raw_text = raw_text[len(prefix):]

    data = json.loads(raw_text)
    tweets = [item["tweet"] for item in data]
    return tweets
