from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import re
import io
import pandas as pd

from gem_automation import GemAutoSearch


app = FastAPI(title="GeM Auto Search")

templates = Jinja2Templates(directory="templates")


class SearchRequest(BaseModel):
    instruction: str


def parse_instruction(text: str):
    """Hindi/English instruction ko basic search parameters me convert karta hai."""

    t = text.lower()

    result = {
        "product": None,
        "brand": None,
        "quantity": None,
        "max_price": None,
        "ram": None,
        "storage": None,
        "processor": None,
        "keywords": text
    }

    # Quantity
    m = re.search(
        r"(\d+)\s*(?:quantity|qty|nos|pcs|pieces|units?)",
        t
    )

    if not m:
        m = re.search(
            r"(?:^|\s)(\d+)\s+(?:hp|lenovo|dell|printer|laptop|computer)",
            t
        )

    if m:
        result["quantity"] = int(m.group(1))

    # Price
    m = re.search(
        r"(?:₹|rs\.?|inr)\s*([0-9,]+)\s*(?:ke\s+andar|tak|under)?",
        t
    )

    if m:
        result["max_price"] = int(
            m.group(1).replace(",", "")
        )

    # RAM
    m = re.search(
        r"(\d+)\s*gb\s*ram",
        t
    )

    if m:
        result["ram"] = f"{m.group(1)} GB"

    # Storage
    m = re.search(
        r"(\d+)\s*(gb|tb)\s*(?:ssd|hdd|storage)",
        t
    )

    if m:
        result["storage"] = (
            f"{m.group(1)} {m.group(2).upper()}"
        )

    # Processor
    for processor in [
        "i3",
        "i5",
        "i7",
        "i9",
        "ryzen 3",
        "ryzen 5",
        "ryzen 7"
    ]:

        if processor in t:
            result["processor"] = processor.upper()
            break

    # Common products
    products = [
        "laptop",
        "desktop computer",
        "computer",
        "printer",
        "office chair",
        "chair",
        "monitor",
        "scanner",
        "ups",
        "air conditioner"
    ]

    for product in products:

        if product in t:
            result["product"] = product
            break

    # Common brands
    brands = [
        "hp",
        "lenovo",
        "dell",
        "canon",
        "epson",
        "acer",
        "asus",
        "lg"
    ]

    found_brands = [
        b.upper()
        for b in brands
        if b in t
    ]

    if found_brands:
        result["brand"] = ", ".join(found_brands)

    return result


def authorized_gem_search(criteria):
    """
    Browser automation ke through GeM search.

    CAPTCHA, OTP, login protection ya anti-bot
    mechanism ko bypass nahi karta.
    """

    search_text = criteria.get(
        "keywords",
        ""
    ).strip()

    if not search_text:
        return []

    bot = GemAutoSearch(
        headless=False
    )

    try:

        bot.start()

        result = bot.search(
            search_text
        )

        return [result]

    except Exception as e:

        return [{
            "status": "error",
            "message": str(e)
        }]

    finally:

        bot.close()


@app.get(
    "/",
    response_class=HTMLResponse
)
async def home(request: Request):

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


@app.post("/parse")
async def parse(req: SearchRequest):

    criteria = parse_instruction(
        req.instruction
    )

    results = authorized_gem_search(
        criteria
    )

    return {
        "criteria": criteria,
        "results": results
    }


@app.post("/excel")
async def excel(req: SearchRequest):

    criteria = parse_instruction(
        req.instruction
    )

    results = authorized_gem_search(
        criteria
    )

    if not results:

        results = [{
            "Status": "No results",
            "Product": criteria["product"] or "",
            "Brand": criteria["brand"] or "",
            "Quantity": criteria["quantity"] or "",
            "Max Price": criteria["max_price"] or "",
            "RAM": criteria["ram"] or "",
            "Storage": criteria["storage"] or "",
            "Processor": criteria["processor"] or ""
        }]

    df = pd.DataFrame(
        results
    )

    output = io.BytesIO()

    df.to_excel(
        output,
        index=False
    )

    output.seek(0)

    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition":
            "attachment; filename=gem_search.xlsx"
        }
    )
