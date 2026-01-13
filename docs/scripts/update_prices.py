import json
import os
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

TICKERS = ["QSI", "QBTS", "RGTI", "IONQ", "QTUM"]

DATA_DIR = "data"
LATEST_JSON = os.path.join(DATA_DIR, "latest.json")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")

def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def fetch_latest_5m_prices(tickers):
    """
    각 티커별로 5분봉(최근 1~2일) 데이터를 받아서 마지막 종가를 사용.
    yfinance는 간헐적으로 데이터가 없거나 지연될 수 있으니 예외 처리 포함.
    """
    results = []

    # interval=5m 은 보통 최근 며칠만 지원됨
    for t in tickers:
        try:
            df = yf.download(
                tickers=t,
                period="2d",
                interval="5m",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            if df is None or df.empty:
                results.append(
                    {"ticker": t, "price_usd": None, "price_time_utc": None, "source": "yfinance"}
                )
                continue

            # df index는 타임스탬프. 마지막 row 사용
            last_ts = df.index[-1]
            last_close = float(df["Close"].iloc[-1])

            # last_ts가 tz-aware 아닐 수 있어 안전하게 처리
            # yfinance는 종종 tz-aware를 주기도 함
            if getattr(last_ts, "tzinfo", None) is None:
                # tz 정보 없으면 UTC로 간주(완벽하지 않을 수 있음)
                last_ts_utc = last_ts.to_pydatetime().replace(tzinfo=timezone.utc)
            else:
                last_ts_utc = last_ts.to_pydatetime().astimezone(timezone.utc)

            results.append(
                {
                    "ticker": t,
                    "price_usd": round(last_close, 6),
                    "price_time_utc": last_ts_utc.replace(microsecond=0).isoformat(),
                    "source": "yfinance",
                }
            )
        except Exception:
            results.append(
                {"ticker": t, "price_usd": None, "price_time_utc": None, "source": "yfinance"}
            )

    return results

def write_latest_json(rows):
    payload = {
        "generated_at_utc": utc_now_iso(),
        "rows": rows,
    }
    with open(LATEST_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def append_history_csv(rows):
    """
    history.csv 포맷:
    timestamp_utc,QSI,QBTS,RGTI,IONQ,QTUM
    """
    ts = utc_now_iso()
    row_map = {r["ticker"]: r["price_usd"] for r in rows}

    new_row = {
        "timestamp_utc": ts,
        "QSI": row_map.get("QSI"),
        "QBTS": row_map.get("QBTS"),
        "RGTI": row_map.get("RGTI"),
        "IONQ": row_map.get("IONQ"),
        "QTUM": row_map.get("QTUM"),
    }

    file_exists = os.path.exists(HISTORY_CSV)
    df_new = pd.DataFrame([new_row])

    if not file_exists:
        df_new.to_csv(HISTORY_CSV, index=False)
        return

    # 기존 CSV 읽어서 이어붙이기
    try:
        df_old = pd.read_csv(HISTORY_CSV)
        df_all = pd.concat([df_old, df_new], ignore_index=True)

        # 너무 커지지 않게 최근 N개만 유지 (예: 2000행)
        MAX_ROWS = 2000
        if len(df_all) > MAX_ROWS:
            df_all = df_all.iloc[-MAX_ROWS:]

        df_all.to_csv(HISTORY_CSV, index=False)
    except Exception:
        # CSV가 깨졌거나 읽기 실패하면 새로 시작
        df_new.to_csv(HISTORY_CSV, index=False)

def main():
    ensure_data_dir()
    rows = fetch_latest_5m_prices(TICKERS)
    write_latest_json(rows)
    append_history_csv(rows)

if __name__ == "__main__":
    main()
