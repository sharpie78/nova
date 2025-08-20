# ===============================
# webfox/app.py  (FastAPI microservice wrapping Selenium+Firefox)
# ===============================
from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from readability import Document
from urllib.parse import urlparse
import os, time, base64

SHOTS_DIR = os.environ.get("SHOTS_DIR", "/shots")
PAGE_TIMEOUT = int(os.environ.get("PAGE_TIMEOUT", "12"))
HEADLESS = os.environ.get("HEADLESS", "1") == "1"

os.makedirs(SHOTS_DIR, exist_ok=True)

app = FastAPI()

class BrowseReq(BaseModel):
    url: str
    screenshot: bool = True
    user_agent: str | None = None
    lang: str = "en-GB"

@app.post("/browse")
def browse(req: BrowseReq):
    opts = Options()
    if HEADLESS:
        opts.add_argument("-headless")
    # Privacy-ish defaults
    ua = req.user_agent or "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0"
    opts.set_preference("general.useragent.override", ua)
    opts.set_preference("intl.accept_languages", req.lang)
    opts.set_preference("browser.download.dir", "/dev/null")
    opts.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")
    opts.set_preference("permissions.default.image", 2)  # block images to speed up
    opts.set_preference("dom.ipc.processCount", 1)

    driver = webdriver.Firefox(options=opts)
    driver.set_page_load_timeout(PAGE_TIMEOUT)

    title = ""
    text = ""
    shot_path = None
    try:
        driver.get(req.url)
        try:
            WebDriverWait(driver, PAGE_TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception:
            pass
        html = driver.page_source
        title = driver.title or ""
        try:
            doc = Document(html)
            text = doc.summary(html_partial=False)
        except Exception:
            text = html
        # crude text strip
        import re
        text = re.sub(r"<[^>]+>", " ", text)
        text = " ".join(text.split())

        if req.screenshot:
            fname = f"shot_{int(time.time()*1000)}.png"
            full = os.path.join(SHOTS_DIR, fname)
            driver.save_screenshot(full)
            shot_path = full
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return {"title": title, "text": text[:4000], "screenshot": shot_path, "url": req.url}
