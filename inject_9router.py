"""Inject API keys to 9Router + test (author: Rofi Indistira)."""
import json
import sys
import time
from pathlib import Path

import httpx

BASE = Path(__file__).parent
API = "http://localhost:20128"
PROVIDER = "openai-compatible-responses-06f3de3d-a8d0-41bd-a1a0-b1617e8b9f78"
MODEL = "Atria-Dawn-Preview"

PSD = {
    "prefix": "at",
    "apiType": "responses",
    "baseUrl": "http://api.atria-asi.ai/v1",
    "nodeName": "Atria",
    "connectionProxyEnabled": False,
    "connectionProxyUrl": "",
    "connectionNoProxy": "",
}


def load_pairs(path: Path):
    """Read email;key lines from api.txt."""
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        for sep in (";", ":", "|", ","):
            if sep in line:
                email, key = line.split(sep, 1)
                out.append((email.strip(), key.strip()))
                break
    return out


def main():
    pairs = load_pairs(BASE / "api.txt")
    if not pairs:
        print("api.txt kosong (format: email;key per baris)")
        return

    with httpx.Client(base_url=API, timeout=30) as c:
        cur = c.get("/api/providers").json().get("connections", [])
        mine = [x for x in cur if x.get("provider") == PROVIDER]
        mine_names = {x.get("name") for x in mine}
        print(f"koneksi {PROVIDER} sekarang: {len(mine)}")

        # add only the ones not connected yet
        new = 0
        for email, key in pairs:
            if email in mine_names:
                print(f"  lewati {email} (sudah ada)")
                continue
            body = {
                "provider": PROVIDER,
                "apiKey": key,
                "name": email,
                "priority": 1,
                "testStatus": "unknown",
                "defaultModel": MODEL,
                "providerSpecificData": PSD,
            }
            r = c.post("/api/providers", json=body)
            ok = r.status_code in (200, 201)
            print(f"  ADD {email}: {r.status_code} {'OK' if ok else r.text[:160]}")
            if ok:
                new += 1
            time.sleep(0.3)
        print(f"ditambahkan: {new}")

        # test every connection of this provider
        cur2 = c.get("/api/providers").json().get("connections", [])
        mine2 = [x for x in cur2 if x.get("provider") == PROVIDER]
        ok = fail = 0
        for x in mine2:
            r = c.post(f"/api/providers/{x['id']}/test", timeout=90)
            try:
                data = r.json()
            except Exception:
                data = {"_raw": r.text[:160]}
            valid = bool(data.get("valid"))
            if valid:
                ok += 1
            else:
                fail += 1
            print(f"  TEST {x['name']}: model={x.get('defaultModel')} valid={valid} {json.dumps(data)[:110]}")
        print(f"\nselesai: {len(mine2)} koneksi, {ok} ok, {fail} fail")


if __name__ == "__main__":
    main()