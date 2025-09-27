from pymongo import MongoClient
from datetime import datetime
import os

# Подключение к MongoDB
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://mongo:27017/'))
db = client['quotes_db']
collection = db['quotes']

def save_quote(author: str, quote: str, tags: list[str]):
    doc = {
        'author': author,
        'quote': quote,
        'tags': tags,
        'added_date': datetime.now()
    }
    result = collection.insert_one(doc)
    return result.inserted_id

def get_quotes(author: str = None, tag: str = None):
    query = {}
    if author:
        query['author'] = {'$regex': author, '$options': 'i'}  # Case-insensitive search
    if tag:
        query['tags'] = tag
    quotes = list(collection.find(query))
    return quotes