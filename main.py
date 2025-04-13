from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.async_api import async_playwright
import logging
import traceback
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lieferando Scraper API", 
              description="API for scraping restaurant data from Lieferando",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the input model for scraping
class ScrapeInput(BaseModel):
    lieferando_url: str
    restaurant_name: str

@app.get("/")
async def root():
    return {"status": "ok", "message": "Lieferando Scraper API is running"}

@app.post("/scrape")
async def scrape(input: ScrapeInput):
    try:
        logger.info(f"Starting scrape for URL: {input.lieferando_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            
            # Set timeout for navigation
            page.set_default_timeout(60000)  # 60 seconds
            
            logger.info(f"Navigating to {input.lieferando_url}")
            response = await page.goto(input.lieferando_url, wait_until="networkidle")
            
            if not response or response.status >= 400:
                status_code = response.status if response else 404
                await browser.close()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to load the page. Status code: {status_code}"
                )
            
            # Wait for content to load
            await page.wait_for_load_state("domcontentloaded")
            
            # Try different selectors for restaurant name
            name = None
            name_selectors = ['h1.restaurant-name', 'h1[data-test="restaurant-header-name"]', '.restaurant-name', '.restaurant-title']
            
            for selector in name_selectors:
                try:
                    if await page.query_selector(selector):
                        name = await page.text_content(selector)
                        if name:
                            logger.info(f"Found restaurant name with selector: {selector}")
                            break
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {str(e)}")
            
            # If we couldn't find the name, use the provided one
            if not name:
                logger.warning("Could not find restaurant name, using provided name")
                name = input.restaurant_name
            
            # Try different selectors for menu items
            menu_selectors = ['.menu-item', '.dish-card', '.foodItem', '.meal-item']
            menu_items = []
            
            for selector in menu_selectors:
                try:
                    items = await page.query_selector_all(selector)
                    if items and len(items) > 0:
                        logger.info(f"Found {len(items)} menu items with selector: {selector}")
                        menu_items = items
                        break
                except Exception as e:
                    logger.warning(f"Error with menu selector {selector}: {str(e)}")
            
            # Take a screenshot for debugging
            await page.screenshot(path="screenshot.png")
            
            items = []
            for item in menu_items:
                try:
                    # Try different selectors for item name and price
                    name_selectors = ['.item-name', '.dish-name', '.meal-name', '.name', 'h3']
                    price_selectors = ['.item-price', '.dish-price', '.meal-price', '.price']
                    
                    title = None
                    price_text = None
                    
                    # Try to get the title
                    for selector in name_selectors:
                        try:
                            name_element = await item.query_selector(selector)
                            if name_element:
                                title = await name_element.text_content()
                                if title:
                                    break
                        except:
                            continue
                    
                    # Try to get the price
                    for selector in price_selectors:
                        try:
                            price_element = await item.query_selector(selector)
                            if price_element:
                                price_text = await price_element.text_content()
                                if price_text:
                                    break
                        except:
                            continue
                    
                    # If we found both title and price
                    if title and price_text:
                        # Clean up the title and price
                        title = title.strip()
                        
                        # Extract price using regex to find numbers with decimal points
                        price_match = re.search(r'\d+[.,]\d+', price_text)
                        if price_match:
                            price_str = price_match.group(0).replace(',', '.')
                            try:
                                price = float(price_str)
                                items.append({
                                    "name": title,
                                    "price": price
                                })
                            except ValueError:
                                logger.warning(f"Could not convert price: {price_str}")
                except Exception as e:
                    logger.warning(f"Error processing menu item: {str(e)}")
            
            await browser.close()
            
            logger.info(f"Scraping completed. Found {len(items)} menu items.")
            
            return {
                "restaurant_name": name.strip() if name else input.restaurant_name,
                "menu": items,
                "url": input.lieferando_url,
                "item_count": len(items)
            }
    
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during scraping: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
