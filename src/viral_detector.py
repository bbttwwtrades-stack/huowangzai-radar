"""爆款判定邏輯：結合觀看門檻條件與短期成長率條件。"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from . import config


def is_viral(
    video: dict[str, Any],
    growth_rate: float | None,
    topic_cfg: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """
    判斷影片是否為爆款。

    Args:
        video: youtube_client._normalize_video() 回傳的標準化 dict。
        growth_rate: tracker.get_growth_rate() 的計算結果，None 表示無歷史數據。
        topic_cfg: 該主題設定；可用 threshold_fast / threshold_slow 覆寫全域門檻。

    Returns:
        (True, reason_str) 若符合爆款條件；(False, "") 若不符合。
    """
    now = datetime.now(timezone.utc)
    published_at: datetime = video["published_at"]
    view_count: int = video["view_count"]

    # 確保 published_at 為 aware datetime
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    age_hours = (now - published_at).total_seconds() / 3600
    age_days = age_hours / 24

    # 門檻條件 1：發布 N 小時內觀看超過 M
    topic_cfg = topic_cfg or {}
    fast = topic_cfg.get("threshold_fast", config.THRESHOLD_FAST)
    if age_hours <= fast["hours"] and view_count >= fast["views"]:
        views_fmt = _fmt_views(view_count)
        return (
            True,
            f"發布 {int(age_hours)} 小時內已累積 {views_fmt} 觀看次數"
            f"（門檻：{fast['hours']}hr / {_fmt_views(fast['views'])}）",
        )

    # 門檻條件 2：發布 N 天內觀看超過 M
    slow = topic_cfg.get("threshold_slow", config.THRESHOLD_SLOW)
    if age_days <= slow["days"] and view_count >= slow["views"]:
        views_fmt = _fmt_views(view_count)
        return (
            True,
            f"發布 {int(age_days)} 天內已累積 {views_fmt} 觀看次數"
            f"（門檻：{slow['days']}天 / {_fmt_views(slow['views'])}）",
        )

    # 成長條件：本次與上次記錄相比，成長率超過閾值
    if growth_rate is not None and growth_rate >= config.GROWTH_RATE_THRESHOLD:
        pct = int(growth_rate * 100)
        views_fmt = _fmt_views(view_count)
        return (
            True,
            f"自上次記錄以來觀看數成長 {pct}%（當前 {views_fmt} 觀看）",
        )

    return (False, "")


def _fmt_views(n: int) -> str:
    """將觀看數格式化為易讀字串，例如 1,234,567 → 123.5萬。"""
    if n >= 10_000_000:
        return f"{n / 10_000_000:.1f}千萬"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}百萬"
    if n >= 10_000:
        return f"{n / 10_000:.1f}萬"
    return f"{n:,}"


# ── 標題語言過濾（只保留繁體中文標題）──────────────────────────────────────────
_KANA = re.compile(r"[\u3040-\u30ff]")
_CJK = re.compile(r"[\u4e00-\u9fff]")
# 常見簡體專用字與其繁體對應字，用來判斷標題偏簡體或繁體
_SIMP_ONLY = set("这们个来时会说为对发经过还进动样问题让给东车门见长话间头点实现学习认识应该没难爱钱么吗还记录带宝妈乐儿岁亲减肥欢厉无语视频关系问开万与业书买卖专历压厂县员团国图圆场处备复够奖学实宁宝将层岁币师帮广庆应强总战户扫报抢护担挡据权条极标样桥检树欢气汉汤沟没泪洁浅测济浓涨温湾满灭灯炼烦热爷牵犹独猎环现电画畅疗盖监盘着确础离种积称稳穷窃竞笔笋签简类粮紧红约级纪纯纸线练组细终经结给绝统继续绿维网罗职联肤脑脸节苏药获萝虑虽补装觉观视规览让议记讲许论设识证评诉词试诗话该详语误说请诸读谁调谈谢贝负财责败货质购贵费贴资赏赚赞赵车转软轻载较辆输边达运还这进远连迟适选递逻遗邮释钟钱铁银错锋长门问间闻闹队阳阴际陆陈险随隐难雾静须顾顿预领频题风飞饭饮马驾验骑鱼鸟鸡麦黄齐龙")
_TRAD_ONLY = set("這們個來時會說為對發經過還進動樣問題讓給東車門見長話間頭點實現學習認識應該沒難愛錢麼嗎記錄帶寶媽樂兒歲親減歡厲無語視頻關係開萬與業書買賣專歷壓廠縣員團國圖圓場處備複夠獎將層幣師幫廣慶應強總戰戶掃報搶護擔擋據權條極標橋檢樹氣漢湯溝淚潔淺測濟濃漲溫灣滿滅燈煉煩熱爺牽猶獨獵環電畫暢療蓋監盤著確礎離種積稱穩窮竊競筆筍簽簡類糧緊紅約級紀純紙線練組細終經結絕統繼續綠維網羅職聯膚腦臉節蘇藥獲蘿慮雖補裝覺觀規覽議講許論設證評訴詞試詩詳誤請諸讀誰調談謝貝負財責敗貨質購貴費貼資賞賺讚趙轉軟輕載較輛輸邊達運遠連遲適選遞邏遺郵釋鐘鐵銀錯鋒聞鬧隊陽陰際陸陳險隨隱霧靜須顧頓預領頻風飛飯飲馬駕驗騎魚鳥雞麥黃齊龍")


def is_traditional_chinese(title: str) -> bool:
    """標題含日文假名、沒有中文、或簡體字不少於繁體字時回傳 False。"""
    if _KANA.search(title) or not _CJK.search(title):
        return False
    simp = sum(1 for ch in title if ch in _SIMP_ONLY)
    trad = sum(1 for ch in title if ch in _TRAD_ONLY)
    return simp == 0 or simp < trad
