import os
from pathlib import Path

import httpx
import openai
from django.conf import settings
from dotenv import load_dotenv

from .definitions import ALL_LABELS


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATHS = [
    BASE_DIR / ".env",
    Path(__file__).resolve().parent / ".env",
]
for env_path in ENV_PATHS:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

api_key = os.getenv("OPENAI_API_KEY")
analysis_ai_model = getattr(settings, "ANALYSIS_AI_MODEL", "gpt-3.5-turbo")

# Some local shells set HTTP(S)_PROXY to a dead localhost port. OpenAI/httpx
# honors proxy env vars by default, so ignore ambient proxy settings here.
http_client = httpx.Client(trust_env=False, timeout=30)
client = openai.OpenAI(api_key=api_key, http_client=http_client)

valid_labels = ALL_LABELS


class AnalysisError(Exception):
    pass


def _extract_labels(content):
    value = content.strip()
    for line in content.splitlines():
        if "感情・エピソード" in line:
            value = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            break

    if not value or value.lower() in {"なし", "特になし", "none"}:
        return "なし"

    words = [word.strip() for word in value.replace("、", ",").split(",")]
    words = [word for word in words if word in valid_labels]
    return ", ".join(words) if words else "なし"


def analyze_emotion_and_episode(text):
    if not api_key:
        raise AnalysisError("OPENAI_API_KEY が設定されていません。")

    prompt = f"""
あなたは、ツイート投稿者の感情や行動（エピソード）を分類する専門家です。
これは「ツイムード」というアプリで使用され、ツイートの中からユーザーの心理状態や日常行動を抽出することを目的としています。

以下のリストに含まれる語句のうち、ツイートから明確に読み取れるものをすべて抽出してください。
曖昧なものやリストにない語句は「なし」とし、文章で補完しないでください。

【抽出対象語リスト】
{", ".join(sorted(valid_labels))}

※リストにない語句（例: 楽しい気分、眠い、外食など）は抽出対象に含めないでください。

ツイート: 「{text}」

回答形式:
感情・エピソード：xx, xxx, ...
"""

    try:
        completion_params = {
            "model": analysis_ai_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        }
        if analysis_ai_model.startswith(("gpt-5", "o")):
            completion_params["max_completion_tokens"] = 800
            completion_params["reasoning_effort"] = "low"
            completion_params.pop("temperature", None)
        else:
            completion_params["max_tokens"] = 150

        response = client.chat.completions.create(
            **completion_params,
        )
    except openai.APIConnectionError as exc:
        raise AnalysisError(
            "OpenAI API に接続できませんでした。ネットワーク接続やプロキシ設定を確認してください。"
        ) from exc
    except openai.AuthenticationError as exc:
        raise AnalysisError("OpenAI API キーが無効、または期限切れの可能性があります。") from exc
    except openai.RateLimitError as exc:
        raise AnalysisError("OpenAI API のレート制限またはクォータ上限に達しました。") from exc
    except openai.NotFoundError as exc:
        raise AnalysisError(f"OpenAI モデルが見つかりません: {analysis_ai_model}") from exc
    except openai.PermissionDeniedError as exc:
        raise AnalysisError(f"このAPIキーではモデルを利用できません: {analysis_ai_model}") from exc
    except openai.BadRequestError as exc:
        raise AnalysisError(f"OpenAI API リクエストが無効です: {exc}") from exc
    except openai.APIError as exc:
        raise AnalysisError(f"OpenAI API エラー: {exc}") from exc
    except Exception as exc:
        raise AnalysisError(f"分析に失敗しました: {exc}") from exc

    content = response.choices[0].message.content or ""
    if not content.strip():
        finish_reason = response.choices[0].finish_reason
        raise AnalysisError(
            f"OpenAI API から空の応答が返りました。モデル: {analysis_ai_model}, finish_reason: {finish_reason}"
        )
    print("OpenAI response:", content)
    return _extract_labels(content), ""
