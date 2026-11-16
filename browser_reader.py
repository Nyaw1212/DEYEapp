"""Browser-assisted local Deye status reader.

Install: py -m pip install playwright
         py -m playwright install chromium
Run:     py browser_reader.py --ip 192.168.1.93

Log in manually in the opened browser window. No password is saved in code.
The Chromium profile stays on this PC under .deye_browser_profile.
"""
import argparse
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="192.168.1.93")
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    profile = str(Path(__file__).resolve().parent / ".deye_browser_profile")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            profile, headless=False, ignore_https_errors=False
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(f"http://{args.ip}/index.html", wait_until="domcontentloaded")
        print("Log in using the opened browser, then press Enter here.")
        input()
        try:
            while True:
                try:
                    result = page.evaluate("""() => new Promise((resolve, reject) => {
                      if (typeof request !== 'function' || typeof handleResText !== 'function') {
                        reject(new Error('Logger request functions unavailable. Open Device Status and retry.'));
                        return;
                      }
                      const timeout = setTimeout(() => reject(new Error('Logger request timed out')), 10000);
                      request({
                        url: 'status.cgi?t=' + Math.random(),
                        retryCount: 0,
                        keyResyncRetryCount: 0,
                        successCb: (response) => {
                          clearTimeout(timeout);
                          try {
                            const obj = handleResText(response);
                            resolve({
                              timestamp: obj.inverter?.time ?? null,
                              measurements: Object.fromEntries((obj.inverter?.info || []).map(x => [x.key, x.value]))
                            });
                          } catch (e) { reject(e); }
                        },
                        failedCb: () => { clearTimeout(timeout); reject(new Error('Logger request failed')); }
                      });
                    })""")
                    print(json.dumps(result, ensure_ascii=False), flush=True)
                except Exception as exc:
                    print(f"Read failed: {exc}", flush=True)
                time.sleep(max(1, args.interval))
        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            context.close()

if __name__ == "__main__":
    main()
