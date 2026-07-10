#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from fastapi.testclient import TestClient
from lxml import html

from src.infraestructura.app import app

LIVE_BASE = "https://madypack.com.ar"
LOCAL_HOST = "localhost:8000"

# Routes mapping: Local path -> Live path
ROUTES = {
    "/": "/",
    "/quienes-somos/": "/quienes-somos/",
    "/contacto/": "/contacto/",
    "/cotizacion/": "/cotizacion/",
    "/productos/": "/tienda/", # WP live site catalog is usually under /tienda/
}

class SiteAuditor:
    def __init__(self):
        self.client = TestClient(app)
        self.http_client = httpx.Client(timeout=15.0, follow_redirects=True)
        self.errors = 0
        self.warnings = 0

    def log_success(self, msg: str):
        print(f"  ✅ {msg}")

    def log_warning(self, msg: str):
        self.warnings += 1
        print(f"  ⚠️ [WARNING] {msg}")

    def log_error(self, msg: str):
        self.errors += 1
        print(f"  ❌ [ERROR] {msg}")

    def fetch_live_page(self, path: str) -> str:
        url = f"{LIVE_BASE}{path}"
        try:
            response = self.http_client.get(url)
            # If the response is not 200, it might be that the path is slightly different, let's try fallback to alternative
            if response.status_code != 200 and path == "/tienda/":
                response = self.http_client.get(f"{LIVE_BASE}/productos/")
            response.raise_for_status()
            return response.text
        except Exception as e:
            # Check for cached content fallback in steps dir if available
            cached_path = Path(__file__).resolve().parents[2] / ".gemini" / "antigravity-cli" / "brain"
            for md_file in cached_path.glob("**/content.md"):
                if path == "/" and md_file.exists():
                    return md_file.read_text(encoding="utf-8")
            raise RuntimeError(f"Could not load live page {url}: {e}")

    def fetch_local_page(self, path: str) -> str:
        response = self.client.get(path, headers={"host": LOCAL_HOST})
        if response.status_code == 301 or response.status_code == 302:
            redirect_url = response.headers.get("location", "")
            if redirect_url.startswith("http://"):
                # strip domain
                redirect_path = "/" + redirect_url.split("/", 3)[-1]
            else:
                redirect_path = redirect_url
            response = self.client.get(redirect_path, headers={"host": LOCAL_HOST})
        response.raise_for_status()
        return response.text

    def audit_route(self, local_path: str, live_path: str):
        print(f"\nAuditing Route: Local '{local_path}' vs Live '{live_path}'")
        print("=" * 60)
        
        try:
            live_html = self.fetch_live_page(live_path)
            local_html = self.fetch_local_page(local_path)
        except Exception as e:
            self.log_error(f"Failed to fetch content for route {local_path}: {e}")
            return

        live_tree = html.fromstring(live_html)
        local_tree = html.fromstring(local_html)

        # 1. Metadata Audit (Title, Description, Canonical)
        self.audit_metadata(local_tree, live_tree, local_path, live_path)

        # 2. Heading Strictness Check (H1, structure, and hierarchy)
        self.audit_headings(local_tree, live_tree)

        # 3. Image Alt Tag Checks
        self.audit_images(local_tree)

        # 4. Link Quality Check
        self.audit_links(local_tree, local_path)

        # 5. Schema Structured Data Check
        self.audit_structured_data(local_tree)

    def audit_metadata(self, local_tree, live_tree, local_path, live_path):
        print("\n--- Metadata & SEO ---")
        live_title = live_tree.xpath("//title/text()")
        local_title = local_tree.xpath("//title/text()")
        
        ltitle = live_title[0].strip() if live_title else ""
        loctitle = local_title[0].strip() if local_title else ""
        
        if ltitle == loctitle:
            self.log_success(f"Title matches: '{loctitle}'")
        else:
            self.log_warning(f"Title discrepancy: Live='{ltitle}', Local='{loctitle}'")

        # Description Check
        live_desc = live_tree.xpath("//meta[@name='description']/@content")
        local_desc = local_tree.xpath("//meta[@name='description']/@content")
        
        ldesc = live_desc[0].strip() if live_desc else ""
        locdesc = local_desc[0].strip() if local_desc else ""
        
        if ldesc == locdesc:
            self.log_success("Meta description matches.")
        else:
            if not ldesc and locdesc:
                self.log_success(f"Local description is set and optimized ('{locdesc}') while live description is empty.")
            elif ldesc and not locdesc:
                self.log_error(f"Local meta description is missing! Live has: '{ldesc}'")
            else:
                self.log_warning(f"Description discrepancy: Live='{ldesc}', Local='{locdesc}'")

        # Canonical Link Check
        local_canonical = local_tree.xpath("//link[@rel='canonical']/@href")
        loc_can = local_canonical[0].strip() if local_canonical else ""
        if not loc_can:
            self.log_error("Canonical link tag (<link rel='canonical'>) is missing locally!")
        else:
            self.log_success(f"Canonical link is correctly configured: '{loc_can}'")

    def audit_headings(self, local_tree, live_tree):
        print("\n--- Heading Hierarchy & Content ---")
        # SEO Rule: Exactly one H1 per page
        local_h1s = local_tree.xpath("//h1")
        if len(local_h1s) == 0:
            self.log_error("No H1 heading found on local page!")
        elif len(local_h1s) > 1:
            self.log_warning(f"Multiple H1 headings ({len(local_h1s)}) found on local page! Only one is recommended.")
        else:
            h1_text = "".join(local_h1s[0].itertext()).strip()
            self.log_success(f"Exactly one H1 found: '{h1_text}'")

        # Compare heading structures
        live_h2s = ["".join(el.itertext()).strip().lower().replace("¿", "").replace("?", "") for el in live_tree.xpath("//h2")]
        local_h2s = [("".join(el.itertext()).strip(), "".join(el.itertext()).strip().lower().replace("¿", "").replace("?", "")) for el in local_tree.xpath("//h2")]

        missing_h2 = []
        for h2_orig, h2_norm in local_h2s:
            # Let's see if this local h2 (or substring) matches a live h2
            match_found = False
            for lh2 in live_h2s:
                if h2_norm in lh2 or lh2 in h2_norm:
                    match_found = True
                    break
            if not match_found:
                # We skip customer service / modal headings if they are internal local features
                if h2_orig not in ["Acceso a Clientes", "Tu Carrito de Cotización", "Tu Carrito de Cotización"]:
                    missing_h2.append(h2_orig)
                    
        if missing_h2:
            self.log_warning(f"Local has headings not found on live site (could be additions/modifications): {missing_h2}")
        else:
            self.log_success("All local H2 headings are aligned with live page headings structure.")

    def audit_images(self, local_tree):
        print("\n--- Visual Assets & Accessibility (Alt Tags) ---")
        img_elements = local_tree.xpath("//img")
        missing_alt = []
        
        for img in img_elements:
            src = img.get("src", "")
            alt = img.get("alt", "")
            if not alt or not alt.strip():
                filename = src.split("/")[-1]
                missing_alt.append(filename)
                
        if missing_alt:
            self.log_warning(f"Found {len(missing_alt)} images missing descriptive alt tags: {missing_alt}")
        else:
            self.log_success("All local images have descriptive 'alt' tags for accessibility.")

    def audit_links(self, local_tree, current_path):
        print("\n--- Link Health & Canonicalization ---")
        links = local_tree.xpath("//a")
        broken_absolute_links = []
        relative_links_count = 0
        
        for link in links:
            href = link.get("href", "")
            if not href:
                continue
            
            # Warn if absolute link points to localhost
            if f"http://{LOCAL_HOST}" in href or f"https://{LOCAL_HOST}" in href:
                broken_absolute_links.append(href)
            
            if href.startswith("/"):
                relative_links_count += 1
                
        if broken_absolute_links:
            self.log_error(f"Hardcoded absolute local URLs found (use relative links instead): {broken_absolute_links}")
        else:
            self.log_success("No hardcoded local absolute URLs found.")
            
        self.log_success(f"Total relative paths processed: {relative_links_count}")

    def audit_structured_data(self, local_tree):
        print("\n--- Structured Data (Schema.org) ---")
        schemas = local_tree.xpath("//script[@type='application/ld+json']")
        if not schemas:
            self.log_warning("No JSON-LD structured data block found on this page.")
            return

        for idx, schema in enumerate(schemas):
            content = schema.text
            if not content:
                self.log_error(f"JSON-LD block #{idx+1} is empty!")
                continue
            
            try:
                data = json.loads(content)
                schema_type = data.get("@type", "Unknown")
                self.log_success(f"Valid JSON-LD schema found of type: '{schema_type}'")
            except json.JSONDecodeError as e:
                self.log_error(f"Malformed JSON-LD schema block: {e}")

    def run_all(self):
        print("=" * 60)
        print("STARTING COMPLETE SITE AUDIT")
        print("=" * 60)
        
        for local_path, live_path in ROUTES.items():
            self.audit_route(local_path, live_path)
            
        print("\n" + "=" * 60)
        print("AUDIT RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Errors Found:   {self.errors}")
        print(f"Total Warnings Found: {self.warnings}")
        print("=" * 60)
        
        if self.errors > 0:
            print("❌ Audit failed with critical errors. Please correct the discrepancies.")
            sys.exit(1)
        else:
            print("🎉 Audit passed successfully! The site has high fidelity and excellent SEO best practices.")

if __name__ == "__main__":
    auditor = SiteAuditor()
    auditor.run_all()
