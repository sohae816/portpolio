"""공공데이터포털 '한국농수산식품유통공사_기간별 소매가격 정보 조회' 수집 스크립트.

인증키는 analysis/.env 의 DATA_GO_KR_KEY 에서 읽고, 화면·파일 어디에도 출력하지 않는다.

사용 예)
  .venv/bin/python fetch_retail.py --item 411 --start 20260801 --end 20261031
  .venv/bin/python fetch_retail.py --item 411 --item 412 --start 20260801 --end 20261031
"""
import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
URL = "https://apis.data.go.kr/B552845/periodRetail/price"
ROWS = 1000  # API 최대값


def load_key():
    env = HERE / ".env"
    if not env.exists():
        sys.exit("analysis/.env 가 없어요. 인증키부터 저장해주세요.")
    for line in env.read_text().splitlines():
        if line.startswith("DATA_GO_KR_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("analysis/.env 에 DATA_GO_KR_KEY 가 없어요.")


def fetch_page(key, start, end, page, item=None, vrty=None, grd=None, mrkt=None):
    params = {
        "serviceKey": key,
        "pageNo": page,
        "numOfRows": ROWS,
        "returnType": "JSON",
        "cond[exmn_ymd::GTE]": start,
        "cond[exmn_ymd::LTE]": end,
    }
    if item: params["cond[item_cd::EQ]"] = item
    if vrty: params["cond[vrty_cd::EQ]"] = vrty
    if grd: params["cond[grd_cd::EQ]"] = grd
    if mrkt: params["cond[mrkt_cd::EQ]"] = mrkt
    try:
        r = requests.get(URL, params=params, timeout=30)
    except requests.RequestException as e:
        # 요청 URL에 키가 들어 있어서 예외 메시지에서 지움
        sys.exit("요청 실패: " + str(e).replace(key, "***"))
    if r.status_code != 200:
        sys.exit(f"HTTP {r.status_code}: {r.text[:300].replace(key, '***')}")
    try:
        data = r.json()
    except ValueError:
        sys.exit("JSON이 아닌 응답: " + r.text[:300].replace(key, "***"))
    resp = data.get("response", data)
    header = resp.get("header", {})
    if header.get("resultCode") not in (None, "0", "00", "200"):
        sys.exit(f"API 오류 {header.get('resultCode')}: {header.get('resultMsg')}")
    body = resp.get("body", {})
    items = (body.get("items") or {}).get("item") or []
    if isinstance(items, dict):
        items = [items]
    return items, int(body.get("totalCount") or 0)


def fetch_all(key, start, end, **filters):
    rows, page = [], 1
    while True:
        items, total = fetch_page(key, start, end, page, **filters)
        rows += items
        print(f"  {filters.get('item') or '전체'} p{page}: {len(rows)}/{total}")
        if not items or len(rows) >= total:
            return rows
        page += 1
        time.sleep(0.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", action="append", help="품목코드 (여러 번 가능). 사과 411, 배 412")
    ap.add_argument("--vrty", help="품종코드")
    ap.add_argument("--grd", help="등급코드")
    ap.add_argument("--mrkt", help="시장코드")
    ap.add_argument("--start", required=True, help="YYYYMMDD")
    ap.add_argument("--end", required=True, help="YYYYMMDD")
    ap.add_argument("--out", help="저장할 CSV 경로 (기본: data/raw/retail_<품목>_<기간>.csv)")
    ap.add_argument("--peek", action="store_true", help="저장하지 않고 첫 페이지 몇 줄만 확인")
    a = ap.parse_args()

    key = load_key()
    items = a.item or [None]

    if a.peek:
        rows, total = fetch_page(key, a.start, a.end, 1, item=items[0], vrty=a.vrty, grd=a.grd, mrkt=a.mrkt)
        print(f"totalCount={total}, 첫 페이지 {len(rows)}건")
        if rows:
            print(pd.DataFrame(rows).head(5).to_string())
        return

    rows = []
    for it in items:
        rows += fetch_all(key, a.start, a.end, item=it, vrty=a.vrty, grd=a.grd, mrkt=a.mrkt)
    df = pd.DataFrame(rows)
    out = Path(a.out) if a.out else HERE / "data" / "raw" / f"retail_{'-'.join(i or 'all' for i in items)}_{a.start}_{a.end}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"저장: {out} ({len(df)}행)")


if __name__ == "__main__":
    main()
