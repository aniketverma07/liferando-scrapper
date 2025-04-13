from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime

# Create FastAPI app
app = FastAPI(title="Simple Test API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the input model
class ScrapeInput(BaseModel):
    lieferando_url: str
    restaurant_name: str

@app.get("/")
async def root():
    """Root endpoint to check if the API is running"""
    return {
        "status": "ok", 
        "message": "Simple Test API is running",
        "timestamp": str(datetime.datetime.now())
    }

@app.post("/scrape")
async def scrape(input: ScrapeInput):
    """Simple test endpoint that returns mock data without using Playwright"""
    try:
        # Just return mock data for testing
        return {
            "restaurant_name": input.restaurant_name,
            "menu": [
                {"name": "Test Item 1", "price": 9.99},
                {"name": "Test Item 2", "price": 12.99},
                {"name": "Test Item 3", "price": 7.50}
            ],
            "url": input.lieferando_url,
            "item_count": 3,
            "timestamp": str(datetime.datetime.now())
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": str(datetime.datetime.now())
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
