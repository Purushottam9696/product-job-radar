#!/usr/bin/env python3
import os
import json
import time
import urllib.request
from datetime import datetime

COMPANIES_FILE = "companies_ats.json"
OUTPUT_FILE = "jobs.json"
HEADERS = {"User-Agent": "ProductPulse-JobCrawler/1.0 (+https://github.com)"}

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"  [WARN] Failed {url}: {e}")
    return None

def fetch_greenhouse(company):
    token = company["token"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    data = fetch_json(url)
    jobs = []
    if not data or "jobs" not in data:
        return jobs
    for item in data.get("jobs", []):
        loc = item.get("location", {}).get("name", "Remote / Multiple")
        jobs.append({
            "id": f"gh_{token}_{item['id']}",
            "company": company["name"],
            "title": item.get("title", "").strip(),
            "location": loc,
            "department": (item.get("departments") or [{}])[0].get("name", "Engineering"),
            "url": item.get("absolute_url", ""),
            "updated_at": item.get("updated_at", datetime.utcnow().isoformat()),
            "domain": company["domain"],
            "origin": company["origin"],
            "company_rating": company["rating"],
            "ats": "Greenhouse"
        })
    return jobs

def fetch_lever(company):
    token = company["token"]
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    data = fetch_json(url)
    jobs = []
    if not data or not isinstance(data, list):
        return jobs
    for item in data:
        cat = item.get("categories", {})
        loc = cat.get("location", "Remote")
        dept = cat.get("department") or cat.get("team") or "Engineering"
        post_time = item.get("createdAt")
        updated_at = datetime.fromtimestamp(post_time / 1000.0).isoformat() if post_time else datetime.utcnow().isoformat()
        jobs.append({
            "id": f"lev_{token}_{item['id']}",
            "company": company["name"],
            "title": item.get("text", "").strip(),
            "location": loc,
            "department": dept,
            "url": item.get("hostedUrl", ""),
            "updated_at": updated_at,
            "domain": company["domain"],
            "origin": company["origin"],
            "company_rating": company["rating"],
            "ats": "Lever"
        })
    return jobs

def main():
    print(f"[{datetime.utcnow().isoformat()}] Starting ProductPulse Job Crawler...")
    if not os.path.exists(COMPANIES_FILE):
        print(f"Error: {COMPANIES_FILE} not found!")
        return
    with open(COMPANIES_FILE, "r") as f:
        companies = json.load(f)

    existing_jobs = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                old_data = json.load(f)
                for j in old_data.get("jobs", []):
                    existing_jobs[j["id"]] = j.get("first_seen", datetime.utcnow().isoformat())
        except Exception:
            pass

    all_jobs = []
    now_iso = datetime.utcnow().isoformat()

    for comp in companies:
        name = comp["name"]
        ats = comp["ats"]
        c_jobs = []
        if ats == "greenhouse":
            c_jobs = fetch_greenhouse(comp)
        elif ats == "lever":
            c_jobs = fetch_lever(comp)
        for j in c_jobs:
            if j["id"] in existing_jobs:
                j["first_seen"] = existing_jobs[j["id"]]
                j["is_new"] = False
            else:
                j["first_seen"] = now_iso
                j["is_new"] = True
            all_jobs.append(j)
        time.sleep(0.2)

    result_payload = {
        "metadata": {
            "last_synced": now_iso,
            "total_jobs": len(all_jobs),
            "total_companies_tracked": len(companies),
            "new_jobs_count": sum(1 for j in all_jobs if j.get("is_new"))
        },
        "jobs": all_jobs
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result_payload, f, indent=2)
    print(f"Successfully synced {len(all_jobs)} jobs.")

if __name__ == "__main__":
    main()
