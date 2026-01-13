import json
import os
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

TICKERS = ["QSI", "QBTS", "RGTI", "IONQ", "QTUM"]

DATA_DIR = "docs/data"
LATEST_JSON = os.path.join(DATA_DIR, "latest.json")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)

def utc_now_iso():
    return utc_now().isoformat()

def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def fetch_price(ticker: str):
    """
    1) 5분봉(5m) 마지막 Close 시도
    2) 실패하면 fast_info.last_price로 폴백
    """
    # 1) 5분봉 시도
    try:
        df = yf.download(
            ticker,
            period="5d",
            interval="5m",
            progress=False,
            threads=False,
        )
        if df is not None and not df.empty:
            last_ts = df.index[-1]
            last_close = float(df["Close"].iloc[-1])

            # 타임존 UTC로 정리
            if getattr(last_ts, "tzinfo", None) is None:
                last_ts_utc = last_ts.to_pydatetime().replace(tzinfo=timezone.utc)
            else:
                last_ts_utc = last_ts.to_pydatetime().astimezone(timezone.utc)

            return last_close, last_ts_utc.replace(microsecond=0).isoformat(), "5m"
    except Exception:
        pass

    # 2) 폴백: fast_info
    try:
        tk = yf.Ticker(ticker)
        fi = getattr(tk, "fast_info", None)
        if fi and fi.get("last_price") is not None:
            return float(fi["last_price"]), utc_now_iso(), "fast_info"
    except Exception:
        pass

    return None, None, "none"

def main():
    ensure_dir()

    rows = []
    hist_row = {"timestamp_utc": utc_now_iso()}

    for t in TICKERS:
        price, price_time, src = fetch_price(t)
        rows.append({
            "ticker": t,
            "price_usd": (round(price, 6) if price is not None else None),
            "price_time_utc": price_time,
            "source": src,
        })
        hist_row[t] = price

    # latest.json 저장
    with open(LATEST_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {"generated_at_utc": utc_now_iso(), "rows": rows},
            f,
            ensure_ascii=False,
            indent=2,
        )

    # history.csv 이어쓰기(없으면 생성)
    if not os.path.exists(HISTORY_CSV):
        pd.DataFrame([hist_row]).to_csv(HISTORY_CSV, index=False)
    else:
        df_old = pd.read_csv(HISTORY_CSV)
        df_all = pd.concat([df_old, pd.DataFrame([hist_row])], ignore_index=True)

        # 너무 커지지 않게 최근 2000행 유지
        df_all = df_all.iloc[-2000:]
        df_all.to_csv(HISTORY_CSV, index=False)

if __name__ == "__main__":
    main()
