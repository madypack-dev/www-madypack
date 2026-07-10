#!/usr/bin/env python3
import sys
import httpx
from lxml import html

LIVE_BASE = "https://madypack.com.ar"
PAGES = ["/", "/quienes-somos/", "/contacto/", "/cotizacion/", "/productos/"]

def fetch_and_analyze():
    client = httpx.Client(timeout=10.0, follow_redirects=True)
    for path in PAGES:
        url = f"{LIVE_BASE}{path}"
        print(f"\nFETCHING AND ANALYZING: {url}")
        print("=" * 60)
        try:
            response = client.get(url)
            if response.status_code == 404 and path == "/productos/":
                # Try WooCommerce /tienda/ path
                url = f"{LIVE_BASE}/tienda/"
                response = client.get(url)
            response.raise_for_status()
            
            tree = html.fromstring(response.text)
            
            # Extract H1 and H2s
            h1s = [el.text_content().strip() for el in tree.xpath("//h1")]
            h2s = [el.text_content().strip() for el in tree.xpath("//h2")]
            print(f"H1 headings: {h1s}")
            print(f"H2 headings: {h2s}")
            
            # Extract main paragraph or text snippets
            paragraphs = [p.text_content().strip() for p in tree.xpath("//p") if p.text_content().strip()]
            print(f"First few paragraphs (up to 3):")
            for p in paragraphs[:3]:
                print(f"  - {p}")
                
            # If there's a form, inspect its inputs
            forms = tree.xpath("//form")
            if forms:
                print(f"Forms found: {len(forms)}")
                for idx, form in enumerate(forms):
                    inputs = [f"{i.get('type','text')}:{i.get('name','')}" for i in form.xpath(".//input")]
                    textareas = [f"textarea:{t.get('name','')}" for t in form.xpath(".//textarea")]
                    print(f"  Form #{idx+1} action='{form.get('action','')}', fields={inputs + textareas}")
            else:
                print("No forms found on this page.")
                
        except Exception as e:
            print(f"Error fetching/parsing {url}: {e}")

if __name__ == "__main__":
    fetch_and_analyze()
