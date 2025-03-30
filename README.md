# SQL Query Generator with Natural Language

An AI-powered tool that converts natural language queries into SQL commands and generates visual reports.

## Features

- Natural language to SQL query conversion
- Interactive data visualization
- Support for complex queries including aggregations and joins
- User-friendly chat interface
- Real-time query execution and results display

## Tech Stack

- Backend: FastAPI (Python)
- Frontend: HTML, CSS, JavaScript
- AI: Transformers (Hugging Face)
- Database: SQLite
- Visualization: Plotly

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Open your browser and navigate to `http://localhost:8000`

## Project Structure

```
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── models/              # Database models
│   ├── routers/             # API routes
│   ├── services/            # Business logic
│   └── static/              # Static files (CSS, JS)
├── templates/               # HTML templates
├── data/                    # Sample database and data
└── requirements.txt         # Project dependencies
```

## Usage

1. Enter your natural language query in the chat interface
2. The system will generate and execute the corresponding SQL query
3. Results will be displayed in both tabular and visual formats
4. You can modify the query or ask follow-up questions

## Contributing

Feel free to submit issues and enhancement requests! 