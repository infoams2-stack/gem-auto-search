from playwright.sync_api import sync_playwright


class GemAutoSearch:
    """
    GeM product search automation module.

    Note:
    This module does not bypass CAPTCHA, OTP, login protection,
    or any other anti-bot/security mechanism.
    """

    BASE_URL = "https://gem.gov.in/"

    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        """Start browser and open GeM."""
        if self.page:
            return

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=self.headless
        )

        self.page = self.browser.new_page()

        self.page.goto(
            self.BASE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

    def search(self, search_text):
        """
        Automatically search GeM for the supplied product text.
        """

        if not search_text or not search_text.strip():
            raise ValueError("search_text cannot be empty")

        if not self.page:
            self.start()

        search_box = self.page.locator(
            'input[type="search"], '
            'input[placeholder*="Search"], '
            'input[name="search"]'
        ).first

        search_box.wait_for(
            state="visible",
            timeout=15000
        )

        search_box.fill(search_text.strip())
        search_box.press("Enter")

        self.page.wait_for_load_state(
            "domcontentloaded",
            timeout=60000
        )

        return {
            "query": search_text.strip(),
            "url": self.page.url,
            "title": self.page.title(),
            "text": self.page.locator("body").inner_text()
        }

    def close(self):
        """Close browser and Playwright."""
        if self.browser:
            self.browser.close()
            self.browser = None

        if self.playwright:
            self.playwright.stop()
            self.playwright = None

        self.page = None

