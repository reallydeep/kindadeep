#!/usr/bin/env python3
"""Build data/osint-feed.json from public Telegram OSINT channel previews.

Reads the free, no-auth t.me/s/<channel> web preview for each channel, keeps only
war-related posts, dedups, sorts newest-first, and writes a compact JSON the site
fetches at runtime. No API key, no login, no scraping of private content.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# ── Config (edit freely) ────────────────────────────────────────────────────
CHANNELS = [
    "OSINTWarfare",
    "IntelSky",
    "WarMonitor",
    "WarMonitors",
    "MenchOsint",
    "terroralarm",
    "OSINTtechnical",
]

WAR_KEYWORDS = [
    "iran", "israel", "israeli", "idf", "irgc", "tehran", "missile", "missiles",
    "drone", "drones", "uav", "strike", "strikes", "airstrike", "air strike",
    "hezbollah", "gaza", "ballistic", "interception", "intercept", "houthi",
    "rocket", "shahed", "iaf", "war", "military", "nuclear", "explosion",
    "shelling", "front line", "frontline", "casualt", "killed", "wounded",
]

# Telegram service-message noise to drop (channel actions, not real posts)
SERVICE_SKIP = ["pinned a", "pinned «", "joined the", "changed the group"]

MAX_ITEMS = 120
REQUEST_TIMEOUT = 8
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "osint-feed.json")


def is_war_related(text):
    low = text.lower()
    if any(skip in low for skip in SERVICE_SKIP):
        return False
    return any(kw in low for kw in WAR_KEYWORDS)


def parse_channel(slug, html):
    items = []
    soup = BeautifulSoup(html, "html.parser")
    for msg in soup.select("div.tgme_widget_message"):
        text_el = msg.select_one(".tgme_widget_message_text")
        if not text_el:
            continue
        text = text_el.get_text("\n", strip=True)
        if not text or not is_war_related(text):
            continue

        date_link = msg.select_one("a.tgme_widget_message_date")
        url = date_link.get("href") if date_link else None
        time_el = msg.select_one("a.tgme_widget_message_date time")
        timestamp = time_el.get("datetime") if time_el else None
        if not url or not timestamp:
            continue

        has_media = bool(
            msg.select_one(".tgme_widget_message_photo_wrap")
            or msg.select_one(".tgme_widget_message_video")
            or msg.select_one(".tgme_widget_message_roundvideo")
            or msg.select_one(".tgme_widget_message_document")
            or msg.select_one("video")
        )

        items.append({
            "id": hashlib.md5(url.encode("utf-8")).hexdigest(),
            "url": url,
            "source": "telegram",
            "channel": slug,
            "text": text,
            "timestamp": timestamp,
            "has_media": has_media,
        })
    return items


def fetch_channel(slug):
    resp = requests.get(
        "https://t.me/s/" + slug,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return parse_channel(slug, resp.text)


def main():
    all_items = []
    for slug in CHANNELS:
        try:
            found = fetch_channel(slug)
            print("[{}] {} war posts".format(slug, len(found)))
            all_items.extend(found)
        except Exception as exc:  # one bad channel must not kill the run
            print("[WARN] {} skipped: {}".format(slug, exc), file=sys.stderr)

    # Dedup by id, newest first
    seen = set()
    deduped = []
    for it in sorted(all_items, key=lambda x: x["timestamp"], reverse=True):
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        deduped.append(it)
    deduped = deduped[:MAX_ITEMS]

    if not deduped:
        print("[ERROR] no items produced; keeping previous feed", file=sys.stderr)
        sys.exit(1)

    payload = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(deduped),
        "items": deduped,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("Wrote {} items to {}".format(len(deduped), os.path.normpath(OUT_PATH)))


if __name__ == "__main__":
    main()
