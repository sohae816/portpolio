"""분석 결과를 사이트용 요약 JSON으로 내보낸다 (원본 데이터는 내보내지 않음).

  .venv/bin/python export_report.py
  → ../reports/chuseok-2026.json, ../reports/index.json, ../reports/chuseok-2026-notebook.html
"""
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "reports"
CHUSEOK = {2025: pd.Timestamp("2025-10-06"), 2026: pd.Timestamp("2026-09-25")}
BASE = (-50, -29)

df = pd.concat([pd.read_csv(f, dtype=str) for f in sorted((HERE / "data/raw").glob("retail_411-412_*.csv"))])
df["date"] = pd.to_datetime(df.exmn_ymd)
df["year"] = df.date.dt.year
df["price"] = pd.to_numeric(df.exmn_dd_prc, errors="coerce")
df["dday"] = (df.date - df.year.map(CHUSEOK)).dt.days
df["channel"] = np.where(df.mrkt_nm.str.contains("유통"), "유통업체", "전통시장")
df = df.dropna(subset=["price"]).drop_duplicates(["date", "mrkt_cd", "item_cd", "vrty_cd", "grd_cd"])

key = ["year", "mrkt_cd", "item_nm", "vrty_nm", "grd_nm"]
base = df[df.dday.between(*BASE)].groupby(key).price.mean().rename("base")
ix = df.join(base, on=key).dropna(subset=["base"])
ix["idx"] = ix.price / ix.base * 100
top = ix[ix.grd_nm == "상품"]


def series(d, lo, hi, roll=3):
    s = d[d.dday.between(lo, hi)].groupby("dday").idx.median().rolling(roll, center=True, min_periods=1).mean()
    return [[int(k), round(float(v), 1)] for k, v in s.items()]


def win(d, a, b):
    return round(float(d[d.dday.between(a, b)].idx.median()), 1)


def pick(year, item, vrty, channel=None):
    d = top[(top.year == year) & (top.item_nm == item) & (top.vrty_nm == vrty)]
    return d if channel is None else d[d.channel == channel]


charts = []
for item, vrty in [("사과", "홍로"), ("배", "신고")]:
    charts.append({
        "id": f"channel-{vrty}",
        "title": f"2026 {item} {vrty} 상품 · 채널별 가격 지수",
        "series": [
            {"name": "유통업체", "color": "accent", "points": series(pick(2026, item, vrty, "유통업체"), -40, 7)},
            {"name": "전통시장", "color": "warn", "points": series(pick(2026, item, vrty, "전통시장"), -40, 7)},
        ],
    })
for item, vrty in [("사과", "홍로"), ("배", "신고")]:
    charts.append({
        "id": f"year-{vrty}",
        "title": f"{item} {vrty} 상품 · 2025 vs 2026 가격 지수",
        "series": [
            {"name": "2026", "color": "accent", "points": series(pick(2026, item, vrty), -50, 7)},
            {"name": "2025", "color": "faint", "points": series(pick(2025, item, vrty), -50, 25)},
        ],
    })

# 상품/중품 비율 (같은 날 같은 시장)
pair = (df[df.grd_nm.isin(["상품", "중품"])]
        .pivot_table(index=["year", "dday", "mrkt_cd", "item_nm", "vrty_nm"], columns="grd_nm", values="price")
        .dropna().reset_index())
pair["ratio"] = pair["상품"] / pair["중품"]
ratio_pre = round(float(pair[(pair.year == 2026) & pair.vrty_nm.isin(["홍로", "신고"]) & pair.dday.between(-21, -1)].ratio.median()), 1)

hong_r = dict(charts[0]["series"][0]["points"] and charts[0]["series"][0]["points"])
rebound_lo = min(v for k, v in charts[0]["series"][0]["points"] if -7 <= k <= 2)
rebound_hi = [v for k, v in charts[0]["series"][0]["points"] if k == max(hong_r)][0]

kpis = [
    {"value": f"{win(pick(2026, '사과', '홍로'), -14, -1):.0f}", "unit": "", "label": "홍로 상품 추석 직전 지수", "note": "8월 기준가 = 100"},
    {"value": f"{ratio_pre}", "unit": "배", "label": "상품 ÷ 중품 가격", "note": "명절 전에도 평소와 같음"},
    {"value": f"{win(pick(2026, '사과', '홍로', '유통업체'), -14, -1):.0f}",
     "unit": f" vs {win(pick(2026, '사과', '홍로', '전통시장'), -14, -1):.0f}", "label": "유통업체 vs 전통시장 지수", "note": "홍로 · 추석 직전 2주"},
]

