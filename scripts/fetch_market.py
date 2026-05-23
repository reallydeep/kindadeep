#!/usr/bin/env python3
"""Build data/market.json from Stooq's free, keyless quote endpoint.

Yahoo Finance blocks datacenter / CI IP ranges, so the GitHub Action could not
fetch it. Stooq serves cloud IPs reliably and returns the latest close plus the
previous close for every symbol in a SINGLE request, from which we compute the
percentage change. No API key, no login. Crypto is handled live, client-side,
by CoinGecko (not here).
"""

import csv
import io
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

# ── Config (edit freely) ────────────────────────────────────────────────────
# Each country: code, name, flag, and a list of (stooq_symbol, label, currency).
# The FIRST index is the headline shown collapsed; the rest appear on drill-down.
COUNTRIES = [
    {"code": "US", "name": "USA", "flag": "🇺🇸", "indices": [
        ("^spx", "S&P 500", "USD"), ("^dji", "Dow Jones", "USD"), ("^ndq", "Nasdaq", "USD"),
    ]},
    {"code": "JP", "name": "JAPAN", "flag": "🇯🇵", "indices": [
        ("^nkx", "Nikkei 225", "JPY"),
    ]},
    {"code": "IN", "name": "INDIA", "flag": "🇮🇳", "indices": [
        ("^snx", "SENSEX", "INR"),
    ]},
    {"code": "RU", "name": "RUSSIA", "flag": "🇷🇺", "indices": [
        ("^moex", "MOEX", "RUB"), ("^rts", "RTS", "USD"),
    ]},
    {"code": "CN", "name": "CHINA", "flag": "🇨🇳", "indices": [
        ("^shc", "Shanghai", "CNY"), ("^hsi", "Hang Seng", "HKD"),
    ]},
    {"code": "UK", "name": "LONDON", "flag": "🇬🇧", "indices": [
        ("^ukx", "FTSE 100", "GBP"), ("^ftm", "FTSE 250", "GBP"),
    ]},
]

REQUEST_TIMEOUT = 12
BACKOFF = [5, 15, 30]   # retry waits if the request fails
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
# f=sohlcp -> Symbol, Open, High, Low, Close, Prev (previous close)
STOOQ_URL = "https://stooq.com/q/l/?s={}&f=sohlcp&h&e=csv"

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "market.json")


def fetch_stooq(symbols):
    """One request for all symbols -> {SYMBOL: {close, prev}} (keys uppercased)."""
    url = STOOQ_URL.format("+".join(symbols))
    last_exc = None
    for attempt in range(len(BACKOFF) + 1):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            out = {}
            for row in csv.DictReader(io.StringIO(r.text)):
                sym = (row.get("Symbol") or "").upper()
                try:
                    out[sym] = {"close": float(row["Close"]), "prev": float(row["Prev"])}
                except (ValueError, KeyError, TypeError):
                    continue  # N/D rows
            if out:
                return out
            raise ValueError("no parseable rows")
        except Exception as exc:
            last_exc = exc
            if attempt < len(BACKOFF):
                time.sleep(BACKOFF[attempt])
    raise last_exc


def main():
    all_symbols = [sym for c in COUNTRIES for sym, _, _ in c["indices"]]

    try:
        quotes = fetch_stooq(all_symbols)
        print("[stooq] {}/{} quotes".format(len(quotes), len(all_symbols)))
    except Exception as exc:
        print("[ERROR] Stooq fetch failed: {}; keeping previous feed".format(exc), file=sys.stderr)
        sys.exit(1)

    out_countries = []
    total = 0
    for c in COUNTRIES:
        indices = []
        for symbol, label, currency in c["indices"]:
            q = quotes.get(symbol.upper())
            if not q or not q["prev"]:
                print("[WARN] {} ({}) missing".format(label, symbol), file=sys.stderr)
                continue
            change_pct = (q["close"] - q["prev"]) / q["prev"] * 100
            indices.append({
                "symbol": symbol,
                "name": label,
                "price": round(q["close"], 2),
                "change_pct": round(change_pct, 2),
                "currency": currency,
            })
        if indices:
            out_countries.append({
                "code": c["code"], "name": c["name"], "flag": c["flag"], "indices": indices,
            })
            total += len(indices)
            print("[{}] {} indices".format(c["name"], len(indices)))

    if not out_countries:
        print("[ERROR] no market data produced; keeping previous feed", file=sys.stderr)
        sys.exit(1)

    payload = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "countries": out_countries,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("Wrote {} countries / {} indices to {}".format(
        len(out_countries), total, os.path.normpath(OUT_PATH)))


if __name__ == "__main__":
    main()
