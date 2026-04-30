import openai
import os
from dotenv import load_dotenv

# .envファイルからAPIキーを読み込む
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 最新バージョン（>= 1.0.0）ではこの書き方でOK
client = openai.OpenAI(api_key=api_key)

def analyze_emotion_and_episode(text):
    prompt = f"""
以下のツイートから読み取れる「感情」と「エピソード」を抽出してください。

【感情】以下の中から該当するものを複数挙げてください。
あいまいな場合は「なし」としてください：

喜び、怒り、悲しみ、不安、無気力、躁、鬱、欲求、不快

【エピソード】
以下の中から、ツイートから**明確に読み取れる**ものがあれば挙げてください。
あいまいな場合は「なし」としてください：

ネガティブなエピソード：不眠、忘れ物、失くし物、過集中、衝動買い、風呂に入らなかった、学校・仕事を休んだ、体調不良、躁、鬱
ポジティブなエピソード：風呂に入った、旅行、友だちと遊んだ、買い物

ツイート: 「{text}」

回答形式：
感情：xxx, xxx, ...
エピソード：xxx, xxx, ...
"""

    try:
        print("🧠 分析中ツイート:", text[:50])

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.4,
        )

        content = response.choices[0].message.content.strip()
        print("📩 応答内容:", content)

        # 初期化
        emotion = ""
        episode = ""

        for line in content.splitlines():
            if line.startswith("感情："):
                value = line.replace("感情：", "").strip()
                if value.lower() in ["なし", "特になし", "none"]:
                    emotion = "なし"
                else:
                    emotion = value
            elif line.startswith("エピソード："):
                value = line.replace("エピソード：", "").strip()
                if value.lower() in ["なし", "特になし", "none"]:
                    episode = "なし"
                else:
                    episode = value


        return emotion, episode

    except Exception as e:
        print("🚨 APIエラー:", e)
        return f"エラー: {e}", ""
