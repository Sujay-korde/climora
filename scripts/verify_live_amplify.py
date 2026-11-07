import urllib.request
import re

url = "https://main.dipd0dx7w10zl.amplifyapp.com/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode("utf-8")
    print("HTML response code:", resp.status)

js_match = re.search(r'assets/index-[^"\']+\.js', html)
if js_match:
    js_url = "https://main.dipd0dx7w10zl.amplifyapp.com/" + js_match.group(0)
    print("Live JS bundle URL:", js_url)
    with urllib.request.urlopen(js_url) as js_resp:
        js_code = js_resp.read().decode("utf-8")
        print("  Length of JS:", len(js_code), "bytes")
        print("  Contains 'Optimizer':", "Optimizer" in js_code)
        print("  Contains 'Interventions':", "Interventions" in js_code)
        print("  Contains 'MRV & Impact':", "MRV & Impact" in js_code or "MRV" in js_code)
        print("  Contains 'Methodology':", "Methodology" in js_code)
else:
    print("No JS bundle match found in HTML!")

