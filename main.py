from fastapi import FastAPI
from pydantic import BaseModel
from playwright.async_api import async_playwright

app = FastAPI()

# Define the input model for scraping
class ScrapeInput(BaseModel):
    lieferando_url: str
    restaurant_name: str

@app.post("/scrape")
async def scrape(input: ScrapeInput):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(input.lieferando_url)

        # Scrape restaurant name (example)
        name = await page.text_content('h1.restaurant-name')

        # Scrape menu items (example)
        menu_items = await page.query_selector_all('.menu-item')

        items = []
        for item in menu_items:
            title = await item.text_content('.item-name')
            price = await item.text_content('.item-price')
            items.append({
                "name": title.strip(),
                "price": float(price.replace("€", "").strip())
            })

        await browser.close()

    return {
        "restaurant_name": name.strip(),
        "menu": items
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
