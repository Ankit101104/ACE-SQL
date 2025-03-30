from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from app.services.query_generator import QueryGenerator
from app.models.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

router = APIRouter()
query_generator = QueryGenerator()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    sql_query: str
    explanation: str
    results: List[Dict[str, Any]]

@router.post("/generate", response_model=QueryResponse)
async def generate_query(request: QueryRequest, db: Session = Depends(get_db)):
    try:
        # Generate SQL query
        sql_query = query_generator.generate_sql(request.query)
        
        # Get explanation
        explanation = query_generator.explain_query(sql_query)
        
        # Execute query and get results
        # Note: In a production environment, you should implement proper SQL injection protection
        result = db.execute(text(sql_query))
        columns = result.keys()
        rows = result.fetchall()
        
        # Convert results to dictionary format
        results = [dict(zip(columns, row)) for row in rows]
        
        return QueryResponse(
            sql_query=sql_query,
            explanation=explanation,
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy"} 