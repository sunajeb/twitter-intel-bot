#!/usr/bin/env python3
"""
LinkedIn Monitor via Phantombuster

Replicates the existing LinkedIn monitor flow (analysis, formatting, Slack)
but fetches posts using Phantombuster's LinkedIn Activity Extractor instead of ScrapIn.

Inputs via environment variables / config.json:
- GEMINI_API_KEY: for analysis
- SLACK_WEBHOOK_URL or config.json.slack_webhook_url: for Slack
- PHANTOMBUSTER_API_KEY: to call Phantombuster API
- PHANTOMBUSTER_AGENT_ID: optional (defaults to a LinkedIn Activity Extractor agent if not provided)
- LI_AT: LinkedIn session cookie value (required by the Phantom)
- PHB_USER_AGENT: optional user-agent string

Behavior mirrors linkedin_monitor.py:
- Loads accounts from linkedin_accounts.txt
- For a given date (defaults to today), fetches posts limited to that date window
- Analyzes with Gemini, formats, and posts to Slack
"""

import os
import re
import json
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

import requests

# Reuse analysis/formatting/slack logic by importing the existing monitor
from linkedin_monitor import LinkedInMonitor


def _to_mm_dd_yyyy(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%m-%d-%Y")


def _extract_company_name(linkedin_url: str) -> str:
    parts = linkedin_url.strip('/').split('/')
    if 'company' in parts:
        idx = parts.index('company')
        if idx + 1 < len(parts):
            return parts[idx + 1].title()
    return "Unknown Company"


class PhantomBusterClient:
    BASE = "https://api.phantombuster.com/api/v2"

    def __init__(self,
                 api_key: str,
                 agent_id: str,
                 session_cookie: str,
                 user_agent: Optional[str] = None):
        if not api_key:
            raise ValueError("PHANTOMBUSTER_API_KEY is required")
        if not session_cookie:
            raise ValueError("LI_AT (LinkedIn session cookie) is required")
        self.api_key = api_key
        self.agent_id = agent_id
        self.session_cookie = session_cookie
        self.user_agent = user_agent
        self.headers = {
            "X-Phantombuster-Key-1": self.api_key,
            "Content-Type": "application/json",
        }

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.BASE}{path}"
        r = requests.post(url, headers=self.headers, data=json.dumps(payload), timeout=60)
        if r.status_code >= 400:
            try:
                body = r.text
            except Exception:
                body = "<no body>"
            raise requests.HTTPError(f"{r.status_code} POST {url} – {body}")
        return r.json()

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.BASE}{path}"
        r = requests.get(url, headers=self.headers, params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    def launch_for_company(self, linkedin_company_url: str, date_after_mmddyyyy: str) -> str:
        arg = {
            "spreadsheetUrl": linkedin_company_url,
            "sessionCookie": self.session_cookie,
            # userAgent is optional but improves stability if provided
            "onlyRetrieveActivitiesAfterDate": True,
            "dateAfter": date_after_mmddyyyy,
            "numberMaxOfPosts": 50,
            "activitiesToScrape": ["Post"],
        }
        if self.user_agent:
            arg["userAgent"] = self.user_agent

        payload = {
            "id": self.agent_id,
            "argument": arg,
        }
        data = self._post("/agents/launch", payload)
        return data.get("containerId")

    def wait_for_container(self, container_id: str, timeout_sec: int = 120) -> dict:
        start = time.time()
        while time.time() - start < timeout_sec:
            info = self._get("/containers/fetch", params={"id": container_id})
            if info.get("status") == "finished":
                return info
            time.sleep(5)
        return info

    def fetch_logs(self, agent_id: str, container_id: str) -> str:
        data = self._get("/agents/fetch-output", params={"id": agent_id, "containerId": container_id})
        return data.get("output", "")

    def _extract_s3_json_url(self, logs: str) -> Optional[str]:
        # Look for a line like: JSON saved at https://phantombuster.s3.amazonaws.com/.../result.json
        m = re.search(r"https://phantombuster\.s3\.amazonaws\.com/\S+?\.json", logs)
        return m.group(0) if m else None

    def download_result_json(self, url: str) -> List[dict]:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        return r.json()


def parse_phb_items(items: List[dict], company_url: str, start_date: str, end_date: str) -> List[Dict]:
    # Convert date window to datetimes (inclusive for end)
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)

    def parse_dt(it: dict) -> Optional[datetime]:
        for k in ('timestamp', 'postTimestamp', 'postDate'):
            v = it.get(k)
            if not v:
                continue
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except Exception:
                pass
        return None

    out: List[Dict] = []
    for it in items:
        dt = parse_dt(it)
        if not dt:
            # If no timestamp, skip to avoid wrong-day leakage
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if not (start_dt <= dt <= end_dt):
            continue
        text = (it.get('postContent') or '').strip()
        url = it.get('postUrl') or ''
        out.append({
            "text": text,
            "url": url,
            "date": dt.isoformat(),
            "company_name": _extract_company_name(company_url),
        })
    return out


