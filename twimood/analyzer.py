import openai
import os
from dotenv import load_dotenv
from .definitions import ALL_LABELS

# .envファイルからAPIキーを読み込む
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# OpenAIクライアント初期化
client = openai.OpenAI(api_key=api_key)

# フィルタ用のセット
valid_labels = ALL_LABELS

def analyze_emotion_and_episode(text):
    prompt = f"""
    あなたは、ツイートの感情や行動（エピソード）を分類する専門家です。
    これは「ツイムード」というアプリで使用され、ツイートの中からユーザーの心理状態や日常行動を抽出することを目的としています。

    以下のリストに含まれる語句のうち、ツイートから**明確に読み取れるものをすべて抽出**してください。
    曖昧なものやリストにない語は「なし」とし、文脈補完は行わないでください。

    【抽出対象語リスト】
    {", ".join(sorted(valid_labels))}

    ※リストにない語句（例：「楽しい気分」「眠い」「外出」など）は抽出対象に含めないでください。

    ツイート: 「{text}」

    回答形式：
    感情やエピソード：xxx, xxx, ...
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.4,
        )

        content = response.choices[0].message.content.strip()
        print("📩 応答内容:", content)

        value = ""
        for line in content.splitlines():
            if "感情やエピソード" in line:
                value = line.split("：", 1)[-1].strip()
                break

        if not value or value.lower() in ["なし", "特になし", "none"]:
            value = "なし"
        else:
            words = [w.strip() for w in value.split(",")]
            words = [w for w in words if w in valid_labels]
            value = ", ".join(words)

        return value, ""

    except Exception as e:
        print("🚨 APIエラー:", e)
        return f"エラー: {e}", ""
