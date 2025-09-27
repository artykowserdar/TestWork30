## Project Setup

This project is a FastAPI service that scrapes quotes from https://quotes.toscrape.com/, saves them to MongoDB using Celery, and provides an API to retrieve them.

### Prerequisites
- Docker and Docker Compose installed.

### Build and Run
1. Clone the repository.
2. Run `docker-compose up --build` in the project root.
3. The FastAPI app will be available at http://localhost:8000.
   - POST /parse-quotes-task: Starts scraping task, returns task_id.
   - GET /quotes?author=AuthorName&tag=TagName: Retrieves quotes, filtered if params provided. Returns message if no results.

Note: Celery worker runs separately to handle tasks asynchronously.