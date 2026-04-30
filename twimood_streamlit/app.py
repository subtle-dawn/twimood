import streamlit as st
import pandas as pd
from datetime import datetime
import os
from streamlit_calendar import calendar
from collections import Counter

from load_tweets import load_tweets_from_js
from analyzer import analyze_emotion_and_episode

st.set_page_config(page_title="Twimood カレンダー", layout="wide")
st.title("🧠 Twimood - 今月分ツイートの分析＆カレンダー表示")

# ファイルパス
monthly_raw_path = "tweets_this_month.csv"
monthly_analyzed_path = "tweets_analyzed_this_month.csv"

# 全ツイート読み込み
df_all = load_tweets_from_js()

# 今月分だけ抽出（UTC）
today = pd.Timestamp.today(tz="UTC")
start_of_month = today.replace(day=1)
start_of_next_month = (start_of_month + pd.DateOffset(months=1)).replace(day=1)
df_this_month = df_all[(df_all["date"] >= start_of_month) & (df_all["date"] < start_of_next_month)].copy()

# 空列を追加しておく
df_this_month["感情"] = ""
df_this_month["エピソード"] = ""

# 一時保存
df_this_month.to_csv(monthly_raw_path, index=False)

# 分析済みの読み込み
if os.path.exists(monthly_analyzed_path):
    df_saved = pd.read_csv(monthly_analyzed_path, parse_dates=["date"]).fillna("")
else:
    df_saved = pd.DataFrame(columns=["date", "text", "感情", "エピソード"])

# マージ
df_merged = pd.merge(
    df_this_month,
    df_saved,
    on=["date", "text"],
    how="left",
    suffixes=("_x", "_y")
)
df_merged["感情_y"] = df_merged["感情_y"].fillna("")
df_merged["エピソード_y"] = df_merged["エピソード_y"].fillna("")

# 未分析抽出
df_target = df_merged[(df_merged["感情_y"] == "") & (df_merged["エピソード_y"] == "")].copy()

# 分析実行
if not df_target.empty:
    with st.spinner("ChatGPTで今月分の感情・エピソード分析中..."):
        results = df_target["text"].apply(analyze_emotion_and_episode)
        df_target[["感情_y", "エピソード_y"]] = pd.DataFrame(results.tolist(), index=df_target.index)
        df_merged.update(df_target)

# 保存
df_merged["感情"] = df_merged["感情_y"]
df_merged["エピソード"] = df_merged["エピソード_y"]
df_merged[["date", "text", "感情", "エピソード"]].drop_duplicates().to_csv(monthly_analyzed_path, index=False)

# 表示用
df_display = df_merged[["date", "text", "感情", "エピソード"]].copy()

# --- カレンダー表示 ---
st.subheader("📅 今月の感情・エピソードカレンダー")

emoji_map = {
    "喜び": "😊", "怒り": "😡", "悲しみ": "😢", "不安": "😰",
    "無気力": "😶", "躁": "😆", "鬱": "🥀", "その他": "🤔",
    "忘れ物": "👜", "不眠": "🌙", "過集中": "🎯", "風呂に入った": "🛁",
    "風呂をやめた": "🚫🛁", "旅行": "🧳", "友だちと遊んだ": "🎉",
    "希死念慮": "💀", "学校・仕事を休んだ": "🏫🚫", "体調不良": "🤒",
    "衝動買い": "🛍", "失くし物": "🔍", "なし": "➖"
}

color_map = {
    "エピソード": "#f87171",  # 赤系
    "感情": "#60a5fa"       # 青系
}

# 日別イベント生成
df_display["date_only"] = df_display["date"].dt.date
calendar_events = []

for date, group in df_display.groupby("date_only"):
    # エピソード
    epi_counter = Counter()
    for val in group["エピソード"].dropna():
        for e in val.split(","):
            e = e.strip()
            if e:
                epi_counter[e] += 1

    for epi, count in sorted(epi_counter.items(), key=lambda x: -x[1]):
        icon = emoji_map.get(epi, "❓")
        calendar_events.append({
            "title": f"{icon}{epi}：{count}",
            "start": date.isoformat(),
            "end": date.isoformat(),
            "color": color_map["エピソード"]
        })

    # 感情
    emo_counter = Counter()
    for val in group["感情"].dropna():
        for e in val.split(","):
            e = e.strip()
            if e:
                emo_counter[e] += 1

    for emo, count in sorted(emo_counter.items(), key=lambda x: -x[1]):
        icon = emoji_map.get(emo, "❓")
        calendar_events.append({
            "title": f"{icon}{emo}：{count}",
            "start": date.isoformat(),
            "end": date.isoformat(),
            "color": color_map["感情"]
        })

# 表示
selected = calendar(
    events=calendar_events,
    options={
        "editable": False,
        "locale": "ja",
        "initialView": "dayGridMonth",
        "eventDisplay": "block"
    },
    key="emotion-calendar"
)

# 詳細表示
if selected and selected.get("start"):
    clicked_date = selected["start"][:10]
    st.subheader(f"🗂 {clicked_date} のツイート一覧")
    clicked_df = df_display[df_display["date"].dt.date == datetime.strptime(clicked_date, "%Y-%m-%d").date()]
    st.dataframe(clicked_df[["date", "text", "感情", "エピソード"]])
