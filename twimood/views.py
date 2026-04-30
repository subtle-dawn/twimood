# twimood/views.py
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from .models import Tweet
from collections import Counter
from django.shortcuts import redirect, render
from .load_tweets import load_tweets_from_api_1month
import pandas as pd
import requests
from .analyzer import analyze_emotion_and_episode
from django.views.decorators.http import require_GET
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.db import models  # ← これが必要！
from .definitions import ALL_LABELS, EMOJI_MAP
from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse
from .utils import load_ytd_archive  # 上の関数をutils.pyに入れておくと良い

from .definitions import CATEGORY_MAP, CATEGORY_COLORS, CATEGORY_EMOJI

# 感情色
COLOR_POS_EMOTION = "#ef4444"
COLOR_NEG_EMOTION = "#3b82f6"

# エピソード色（
COLOR_POS_EPISODE = "#ef4444"
COLOR_NEG_EPISODE = "#3b82f6"
COLOR_UNKNOWN = "#9ca3af"

# ✅ APIからツイートを取得してDBに保存するビュー関数
def _default_start_date():
    return timezone.localdate()


def _default_end_date():
    return timezone.localdate()


def _parse_date_range(request):
    start_date = parse_date(request.POST.get("start_date", ""))
    end_date = parse_date(request.POST.get("end_date", ""))

    if not start_date or not end_date:
        raise ValueError("開始日と終了日を入力してください。")
    if start_date > end_date:
        raise ValueError("終了日は開始日以降の日付を選んでください。")

    start = datetime.combine(start_date, time.min)
    end = datetime.combine(end_date, time.max)
    aware_start = timezone.make_aware(start, timezone.get_current_timezone())
    aware_end = timezone.make_aware(end, timezone.get_current_timezone())
    return start_date, end_date, aware_start, aware_end


def _save_tweets_from_dataframe(df):
    if df.empty:
        return 0

    created = 0
    for _, row in df.iterrows():
        if not Tweet.objects.filter(date=row["date"], text=row["text"]).exists():
            Tweet.objects.create(date=row["date"], text=row["text"])
            created += 1
    return created


def _save_tweets_from_archive(start, end):
    archive_path = settings.BASE_DIR / "twimood" / "data" / "tweets.js"
    tweets = load_ytd_archive(archive_path)

    created = 0
    for t in tweets:
        text = t.get("full_text") or t.get("text")
        created_at = t.get("created_at")

        if not created_at or not text:
            continue

        try:
            dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            continue

        if not (start <= dt <= end):
            continue

        if not Tweet.objects.filter(date=dt, text=text).exists():
            Tweet.objects.create(date=dt, text=text)
            created += 1

    return created


def setup_page(request):
    context = {
        "start_date": _default_start_date().isoformat(),
        "end_date": _default_end_date().isoformat(),
        "tweet_count": Tweet.objects.count(),
        "unanalyzed_count": Tweet.objects.filter(labels="").count(),
    }

    if request.method == "POST":
        source = request.POST.get("source", "archive")

        try:
            start_date, end_date, start, end = _parse_date_range(request)
            context["start_date"] = start_date.isoformat()
            context["end_date"] = end_date.isoformat()

            if source == "archive":
                created = _save_tweets_from_archive(start, end)
                source_label = "Xアーカイブ"
            else:
                from .load_tweets import load_tweets_from_api_range

                df = load_tweets_from_api_range(
                    start.astimezone(dt_timezone.utc).replace(tzinfo=None),
                    end.astimezone(dt_timezone.utc).replace(tzinfo=None),
                )
                created = _save_tweets_from_dataframe(df)
                source_label = "X API"

            messages.success(
                request,
                f"{source_label}から{start_date}〜{end_date}のデータを取得しました。新規追加: {created}件",
            )
            return redirect("setup")
        except requests.exceptions.HTTPError as exc:
            response = exc.response
            if response is not None and response.status_code == 403:
                messages.error(
                    request,
                    "X APIで403 Forbiddenが返りました。このBearer Tokenではユーザーの投稿取得が許可されていない可能性があります。"
                    "X Developer Consoleで現在のAPIプランとAppの有効状態を確認してください。"
                    f"詳細: {exc}",
                )
            else:
                messages.error(request, f"X APIの呼び出しに失敗しました: {exc}")
        except Exception as exc:
            messages.error(request, str(exc))

    return render(request, "twimood/setup.html", context)


