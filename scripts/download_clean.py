#!/usr/bin/env python3
"""
Скачивает готовые чистые планировки из Higgsfield (CloudFront) в assets/plans_clean/.

Источник ссылок — scripts/clean_jobs.json (поле cards[].clean_job + unique_clean_jobs[].result_url).
Требует открытого egress к *.cloudfront.net (хосты d8j0ntlcm91z4 / d2ol7oe51mr4n9).

Использование:
  python3 scripts/download_clean.py
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS = os.path.join(ROOT, "scripts", "clean_jobs.json")
OUT = os.path.join(ROOT, "assets", "plans_clean")


def main():
    with open(JOBS, encoding="utf-8") as fh:
        data = json.load(fh)
    url_by_job = {j["clean_job"]: j["result_url"] for j in data["unique_clean_jobs"]}
    os.makedirs(OUT, exist_ok=True)

    ok, fail = 0, 0
    for card in data["cards"]:
        job = card["clean_job"]
        url = url_by_job.get(job)
        if not url:
            print(f"!! нет result_url для {job}", file=sys.stderr)
            fail += 1
            continue
        dst = os.path.join(OUT, card["src"])
        r = subprocess.run(
            ["curl", "-sSL", "-m", "60", "-o", dst, url],
            capture_output=True, text=True,
        )
        size = os.path.getsize(dst) if os.path.exists(dst) else 0
        if r.returncode == 0 and size > 2000:
            print(f"OK  {card['id']}  {card['src']}  ({size} б)")
            ok += 1
        else:
            print(f"FAIL {card['id']} {card['src']} size={size} {r.stderr.strip()}",
                  file=sys.stderr)
            fail += 1
    print(f"\nСкачано: {ok}, ошибок: {fail}")


if __name__ == "__main__":
    main()
