from gem_automation import GemAutoSearch


def automatic_product_search(search_text, headless=False):
    """
    GeM पर दिए गए product text का automatic search करता है।
    """

    gem = GemAutoSearch(headless=headless)

    try:
        result = gem.search(search_text)
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
        print("\nSearch Page Text:\n")
        print(result["text"])