def import_tweets_from_api(request):
    # API経由で直近1ヶ月分のツイートを取得
    df = load_tweets_from_api_1month()

    print("---- IMPORTED ----")
    print(df.head())

    created = 0
    for _, row in df.iterrows():
        if not Tweet.objects.filter(date=row["date"], text=row["text"]).exists():
            Tweet.objects.create(
                date=row["date"],
                text=row["text"],
            )
            created += 1

    return JsonResponse({"imported": created})

# ✅ 3/24〜5/8の間のツイートを取得して保存するビュー関数
def import_between_mar24_may8(request):
    from .load_tweets import load_tweets_from_api_range

    start = datetime(2025, 3, 24, 0, 0, 0)
    end = datetime(2025, 5, 8, 23, 59, 59)

    df = load_tweets_from_api_range(start, end)

    # ✅ 取得失敗 or 空データ対策
    if df.empty:
        return JsonResponse({"imported": 0, "message": "No tweets retrieved from API."})

    created = 0
    for _, row in df.iterrows():
        if not Tweet.objects.filter(date=row["date"], text=row["text"]).exists():
            Tweet.objects.create(
                date=row["date"],
                text=row["text"],
            )
            created += 1

    return JsonResponse({"imported": created})

# ✅ アーカイブファイルからツイートを読み込むビュー関数
def import_archive_view(request):
    filepath = "data/tweets.js"  # ← 実際のファイルパスに修正
    tweets = load_ytd_archive(filepath)

    created = 0
    cutoff_date = datetime(2025, 3, 1, tzinfo=datetime.now().astimezone().tzinfo)

    for t in tweets:
        text = t.get("full_text") or t.get("text")
        created_at = t.get("created_at")

        if not created_at or not text:
            continue

        try:
            dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
        except ValueError:
            continue

        # 3月1日以降のツイートのみ対象
        if dt < cutoff_date:
            continue

        if not Tweet.objects.filter(date=dt, text=text).exists():
            Tweet.objects.create(date=dt, text=text)
            created += 1

    return JsonResponse({"imported": created})

# ✅ ツイートの感情・エピソード分析を実行するビュー関数
def analyze_tweets(request):
    from time import sleep

    tweets = Tweet.objects.filter(labels="")
    updated = 0

    for tweet in tweets:
        labels, _ = analyze_emotion_and_episode(tweet.text)
        tweet.labels = labels
        tweet.save()
        updated += 1
        sleep(0.8)  # 過負荷回避のため少し待つ

    messages.success(request, f"分析できました。分析済みツイート: {updated}件")
    return redirect("setup")

# ✅ カレンダー用に日ごとの感情イベントを整形して返すビュー関数
def emotion_calendar_events(request):
    events = []

    # 表示モード取得（simple / detailed）
    mode = request.GET.get("mode", "detailed")
    
    tweets = Tweet.objects.all()

    for date in sorted(set(t.date.date() for t in tweets)):
        day_tweets = [t for t in tweets if t.date.date() == date]

        combined_counter = Counter()

        for t in day_tweets:
            for label in (t.labels or "").split(","):
                label = label.strip()
                if label and label != "なし":
                    combined_counter[label] += 1

        if mode == "detailed":
            for label, count in sorted(combined_counter.items(), key=lambda x: -x[1]):
                for category, keywords in CATEGORY_MAP.items():
                    if label in keywords:
                        color = CATEGORY_COLORS[category]
                        emoji = EMOJI_MAP.get(label, "❓")
                        break
                else:
                    color = "#9ca3af"
                    emoji = "❓"

                events.append({
                    "id": f"{date}-{label}",
                    "title": f"{emoji}：{count}",
                    "start": str(date),
                    "end": str(date),
                    "color": color,
                    "allDay": True,
                    "extendedProps": {
                        "sort_order": 100 - count,
                        "label": label,
                        "emoji": emoji,
                        "count": count
                    }
                })
        else:
            # 簡略表示：感情＋エピソードを合算して4分類する
            combined_counter = combined_counter

            summary = []
            for category, keywords in CATEGORY_MAP.items():
                count = sum(count for k, count in combined_counter.items() if k in keywords)
                if count > 0:
                    summary.append((
                        category,
                        count,
                        CATEGORY_COLORS.get(category, "#9ca3af"),
                        CATEGORY_EMOJI.get(category, "❓")
                    ))

            for label, count, color, emoji in sorted(summary, key=lambda x: -x[1]):
                events.append({
                    "id": f"{date}-{label}",
                    "title": f"{emoji}：{count}",
                    "start": str(date),
                    "end": str(date),
                    "color": color,
                    "allDay": True,
                    "extendedProps": {
                        "label": label,
                        "emoji": emoji,
                        "count": count
                    }
                })

    return JsonResponse(events, safe=False)

