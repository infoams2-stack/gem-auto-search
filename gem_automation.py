from playwright.sync_api import sync_playwright
import re


class GemAutoSearch:
    """
    GeM product search automation module.

    Features:
    - GeM product search
    - Visible price extraction
    - Lowest detected price selection

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
        Search GeM for the supplied product text.
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

    # ==================================================
    # PRICE PARSER
    # ==================================================

    @staticmethod
    def parse_price(value):
        """
        Convert GeM price text into a number.

        Examples:
            ₹48,999       -> 48999.0
            Rs. 48,999    -> 48999.0
            INR 48,999    -> 48999.0
        """

        if not value:
            return None

        value = str(value).strip()

        match = re.search(
            r'(?:₹|Rs\.?|INR)\s*'
            r'([\d,]+(?:\.\d{1,2})?)',
            value,
            re.IGNORECASE
        )

        if not match:
            return None

        try:
            return float(
                match.group(1).replace(",", "")
            )
        except ValueError:
            return None

    # ==================================================
    # EXTRACT PRICES
    # ==================================================

    def extract_prices(self):
        """
        Extract visible price values from the current page.

        Returns:
            [
                {
                    "price": 48999.0,
                    "raw": "₹48,999"
                }
            ]
        """

        if not self.page:
            raise RuntimeError(
                "Browser is not started. Call search() first."
            )

        prices = []
        seen = set()

        # Common price-related selectors.
        selectors = [
            '[class*="price" i]',
            '[class*="amount" i]',
            '[class*="cost" i]',
            '[class*="rate" i]',
            '[class*="selling" i]'
        ]

        for selector in selectors:

            try:
                elements = self.page.locator(
                    selector
                ).all()
            except Exception:
                continue

            for element in elements:

                try:
                    text = element.inner_text().strip()
                except Exception:
                    continue

                price = self.parse_price(text)

                if price is None:
                    continue

                key = (price, text)

                if key in seen:
                    continue

                seen.add(key)

                prices.append({
                    "price": price,
                    "raw": text
                })

        # ==================================================
        # FALLBACK: SEARCH COMPLETE PAGE TEXT
        # ==================================================

        if not prices:

            try:
                body_text = self.page.locator(
                    "body"
                ).inner_text()
            except Exception:
                body_text = ""

            matches = re.findall(
                r'(?:₹|Rs\.?|INR)\s*'
                r'[\d,]+(?:\.\d{1,2})?',
                body_text,
                re.IGNORECASE
            )

            for value in matches:

                price = self.parse_price(value)

                if price is None:
                    continue

                key = (price, value)

                if key in seen:
                    continue

                seen.add(key)

                prices.append({
                    "price": price,
                    "raw": value
                })

        # Lowest price first.
        prices.sort(
            key=lambda item: item["price"]
        )

        return prices

    # ==================================================
    # LOWEST PRICE
    # ==================================================

    def get_lowest_price(self):
        """
        Return the lowest detected price.

        Returns:
            {
                "price": 48999.0,
                "raw": "₹48,999"
            }

        or None.
        """

        prices = self.extract_prices()

        if not prices:
            return None

        return prices[0]

    # ==================================================
    # SEARCH + LOWEST PRICE
    # ==================================================

    def search_lowest_price(self, search_text):
        """
        Search GeM and return lowest detected price.
        """

        result = self.search(search_text)

        prices = self.extract_prices()

        result["prices"] = prices

        if prices:
            result["lowest_price"] = prices[0]
        else:
            result["lowest_price"] = None

        return result

    # ==================================================
    # CLOSE
    # ==================================================

    def close(self):
        """Close browser and Playwright."""

        if self.browser:
            self.browser.close()
            self.browser = None

        if self.playwright:
            self.playwright.stop()
            self.playwright = None

        self.page = None
