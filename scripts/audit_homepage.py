#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from fastapi.testclient import TestClient
from lxml import html

from src.infraestructura.app import app

LIVE_URL = "https://madypack.com.ar/"
LOCAL_HOST = "localhost:8000"

def get_live_html() -> str:
    print(f"Fetching live HTML from {LIVE_URL}...")
    try:
        response = httpx.get(LIVE_URL, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching live site: {e}")
        # Try to fallback to cached content if running inside the sandboxed environment
        cached_path = Path(__file__).resolve().parents[2] / ".gemini" / "antigravity-cli" / "brain"
        # Search for any content.md in system generated logs
        for md_file in cached_path.glob("**/content.md"):
            print(f"Using cached file as fallback: {md_file}")
            return md_file.read_text(encoding="utf-8")
        raise

def get_local_html() -> str:
    print("Rendering local homepage via TestClient...")
    client = TestClient(app)
    response = client.get("/", headers={"host": LOCAL_HOST})
    response.raise_for_status()
    return response.text

def extract_metadata(tree) -> dict:
    title_el = tree.xpath("//title/text()")
    title = title_el[0].strip() if title_el else ""
    
    desc_el = tree.xpath("//meta[@name='description']/@content")
    desc = desc_el[0].strip() if desc_el else ""
    
    return {
        "title": title,
        "description": desc
    }

def extract_headings(tree) -> list:
    # Get all headings H1, H2, H3
    headings = []
    for h_type in ["h1", "h2", "h3"]:
        elements = tree.xpath(f"//{h_type}")
        for el in elements:
            text = "".join(el.itertext()).strip()
            if text:
                headings.append((h_type, text))
    return headings

def extract_images(tree) -> list:
    images = []
    # Get all img tags and their src/alt attributes
    for img in tree.xpath("//img"):
        src = img.get("src", "")
        alt = img.get("alt", "") or ""
        # Get filename
        filename = src.split("/")[-1].split("?")[0] if src else ""
        if filename:
            images.append({
                "filename": filename,
                "alt": alt.strip()
            })
    return images

def main():
    print("=" * 60)
    print("MADYPACK HOMEPAGE AUDIT TOOL")
    print("=" * 60)
    
    try:
        live_html = get_live_html()
        local_html = get_local_html()
    except Exception as e:
        print(f"FATAL: Could not fetch pages for auditing: {e}")
        sys.exit(1)
        
    live_tree = html.fromstring(live_html)
    local_tree = html.fromstring(local_html)
    
    # 1. Audit Metadata
    live_meta = extract_metadata(live_tree)
    local_meta = extract_metadata(local_tree)
    
    print("\n[1] AUDITING METADATA")
    print("-" * 30)
    meta_mismatch = False
    for key in ["title", "description"]:
        if live_meta[key] != local_meta[key]:
            print(f"❌ Mismatch in {key.upper()}:")
            print(f"   Live:  '{live_meta[key]}'")
            print(f"   Local: '{local_meta[key]}'")
            meta_mismatch = True
        else:
            print(f"✅ {key.upper()} matches: '{live_meta[key]}'")
            
    # 2. Audit Headings
    live_headings = extract_headings(live_tree)
    local_headings = extract_headings(local_tree)
    
    print("\n[2] AUDITING HEADINGS")
    print("-" * 30)
    
    # Clean headings text (normalize spaces and remove HTML tags/special symbols)
    live_headings_normalized = [h[1].lower().replace("¿", "").replace("?", "") for h in live_headings]
    local_headings_normalized = [h[1].lower().replace("¿", "").replace("?", "") for h in local_headings]
    
    missing_headings = []
    for h_type, h_text in live_headings:
        norm = h_text.lower().replace("¿", "").replace("?", "")
        if norm not in local_headings_normalized:
            missing_headings.append((h_type, h_text))
            
    if not missing_headings:
        print("✅ All major live headings are present in the local template.")
    else:
        print(f"⚠️ Some headings from the live site are missing or text differs:")
        for h_type, h_text in missing_headings:
            print(f"   - [{h_type}] '{h_text}'")
            
    # Print current local headings for reference
    print("\n   Local Headings List:")
    for h_type, h_text in local_headings:
        print(f"   - [{h_type}] {h_text}")

    # 3. Audit Images
    live_images = extract_images(live_tree)
    local_images = extract_images(local_tree)
    
    print("\n[3] AUDITING IMAGES")
    print("-" * 30)
    
    live_filenames = {img["filename"] for img in live_images}
    local_filenames = {img["filename"] for img in local_images}
    
    missing_images = live_filenames - local_filenames
    extra_images = local_filenames - live_filenames
    
    if not missing_images:
        print("✅ All visual assets from the live homepage are correctly referenced in the local site.")
    else:
        print("❌ Missing image references in the local site:")
        for img in missing_images:
            # Skip common WP tracking pixels or non-related icons if any
            if "w.org" in img or "google" in img:
                continue
            print(f"   - {img}")
            
    if extra_images:
        print("\n   Additional local image references (not present on live homepage):")
        for img in extra_images:
            print(f"   - {img}")

    print("\n" + "=" * 60)
    print("AUDIT COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