def run_with_phantombuster(date_str: Optional[str] = None):
    # Determine date (default to yesterday to ensure stable availability)
    if not date_str:
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # Load env for Phantombuster
    phb_key = os.getenv('PHANTOMBUSTER_API_KEY')
    agent_id = os.getenv('PHANTOMBUSTER_AGENT_ID', '3249419960471536')
    li_at = os.getenv('LI_AT')
    ua = os.getenv('PHB_USER_AGENT')
    if not phb_key or not li_at:
        raise ValueError("PHANTOMBUSTER_API_KEY and LI_AT must be set in environment")

    client = PhantomBusterClient(api_key=phb_key, agent_id=agent_id, session_cookie=li_at, user_agent=ua)

    # Instantiate the existing monitor to reuse analysis + Slack
    monitor = LinkedInMonitor()

    # Load accounts
    accounts = monitor.load_accounts()
    if not accounts:
        print("No LinkedIn accounts to monitor")
        return

    all_posts: List[Dict] = []
    mmddyyyy = _to_mm_dd_yyyy(date_str)
    for account_url in accounts:
        print(f"[PHB] Launching for {account_url} (dateAfter={mmddyyyy})")
        try:
            cid = client.launch_for_company(account_url, mmddyyyy)
            if not cid:
                print("Failed to obtain containerId; skipping.")
                continue
            info = client.wait_for_container(cid, timeout_sec=180)
            status = info.get('status')
            print(f"[PHB] Container {cid} status: {status}")
            if status != 'finished':
                print("Run did not finish in time; skipping.")
                continue
            logs = client.fetch_logs(agent_id, cid)
            s3_json_url = client._extract_s3_json_url(logs)
            if not s3_json_url:
                print("Could not locate result.json URL in logs; skipping.")
                continue
            items = client.download_result_json(s3_json_url)
            posts = parse_phb_items(items, account_url, date_str, date_str)
            print(f"[PHB] Got {len(posts)} posts in window from {account_url}")
            all_posts.extend(posts)
            # Small delay between accounts
            time.sleep(2)
        except Exception as e:
            print(f"[PHB] Error for {account_url}: {e}")
            continue

    print(f"Fetched {len(all_posts)} posts total (PHB)")

    if all_posts:
        print("\n=== FETCHED POSTS (PHB) ===\n")
        for i, post in enumerate(all_posts, 1):
            print(f"Post {i} - {post['company_name']}:")
            print(f"  Date: {post['date']}")
            print(f"  URL: {post['url']}")
            preview = post['text'][:200]
            print(f"  Text preview: {preview}..." if len(post['text']) > 200 else f"  Text: {post['text']}")
            print()
    else:
        print("No posts found for the specified date window (PHB).")

    # Analyze, format, and send to Slack via the existing methods
    analysis = monitor.analyze_posts_with_gemini(all_posts, date_str)
    slack_message = monitor.format_for_slack(analysis, date_str)
    monitor.send_slack_notification(slack_message)
    print("LinkedIn analysis (PHB) completed")


if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_with_phantombuster(date_arg)
