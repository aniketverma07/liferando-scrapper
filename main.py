from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from playwright.async_api import async_playwright
import logging
import traceback
import re
import datetime

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

@app.get("/test")
async def test():
    """Simple test endpoint to verify the API is working correctly"""
    return {
        "status": "ok",
        "message": "Test endpoint is working",
        "timestamp": str(datetime.datetime.now())
    }

@app.post("/scrape")
async def scrape(input: ScrapeInput):
    try:
        logger.info(f"Starting scrape for URL: {input.lieferando_url}")
        
        # First, return a simple response to test if basic functionality works
        # Comment this out after testing
        # return {
        #     "restaurant_name": input.restaurant_name,
        #     "menu": [{"name": "Test item", "price": 9.99}],
        #     "url": input.lieferando_url,
        #     "item_count": 1,
        #     "debug": "Simple test response"
        # }
        
        async with async_playwright() as p:
            # Log browser launch attempt
            logger.info("Attempting to launch browser")
            browser = await p.chromium.launch(headless=True)
            logger.info("Browser launched successfully")
            
            # Create a browser context with a custom user agent
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            
            # Set timeout for navigation
            page.set_default_timeout(30000)  # 30 seconds
            
            try:
                logger.info(f"Navigating to {input.lieferando_url}")
                response = await page.goto(input.lieferando_url, wait_until="domcontentloaded")
                
                if not response:
                    logger.error("No response received from page")
                    await browser.close()
                    return {
                        "restaurant_name": input.restaurant_name,
                        "menu": [],
                        "url": input.lieferando_url,
                        "item_count": 0,
                        "error": "No response received from page"
                    }
                
                logger.info(f"Page loaded with status: {response.status}")
                
                # Wait a moment for JavaScript to execute
                await page.wait_for_timeout(2000)
                
                # Get page title for debugging
                title = await page.title()
                logger.info(f"Page title: {title}")
                
                # Get page content for debugging
                content = await page.content()
                content_preview = content[:200] + "..." if len(content) > 200 else content
                logger.info(f"Page content preview: {content_preview}")
                
                # Simple approach: just get the restaurant name from the title
                name = title.split("|")
                restaurant_name = name[0].strip() if len(name) > 0 else input.restaurant_name
                
                # For now, return a simplified response with debugging info
                debug_info = {
                    "page_title": title,
                    "content_preview": content_preview,
                    "response_status": response.status,
                    "url": input.lieferando_url
                }
                
                await browser.close()
                
                return {
                    "restaurant_name": restaurant_name,
                    "menu": [{"name": "Sample item", "price": 9.99}],  # Placeholder
                    "url": input.lieferando_url,
                    "item_count": 1,
                    "debug": debug_info
                }
                
            except Exception as e:
                logger.error(f"Error during page navigation: {str(e)}")
                await browser.close()
                return {
                    "restaurant_name": input.restaurant_name,
                    "menu": [],
                    "url": input.lieferando_url,
                    "item_count": 0,
                    "error": f"Navigation error: {str(e)}"
                }
    
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Instead of raising an exception, return an error response
        return {
            "restaurant_name": input.restaurant_name,
            "menu": [],
            "url": input.lieferando_url if hasattr(input, 'lieferando_url') else "unknown",
            "item_count": 0,
            "error": f"Scraping error: {str(e)}",
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
