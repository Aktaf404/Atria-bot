"""
Atria-asi.ai Auto-Login via Google (GSuite)
============================================
Author: Rofi Indistira
Baca list akun dari akun.txt (format: email;password per baris), login
lewat Google OAuth di browser (Camoufox), lalu bikin API key di Atria
console dan simpan ke api.txt.

Buka beberapa window paralel (default 10), 1 sesi per window, loop sampai
semua akun diproses.

Usage:  python astra_glogin.py
        python astra_glogin.py --workers 5 --accounts akun.txt --out api.txt
"""

import asyncio
import argparse
import json
import re
import sys
import time
from pathlib import Path

import httpx
from camoufox import AsyncCamoufox

ATRIA = "https://api.atria-asi.ai"
BASE = Path(__file__).parent


# ─── helpers ──────────────────────────────────────────
def load_accounts(path: Path):
    """Parse email;password lines. Skips blanks and comments."""
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for sep in (";", ":", "|", ","):
            if sep in line:
                email, pw = line.split(sep, 1)
                out.append((email.strip(), pw.strip()))
                break
    return out


def existing_emails(path: Path):
    """Emails that already have a key saved (api.txt is used as the store,
    lines are now email;key so a key is never created twice per account)."""
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        for sep in (";", ":", "|", ","):
            if sep in line:
                out.add(line.split(sep, 1)[0].strip())
                break
    return out


