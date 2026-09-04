from playwright.sync_api import sync_playwright


class GemAutoSearch:

    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=self.headless
        )

        self.page = self.browser.new_page()

        self.page.goto(
            "https://gem.gov.in/",
            wait_until="domcontentloaded",
            timeout=60000
        )

    def search(self, search_text):

        if not self.page:
            self.start()

        search_box = self.page.locator(
            'input[type="search"], input[placeholder*="Search"], input[name="search"]'
        ).first

        search_box.wait_for(
            state="visible",
            timeout=15000
        )

        search_box.fill(search_text)
        search_box.press("Enter")

        self.page.wait_for_load_state(
            "domcontentloaded",
            timeout=60000
        )

        return {
            "url": self.page.url,
            "title": self.page.title(),
            "text": self.page.locator("body").inner_text()
        }

    def close(self):

        if self.browser:
            self.browser.close()

        if self.playwright:
            self.playwright.stop()
