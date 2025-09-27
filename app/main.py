import logging
import os

from celery import Celery
from fastapi import FastAPI, Query
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client.quotes_db
quotes_collection = db.quotes

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
celery_app = Celery("tasks", broker=CELERY_BROKER_URL)

@celery_app.task
def parse_quotes():
    import requests
    from bs4 import BeautifulSoup
    from datetime import datetime

    quotes = []
    url = "https://quotes.toscrape.com/page/1/"
    while url:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        for quote_div in soup.select(".quote"):
            quote_text = quote_div.select_one(".text").text.strip()
            author = quote_div.select_one(".author").text.strip()
            tags = [tag.text.strip() for tag in quote_div.select(".tag")]
            quotes.append({
                "author": author,
                "quote": quote_text,
                "tags": tags,
                "added_date": datetime.now()
            })
        next_link = soup.select_one("li.next a")
        url = "https://quotes.toscrape.com" + next_link["href"] if next_link else None

    # Save to MongoDB synchronously
    client = MongoClient(MONGO_URI)
    db = client.quotes_db
    quotes_collection = db.quotes
    for quote in quotes:
        logger.info(f"Saving quote: {quote['quote'][:50]}... by {quote['author']}")
        quotes_collection.insert_one(quote)
    client.close()
    return len(quotes)

class TaskResponse(BaseModel):
    task_id: str

@app.post("/parse-quotes-task", response_model=TaskResponse)
async def parse_quotes_task():
    task = parse_quotes.delay()
    return {"task_id": task.id}

@app.get("/quotes")
async def get_quotes(author: str = Query(None), tag: str = Query(None)):
    query = {}
    if author:
        query["author"] = author
    if tag:
        query["tags"] = tag
    cursor = quotes_collection.find(query)
    results = await cursor.to_list(length=None)
    if not results:
        return {"message": "No quotes found for the given criteria."}
    # Convert ObjectId to string for JSON serialization
    serialized_results = [
        {**doc, "_id": str(doc["_id"])} for doc in results
    ]
    return serialized_results