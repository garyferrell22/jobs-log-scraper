import os
import re
import json
import sys
import requests

BASE_URL = os.environ["BASE_URL"].rstrip("/")   # e.g. https://yourhost.com
UID      = os.environ["APP_UID"]
PWD      = os.environ["APP_PWD"]

# The statuses you want to track. Add/remove lines as you like —
# the text must match exactly what's rendered, e.g. "In Production".
STATUSES = [
    "In Production",
    "Pre-Production",
]

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (jobs-log-bot)"})

# 1. Log in (don't follow the redirect — just capture the session cookies)
login_url = f"{BASE_URL}/shared/aspx/app_logon.aspx"
resp = session.post(login_url, data={
    "sessionid": "",
    "uid": UID,
    "pwd": PWD,
    "target": "",
    "id": "",
}, timeout=30, allow_redirects=False)

# Accept the login response whether it's a 200 or a 302 redirect
if resp.status_code not in (200, 302):
    resp.raise_for_status()

# 2. Fetch the jobs_log page
page_url = f"{BASE_URL}/rpsigns/aspx/default.aspx?xml=jobs_log"
page = session.get(page_url, timeout=30, headers={
    "Referer": f"{BASE_URL}/shared/aspx/app_logon.aspx"
})
print("STATUS:", page.status_code)
print("BODY (first 1500 chars):", page.text[:1500])
page.raise_for_status()

# Sanity check: if we got bounced back to the login form, creds/URL are off
if "app_logon" in html.lower() and "In Production" not in html:
    print("ERROR: looks like login failed — got the logon page back.", file=sys.stderr)
    sys.exit(1)

# 3. Parse each status count: matches e.g. "In Production (65)"
counts = {}
for label in STATUSES:
    m = re.search(re.escape(label) + r"\s*\((\d+)\)", html)
    counts[label] = int(m.group(1)) if m else None

# Flag if nothing matched at all — page structure may have changed
if all(v is None for v in counts.values()):
    print("ERROR: no counts matched — page format may have changed.", file=sys.stderr)
    sys.exit(1)

# 4. Write count.json — flat keys are easiest for DakBoard to read
output = {"updated": __import__("datetime").datetime.utcnow().isoformat() + "Z"}
for label, value in counts.items():
    key = label.lower().replace(" ", "_").replace("-", "_")  # in_production, pre_production
    output[key] = value

with open("count.json", "w") as f:
    json.dump(output, f, indent=2)

print("Wrote count.json:", output)
