import json
import time
from playwright.sync_api import sync_playwright

def run_recon():
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pages": {},
        "console_errors": []
    }
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 2560, "height": 1440})
        page = context.new_page()

        # Capture console messages
        page.on("console", lambda msg: results["console_errors"].append(msg.text) if msg.type == "error" else None)

        # 1. Overview Page
        t0 = time.time()
        page.goto("http://127.0.0.1:3000/", wait_until="networkidle")
        load_time_overview = time.time() - t0
        page.wait_for_timeout(1000)
        
        # Extract 4-metric strip
        overview_text = page.locator("body").inner_text()
        results["pages"]["overview"] = {
            "load_time_s": round(load_time_overview, 3),
            "url": page.url,
            "title": page.title(),
            "has_hero": "Turning planetary observations into fundable urban interventions" in overview_text,
            "thermal_baseline": "46.36°C" if "46.36°C" in overview_text else "Not found",
        }

        # 2. Explore Pune
        t0 = time.time()
        page.goto("http://127.0.0.1:3000/explore/pune", wait_until="networkidle")
        load_time_explore = time.time() - t0
        page.wait_for_timeout(2000)

        # Look for layer toggle buttons and map elements
        buttons = page.locator("button").all_text_contents()
        
        # Test clicking cell 8960144d577ffff if possible or check layer toggles
        results["pages"]["explore"] = {
            "load_time_s": round(load_time_explore, 3),
            "url": page.url,
            "buttons": [b.strip() for b in buttons if b.strip()],
        }

        # 3. Portfolio Optimizer
        t0 = time.time()
        page.goto("http://127.0.0.1:3000/optimizer", wait_until="networkidle")
        load_time_opt = time.time() - t0
        page.wait_for_timeout(1500)
        opt_text = page.locator("body").inner_text()
        results["pages"]["optimizer"] = {
            "load_time_s": round(load_time_opt, 3),
            "url": page.url,
            "buttons": [b.strip() for b in page.locator("button").all_text_contents() if b.strip()],
            "text_preview": opt_text[:500]
        }

        # 4. Project Page
        t0 = time.time()
        page.goto("http://127.0.0.1:3000/projects/PROJ-PUNE-2025-BA225D6A", wait_until="networkidle")
        load_time_proj = time.time() - t0
        page.wait_for_timeout(1500)
        proj_text = page.locator("body").inner_text()
        results["pages"]["project"] = {
            "load_time_s": round(load_time_proj, 3),
            "url": page.url,
            "buttons": [b.strip() for b in page.locator("button").all_text_contents() if b.strip()],
            "text_preview": proj_text[:500]
        }

        # 5. MRV Page
        t0 = time.time()
        page.goto("http://127.0.0.1:3000/mrv", wait_until="networkidle")
        load_time_mrv = time.time() - t0
        page.wait_for_timeout(1500)
        mrv_text = page.locator("body").inner_text()
        results["pages"]["mrv"] = {
            "load_time_s": round(load_time_mrv, 3),
            "url": page.url,
            "buttons": [b.strip() for b in page.locator("button").all_text_contents() if b.strip()],
            "text_preview": mrv_text[:500]
        }

        browser.close()

    with open("docs/recon_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Recon complete. Saved to docs/recon_results.json")

if __name__ == "__main__":
    run_recon()