def append_key(path: Path, email: str, key: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{email};{key}\n")


def append_log(path: Path, email: str, status: str, extra: str = ""):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {status:8s} {email} {extra}\n")


# ─── google login ─────────────────────────────────────
async def snapshot(p):
    """Diagnostic: current url + page text + visible buttons."""
    try:
        info = await p.evaluate("""() => {
            const btns = [...document.querySelectorAll('button')]
                .map(b => (b.innerText || '').trim()).filter(t => t).slice(0, 12);
            return {url: location.href, body: document.body.innerText.slice(0, 220), btns};
        }""")
        return info
    except Exception:
        return {"url": "?", "body": "", "btns": []}


async def google_login(p, email: str, password: str, timeout: int = 60):
    """Runs the Google OAuth flow on page p. Returns True on success."""
    try:
        await p.goto(f"{ATRIA}/sign-in", wait_until="networkidle", timeout=45000)
    except Exception:
        return False
    await asyncio.sleep(3)

    try:
        await p.click('button:has-text("Continue with Google")', timeout=15000)
    except Exception:
        return False

    deadline = time.time() + timeout
    warned = False

    # step 1: email
    while time.time() < deadline:
        await asyncio.sleep(1)
        if "accounts.google.com" not in p.url:
            break
        try:
            inp = await p.query_selector('input[name="identifier"]')
            if inp and await inp.is_visible():
                await inp.fill(email)
                await asyncio.sleep(0.4)
                await p.click('button:has-text("Next")')
                await asyncio.sleep(3)
                break
            if not warned and time.time() > deadline - 25:
                s = await snapshot(p)
                print(f"      [step1 macet] url={s['url'][:70]} body={s['body'][:80]} btn={s['btns'][:6]}")
                warned = True
        except Exception:
            pass
    else:
        return False

    # step 2: password (+ tos / consent / verify pages)
    warned = False
    while time.time() < deadline:
        await asyncio.sleep(1)
        url = p.url
        if "atria-asi.ai" in url and "accounts.google.com" not in url:
            break
        try:
            inp = await p.query_selector('input[type="password"]')
            if inp and await inp.is_visible():
                await inp.fill(password)
                await asyncio.sleep(0.4)
                await p.click('button:has-text("Next")')
                await asyncio.sleep(3)
                continue
        except Exception:
            pass

        # workspace terms of service, oauth consent, and similar gates all
        # show a single confirmation button (handle EN + ID locales)
        try:
            for label in ("I understand", "Saya mengerti", "Allow", "Izinkan",
                          "Continue", "Lanjutkan", "Accept", "Terima",
                          "Agree", "Setuju"):
                b = await p.query_selector(f'button:has-text("{label}")')
                if b and await b.is_visible():
                    await b.click()
                    await asyncio.sleep(3)
                    break
        except Exception:
            pass

        # if Google bounced us back to the email step, resubmit
        try:
            inp = await p.query_selector('input[name="identifier"]')
            if inp and await inp.is_visible():
                val = (await inp.input_value() or "").strip()
                if not val:
                    await inp.fill(email)
                    await asyncio.sleep(0.3)
                await p.click('button:has-text("Next")')
                await asyncio.sleep(3)
        except Exception:
            pass

        if not warned and time.time() > deadline - 25:
            s = await snapshot(p)
            print(f"      [step2 macet] url={s['url'][:70]} body={s['body'][:80]} btn={s['btns'][:6]}")
            warned = True

    if "accounts.google.com" in p.url:
        return False

    # land on the console
    for _ in range(30):
        if "console" in p.url:
            break
        await asyncio.sleep(2)

    return "atria" in p.url


async def create_api_key(p, timeout: int = 60):
    """Creates the default API key via the in-page API call."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = await p.evaluate("""async () => {
                const res = await fetch('/api/keys', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: 'default'})
                });
                return {status: res.status, body: await res.text()};
            }""")
        except Exception:
            await asyncio.sleep(2)
            continue

        if r.get("status") in (200, 201):
            try:
                data = json.loads(r["body"])
            except Exception:
                continue
            key = data.get("key") or data.get("apiKey") or ""
            if not key:
                m = re.search(r'"?(atr_\w+)"?', r["body"])
                if m:
                    key = m.group(1)
            if key:
                return key
        elif r.get("status") == 401:
            return None  # not logged in
        await asyncio.sleep(2)
    return None


# ─── one account ──────────────────────────────────────
async def process(account, idx, total, workers, results, lock):
    email, password = account
    tag = f"[{idx}/{total}]"
    print(f"  {tag} {email} logging in...")

    try:
        async with AsyncCamoufox(headless=True, humanize=True) as br:
            p = await br.new_page()
            await p.set_viewport_size({"width": 1280, "height": 900})

            ok = await google_login(p, email, password)
            if not ok:
                print(f"  {tag} {email} login failed")
                async with lock:
                    results.append((email, None))
                return

            await asyncio.sleep(3)
            try:
                await p.goto(f"{ATRIA}/console", wait_until="networkidle", timeout=30000)
            except Exception:
                pass
            await asyncio.sleep(2)

            key = await create_api_key(p)
            if key:
                print(f"  {tag} {email} -> {key}")
                async with lock:
                    results.append((email, key))
            else:
                print(f"  {tag} {email} no api key")
                async with lock:
                    results.append((email, None))

    except Exception as e:
        print(f"  {tag} {email} error: {type(e).__name__}: {str(e)[:100]}")
        async with lock:
            results.append((email, None))


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accounts", default=str(BASE / "akun.txt"))
    ap.add_argument("--out", default=str(BASE / "api.txt"))
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()

    accounts_path = Path(args.accounts)
    out_path = Path(args.out)

    accounts = load_accounts(accounts_path)
    if not accounts:
        print(f"  Tidak ada akun di {accounts_path}")
        print("  Format: email;password per baris")
        return

    done = existing_emails(out_path)
    todo = [a for a in accounts if a[0] not in done]
    skipped = len(accounts) - len(todo)

    print(f"\n  {len(accounts)} akun dibaca dari {accounts_path.name}")
    if skipped:
        print(f"  {skipped} sudah punya key di {out_path.name} (skip)")
    print(f"  Paralel: {args.workers} window")
    if not todo:
        # clean up akun.txt: everything already done -> success_akun.txt
        success_path = BASE / "success_akun.txt"
        with open(success_path, "a", encoding="utf-8") as f:
            for email, pw in accounts:
                f.write(f"{email}:{pw}\n")
        with open(accounts_path, "w", encoding="utf-8") as f:
            pass
        print(f"  Semua {len(accounts)} akun sudah punya key, dipindah ke {success_path.name}\n")
        return
    print("")

    acc_map = {a[0]: a for a in accounts}

    # accounts that already have a key count as success too
    success = [(a[0], a[1]) for a in accounts if a[0] in done]

    results = []
    lock = asyncio.Lock()

    # Pre-extract addons to prevent race conditions during parallel processing
    try:
        async with AsyncCamoufox(headless=True, humanize=True):
            pass
    except Exception:
        pass

    # process in batches of N parallel windows
    for i in range(0, len(todo), args.workers):
        batch = todo[i:i + args.workers]
        await asyncio.gather(*[
            process(a, i + j + 1, len(todo), args.workers, results, lock)
            for j, a in enumerate(batch)
        ])

    ok = sum(1 for _, k in results if k)
    print(f"\n  Selesai: {ok}/{len(results)} akun dapat API key\n")

    for email, key in results:
        if key:
            append_key(out_path, email, key)
            success.append(acc_map[email])
        else:
            pass
    failed = [acc_map[a] for a, k in results if not k]

    # write success / failed lists
    success_path = BASE / "success_akun.txt"
    failed_path = BASE / "failed_akun.txt"
    for email, pw in success:
        with open(success_path, "a", encoding="utf-8") as f:
            f.write(f"{email}:{pw}\n")
    for email, pw in failed:
        with open(failed_path, "a", encoding="utf-8") as f:
            f.write(f"{email}:{pw}\n")

    # remove handled accounts from akun.txt (so the file is consumed as it goes)
    moved = {a[0] for a in success} | {a[0] for a in failed}
    remaining = [a for a in accounts if a[0] not in moved]
    with open(accounts_path, "w", encoding="utf-8") as f:
        for email, pw in remaining:
            f.write(f"{email}:{pw}\n")

    print(f"  success: {len(success)}  -> {success_path.name}")
    print(f"  failed : {len(failed)}  -> {failed_path.name}")
    print(f"  sisa di {accounts_path.name}: {len(remaining)}")

    if ok:
        append_log(BASE / "glogin.log", f"{ok} keys", "saved to", out_path.name)
        print(f"  Disimpan di {out_path.name}")


if __name__ == "__main__":
    asyncio.run(main())
