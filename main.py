from gem_automation import GemAutoSearch


def automatic_product_search(search_text, headless=False):
    """
    GeM par product search karta hai aur
    lowest detected price return karta hai.
    """

    gem = GemAutoSearch(headless=headless)

    try:
        result = gem.search_lowest_price(search_text)
        return result
    finally:
        gem.close()


if __name__ == "__main__":
    query = input("Product search likhiye: ").strip()

    if not query:
        print("Search query khali nahi ho sakti.")
    else:
        result = automatic_product_search(query)

        print("\n--- GeM Search Result ---")
        print("Query:", result["query"])
        print("Title:", result["title"])
        print("URL:", result["url"])

        lowest = result.get("lowest_price")

        print("\n--- Lowest Price ---")

        if lowest:
            print(
                f"Lowest Price: ₹{lowest['price']:,.2f}"
            )
            print(
                "Price Text:",
                lowest["raw"]
            )
        else:
            print("Lowest price nahi mila.")

        print("\n--- All Detected Prices ---")

        prices = result.get("prices", [])

        if prices:
            for item in prices:
                print(
                    f"₹{item['price']:,.2f} | "
                    f"{item['raw']}"
                )
        else:
            print("Koi price detect nahi hua.")