# ✅ カレンダー画面を表示するビュー関数
def calendar_page(request):
    return render(request, 'twimood/calendar.html', {
        "today": timezone.localdate().isoformat(),
    })

@require_GET
# ✅ 指定ラベルに一致するツイートを日付で絞り込んで返すビュー関数
def get_tweets_by_label(request):
    from .definitions import EMOJI_MAP, CATEGORY_MAP

    date_str = request.GET.get("date")
    label = request.GET.get("label")
    mode = request.GET.get("mode", "detailed")

    if not date_str or not label:
        return JsonResponse({"tweets": []})

    # ラベルから絵文字を除去（🥰ポジティブな興奮 → ポジティブな興奮）
    emoji_to_category = {v: k for k, v in CATEGORY_EMOJI.items()}

    for emoji, category in emoji_to_category.items():
        if label.startswith(emoji):
            label = category
            break

    date = parse_date(date_str)
    tweets = Tweet.objects.filter(date__date=date)

    # カテゴリ名なら、その語句すべてを対象に
    if label in CATEGORY_MAP:
        keywords = CATEGORY_MAP[label]
    else:
        keywords = {label}

    # 該当する labels を含むツイートを抽出
    matching_tweets = []
    for t in tweets:
        label_set = {w.strip() for w in (t.labels or "").split(",") if w.strip()}
        if label_set & keywords:  # 共通部分があればマッチ
            matching_tweets.append(t)

    print(f"label={label}, keywords={keywords}, matched={len(matching_tweets)}")

    return JsonResponse({
        "tweets": [
            {
                "text": t.text,
                "datetime": t.date.strftime("%Y-%m-%d %H:%M"),
                "labels": t.labels
            }
            for t in matching_tweets
        ],
        "mode": mode
    })

# ✅ グラフ画面を表示するビュー関数
def graph_page(request):
    return render(request, 'twimood/graph.html', {
        "today": timezone.localdate().isoformat(),
    })

from .definitions import CATEGORY_MAP, CATEGORY_COLORS

@require_GET
# ✅ グラフ用の集計データ（感情カテゴリごとの時系列）を返すビュー関数
def graph_data(request):
    unit = request.GET.get("unit", "month")
    year = int(request.GET.get("year", datetime.now().year))
    month = int(request.GET.get("month", datetime.now().month))
    day = int(request.GET.get("day", datetime.now().day))

    base_date = datetime(year, month, day)

    if unit == "year":
        end = datetime(year, month, 1) + relativedelta(months=1)
        start = end - relativedelta(months=12)
        step = "month"
    elif unit == "week":
        start = base_date - timedelta(days=6)
        end = base_date + timedelta(days=1)
        step = "day"
    else:
        end = base_date + timedelta(days=1)
        start = end - relativedelta(months=1)
        step = "day"

    tweets = Tweet.objects.filter(date__gte=start, date__lt=end)

    counter = defaultdict(lambda: defaultdict(int))  # counter[日付][カテゴリ名]

    for tweet in tweets:
        date_key = tweet.date.strftime("%Y-%m") if step == "month" else tweet.date.strftime("%Y-%m-%d")
        words = (tweet.labels or "").split(",")
        for word in words:
            word = word.strip()
            if not word or word == "なし":
                continue
            for category, words_in_cat in CATEGORY_MAP.items():
                if word in words_in_cat:
                    counter[date_key][category] += 1

    # ラベル（日付）を生成
    labels = []
    current = start
    weekday_map = ["月", "火", "水", "木", "金", "土", "日"]

    while current < end:
        if step == "day":
            key = current.strftime("%Y-%m-%d")
            if unit == "week":
                key += f" ({weekday_map[current.weekday()]})"
        else:
            key = current.strftime("%Y-%m")
        labels.append(key)
        current += relativedelta(months=1) if step == "month" else timedelta(days=1)

    data_keys = [key.split()[0] for key in labels]

    # datasets構築（4本の棒）
    datasets = []
    for category in CATEGORY_MAP:
        # 落ち込みカテゴリだけ負の数値にする
        if category in {"正常な落ち込み", "異常な落ち込み"}:
            data = [-counter[k][category] if k in counter else 0 for k in data_keys]
        else:
            data = [counter[k][category] if k in counter else 0 for k in data_keys]

        datasets.append({
            "label": category,
            "data": data,
            "backgroundColor": CATEGORY_COLORS[category],
            "borderColor": CATEGORY_COLORS[category],
            "tension": 0.3
        })

    return JsonResponse({
        "labels": labels,
        "datasets": datasets
    })
