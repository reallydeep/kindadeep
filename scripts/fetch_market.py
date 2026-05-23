#!/usr/bin/env python3
"""Build data/market.json from the free Yahoo Finance chart API.

For each index ticker, reads the latest price and previous close from the public
chart endpoint (no key, no login) and computes the percentage change. Indices are
grouped by country; the first index in each country is the headline. Crypto is NOT
handled here: the site fetches that live, client-side, from CoinGecko.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

# ── Config (edit freely) ────────────────────────────────────────────────────
# Each country: code, name, flag, and a list of (yahoo_symbol, label).
# The FIRST index is the headline shown collapsed; the rest appear on drill-down.
COUNTRIES = [
    {"code": "US", "name": "USA", "flag": "🇺🇸", "indices": [
        ("^GSPC", "S&P 500"), ("^DJI", "Dow Jones"), ("^IXIC", "Nasdaq"), ("^RUT", "Russell 2000"),
    ]},
    {"code": "JP", "name": "JAPAN", "flag": "🇯🇵", "indices": [
        ("^N225", "Nikkei 225"),
    ]},
    {"code": "IN", "name": "INDIA", "flag": "🇮🇳", "indices": [
        ("^NSEI", "NIFTY 50"), ("^BSESN", "SENSEX"), ("^NSEBANK", "Bank Nifty"),
    ]},
    {"code": "RU", "name": "RUSSIA", "flag": "🇷🇺", "indices": [
        ("IMOEX.ME", "MOEX"), ("RTSI.ME", "RTS"),
    ]},
    {"code": "CN", "name": "CHINA", "flag": "🇨🇳", "indices": [
        ("000001.SS", "Shanghai"), ("399001.SZ", "Shenzhen"),
        ("000300.SS", "CSI 300"), ("^HSI", "Hang Seng"),
    ]},
    {"code": "UK", "name": "LONDON", "flag": "🇬🇧", "indices": [
        ("^FTSE", "FTSE 100"), ("^FTMC", "FTSE 250"),
    ]},
]

REQUEST_TIMEOUT = 10
SPACING = 1.2          # seconds between calls, to stay under Yahoo's rate limit
BACKOFF = [5, 15, 30]  # retry waits on HTTP 429
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
# Two hosts: fall back to query2 if query1 throttles.
CHART_HOSTS = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]
CHART_PATH = "/v8/finance/chart/{}?range=5d&interval=1d"

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "market.json")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})


def _retry(fn):
    """Run fn, backing off on failure per BACKOFF."""
    last_exc = None
    for attempt in range(len(BACKOFF) + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < len(BACKOFF):
                time.sleep(BACKOFF[attempt])
    raise last_exc


def _get_crumb():
    """Prime cookies then fetch a Yahoo crumb (needed by the quote endpoint)."""
    try:
        SESSION.get("https://fc.yahoo.com", timeout=REQUEST_TIMEOUT)
    except Exception:
        pass

    def go():
        for host in CHART_HOSTS:
            r = SESSION.get(host + "/v1/test/getcrumb", timeout=REQUEST_TIMEOUT)
            txt = (r.text or "").strip()
            if r.status_code == 200 and txt and "Too Many" not in txt and "{" not in txt:
                return txt
        raise requests.HTTPError("crumb unavailable")
    return _retry(go)


def fetch_quotes_batch(symbols):
    """One request for all symbols: returns {symbol: {price, change_pct, currency}}."""
    crumb = _get_crumb()

    def go():
        last = None
        for host in CHART_HOSTS:
            r = SESSION.get(host + "/v7/finance/quote",
                            params={"symbols": ",".join(symbols), "crumb": crumb},
                            timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.json()["quoteResponse"]["result"]
            last = requests.HTTPError("quote status %s" % r.status_code)
        raise last
    results = _retry(go)

    out = {}
    for q in results:
        sym = q.get("symbol")
        price = q.get("regularMarketPrice")
        if sym is None or price is None:
            continue
        chg = q.get("regularMarketChangePercent")
        if chg is None:
            prev = q.get("regularMarketPreviousClose")
            chg = ((price - prev) / prev * 100) if prev else 0.0
        out[sym] = {
            "price": round(price, 2),
            "change_pct": round(chg, 2),
            "currency": q.get("currency", ""),
        }
    return out


def _get_chart(symbol):
    """Fallback: per-symbol chart JSON, retrying hosts and backing off on 429."""
    last_exc = None
    for attempt in range(len(BACKOFF) + 1):
        host = CHART_HOSTS[attempt % len(CHART_HOSTS)]
        try:
            resp = SESSION.get(host + CHART_PATH.format(symbol), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 429:
                raise requests.HTTPError("429 Too Many Requests")
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_exc = exc
            if attempt < len(BACKOFF):
                time.sleep(BACKOFF[attempt])
    raise last_exc


def fetch_index_fallback(symbol):
    """Fallback single-index fetch via the chart endpoint."""
    meta = _get_chart(symbol)["chart"]["result"][0]["meta"]
    price = meta.get("regularMarketPrice")
    prev = meta.get("chartPreviousClose") or meta.get("previousClose")
    if price is None or not prev:
        raise ValueError("missing price/prevClose")
    return {
        "price": round(price, 2),
        "change_pct": round((price - prev) / prev * 100, 2),
        "currency": meta.get("currency", ""),
    }


def main():
    all_symbols = [sym for c in COUNTRIES for sym, _ in c["indices"]]

    # Primary: one batched quote request for everything (avoids per-symbol rate limits).
    quotes = {}
    try:
        quotes = fetch_quotes_batch(all_symbols)
        print("[batch] {}/{} quotes".format(len(quotes), len(all_symbols)))
    except Exception as exc:
        print("[WARN] batch quote failed: {}; using per-symbol fallback".format(exc), file=sys.stderr)

    out_countries = []
    total_indices = 0
    for c in COUNTRIES:
        indices = []
        for symbol, label in c["indices"]:
            data = quotes.get(symbol)
            if not data:  # fallback for anything the batch missed
                try:
                    data = fetch_index_fallback(symbol)
                except Exception as exc:
                    print("[WARN] {} ({}) skipped: {}".format(label, symbol, exc), file=sys.stderr)
                time.sleep(SPACING)
            if data:
                indices.append({"symbol": symbol, "name": label, **data})
        if indices:
            out_countries.append({
                "code": c["code"],
                "name": c["name"],
                "flag": c["flag"],
                "indices": indices,
            })
            total_indices += len(indices)
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
        len(out_countries), total_indices, os.path.normpath(OUT_PATH)))


if __name__ == "__main__":
    main()