report = {
    "id": "chuseok-2026",
    "title": "추석에 과일값은 정말 오를까?",
    "date": "2026-10-05",
    "tags": ["사과", "배", "KAMIS", "추석"],
    "meta": f"사과·배 소매가격 · 전국 {df.mrkt_cd.nunique()}곳 · 2025·2026 추석 비교",
    "field": "2026-09-23 이마트 신도림점 — 제수용 과일이 매대 전면을 차지",
    "question": "명절 수요가 몰리면 제수용 과일 가격도 오를까?",
    "verdict": "틀림",
    "answer": "오르지 않았다. 햇과일 공급이 명절 수요보다 컸고, 유통업체는 오히려 행사가로 가격을 내려 손님을 끌었다.",
    "kpis": kpis,
    "headline_chart": "channel-홍로",
    "charts": charts,
    "chart_note": "지수 = 그날 가격 ÷ 그 시장의 8월 기준가 × 100 · 추석 당일 = D-day 0",
    "findings": [
        f"두 해 모두 추석 직전 가격이 8월 기준가 아래였다. 2026년 홍로 {kpis[0]['value']}, 신고배 {win(pick(2026, '배', '신고'), -14, -1):.0f} 수준.",
        f"상품/중품 가격 비율은 명절 전후 {ratio_pre}~1.3배로 그대로. 좋은 등급에 수요가 몰려 상품만 오르는 흐름은 없었다.",
        f"유통업체는 추석 직전 지수가 60대까지 내려갔다가, 추석이 지나자 홍로 {rebound_lo:.0f} → {rebound_hi:.0f}로 바로 반등했다. 명절 집객용 행사가로 해석된다.",
    ],
    "implications": [
        "명절 과일은 가격을 올리는 시즌이 아니라 행사가로 손님을 끌어오는 시즌이다. 마진은 산지 물량 선확보에서 나온다.",
        "추석이 빠른 해일수록 햇과일 출하와 겹쳐 원가 부담이 줄어든다. 추석 시점에 따라 행사 강도와 매입 시기를 달리 가져갈 수 있다.",
        "명절 직후 유통업체 가격이 정상가로 돌아가는 구간은 전통시장 대비 가격 경쟁력이 약해져, 잔여 물량 운영 계획이 따로 필요하다.",
    ],
    "method": [
        "데이터: 공공데이터포털 「한국농수산식품유통공사_기간별 소매가격 정보 조회」, 사과(홍로·후지·아오리)·배(신고·원황) 10개 단위 소매가",
        "두 해의 추석을 D-day로 맞추고(2025.10.6 / 2026.9.25), 시장마다 D-50~D-29 평균을 기준가 100으로 지수화",
        "같은 시장 안에서만 비교해, 날마다 조사 시장 구성이 바뀌어 생기는 착시를 줄였다",
    ],
    "limits": [
        "기준가 기간이 홍로 첫 출하(첫물 프리미엄) 시기와 겹쳐 하락 폭이 크게 보일 수 있다",
        "가격이 10개당이라 제수용 대과와 일반 과일을 구분하지 못한다",
        "유통업체가 익명이라 특정 업체(이마트 등) 단위로는 볼 수 없다",
        "2026년은 10/2까지만 있어 추석 이후는 1주만 확인했다",
    ],
    "next": "가락시장 도매 경락가·반입량을 붙여 '원가가 먼저 내렸는지 vs 소매 행사만인지' 구분하기",
    "notebook": "reports/chuseok-2026-notebook.html",
}
# 필드노트 카드에 연결했을 때 보이는 요약 (리포트를 고치면 카드도 같이 바뀜)
report["card"] = {
    "question": "명절 수요로 제수용 과일값이 오를까?",
    "status": "분석 완료",
    "sources": ["KAMIS", "현장 기록"],
    "target": "사과·배",
    "period": "2025·2026 8~10월",
    "kpis": [
        {"label": "홍로 추석 직전 지수", "value": kpis[0]["value"], "note": "8월 = 100"},
        {"label": "유통업체 지수", "value": kpis[2]["value"], "note": "전통시장 " + kpis[2]["unit"].replace(" vs ", "")},
        {"label": "상품 ÷ 중품", "value": f"{ratio_pre}배", "note": "평소와 같음"},
    ],
    "verdict": report["verdict"],
    "conclusion": "가격을 올린 게 아니라 행사가로 손님을 끌었다",
    "insight": "명절 마진은 가격 인상이 아니라 산지 물량 선확보에서 나온다",
}

OUT.mkdir(exist_ok=True)
(OUT / "chuseok-2026.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
index = [{k: report[k] for k in ("id", "title", "date", "meta", "verdict", "answer", "tags", "card")}]
(OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
shutil.copy(HERE / "chuseok_fruit_price.html", OUT / "chuseok-2026-notebook.html")
print(json.dumps(kpis, ensure_ascii=False), "\n", report["findings"][2])
