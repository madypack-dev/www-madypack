#!/usr/bin/env python3
import sys
from pathlib import Path
from lxml import html
import httpx
from fastapi.testclient import TestClient

from src.infraestructura.app import app

LIVE_URL = "https://madypack.com.ar/"
LOCAL_HOST = "localhost:8000"

def get_text_nodes(tree):
    # Get all text elements from body, ignoring script, style, and comments
    body = tree.xpath("//body")[0]
    texts = []
    for el in body.iter():
        if el.tag in ["script", "style", "noscript", "iframe"]:
            continue
        # Get immediate text
        text = el.text.strip() if el.text else ""
        if text:
            texts.append((el.tag, text))
        # Get tail text
        tail = el.tail.strip() if el.tail else ""
        if tail:
            texts.append((el.tag + " (tail)", tail))
    return texts

def compare():
    client = httpx.Client(timeout=10.0, follow_redirects=True)
    try:
        live_res = client.get(LIVE_URL)
        live_html = live_res.text
    except Exception as e:
        print(f"Error fetching live: {e}")
        # Try to find a cached content.md
        cached_path = Path(__file__).resolve().parents[2] / ".gemini" / "antigravity-cli" / "brain"
        for md_file in cached_path.glob("**/content.md"):
            live_html = md_file.read_text(encoding="utf-8")
            break
            
    local_client = TestClient(app)
    local_res = local_client.get("/", headers={"host": LOCAL_HOST})
    local_html = local_res.text

    live_tree = html.fromstring(live_html)
    local_tree = html.fromstring(local_html)

    live_texts = get_text_nodes(live_tree)
    local_texts = get_text_nodes(local_tree)

    print(f"Total live text blocks: {len(live_texts)}")
    print(f"Total local text blocks: {len(local_texts)}")

    # Let's print all live text blocks to see if there's anything missing
    print("\n--- ALL LIVE SITE TEXT BLOCKS ---")
    for tag, txt in live_texts:
        # Filter out common header/footer menus or WooCommerce auth widgets to focus on homepage content
        if any(w in txt.lower() for w in ["username", "password", "remember me", "lost your password", "privacy policy"]):
            continue
        print(f"[{tag}]: {txt}")

if __name__ == "__main__":
    compare()
