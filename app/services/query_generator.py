import re
from typing import Dict, Any, List, Tuple
import logging
from datetime import datetime, timedelta
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryGenerator:
    def __init__(self):
        logger.info("Initializing QueryGenerator")
        
        # Initialize OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Define schema for AI context
        self.schema_definition = """
        Available tables and their relationships:
        
        1. sales
           - id: unique sale identifier
           - date: date of sale
           - product_id: foreign key to products.id
           - customer_id: foreign key to customers.id
           - quantity: number of units sold
           - total_amount: total sale amount
        
        2. products
           - id: unique product identifier
           - name: product name
           - category: product category
           - price: unit price
           - stock: current stock level
        
        3. customers
           - id: unique customer identifier
           - name: customer name
           - email: customer email
           - region: customer's region
        
        Relationships:
        - sales.product_id references products.id
        - sales.customer_id references customers.id
        """
        
        # Define available tables and their columns
        self.schema = {
            'sales': {
                'columns': ['id', 'date', 'product_id', 'customer_id', 'quantity', 'total_amount'],
                'table_alias': 's',
                'description': 'sales transactions'
            },
            'products': {
                'columns': ['id', 'name', 'category', 'price', 'stock'],
                'table_alias': 'p',
                'description': 'product information'
            },
            'customers': {
                'columns': ['id', 'name', 'email', 'region'],
                'table_alias': 'c',
                'description': 'customer information'
            }
        }
        
        # Define common business metrics
        self.metrics = {
            'sales': {'field': 's.total_amount', 'agg': 'SUM', 'description': 'total sales amount'},
            'revenue': {'field': 's.total_amount', 'agg': 'SUM', 'description': 'total revenue'},
            'quantity': {'field': 's.quantity', 'agg': 'SUM', 'description': 'total units sold'},
            'average_sale': {'field': 's.total_amount', 'agg': 'AVG', 'description': 'average sale amount'},
            'customer_count': {'field': 'c.id', 'agg': 'COUNT DISTINCT', 'description': 'number of unique customers'},
            'order_count': {'field': 's.id', 'agg': 'COUNT', 'description': 'number of orders'}
        }
        
        # Define common aggregation functions
        self.aggregations = {
            'total': 'SUM',
            'average': 'AVG',
            'count': 'COUNT',
            'minimum': 'MIN',
            'maximum': 'MAX',
            'sum': 'SUM',
            'avg': 'AVG',
            'min': 'MIN',
            'max': 'MAX'
        }
        
        # Define time-related keywords
        self.time_patterns = {
            'today': "date(s.date) = date('now')",
            'yesterday': "date(s.date) = date('now', '-1 day')",
            'this week': "strftime('%Y-%W', s.date) = strftime('%Y-%W', 'now')",
            'last week': "strftime('%Y-%W', s.date) = strftime('%Y-%W', 'now', '-7 days')",
            'this month': "strftime('%Y-%m', s.date) = strftime('%Y-%m', 'now')",
            'last month': "strftime('%Y-%m', s.date) = strftime('%Y-%m', 'now', '-1 month')",
            'this year': "strftime('%Y', s.date) = strftime('%Y', 'now')",
            'last year': "strftime('%Y', s.date) = strftime('%Y', 'now', '-1 year')"
        }
        
        # Define comparison operators
        self.comparisons = {
            'greater than': '>',
            'more than': '>',
            'higher than': '>',
            'less than': '<',
            'lower than': '<',
            'equal to': '=',
            'equals': '=',
            'not equal to': '!=',
            'at least': '>=',
            'greater than or equal to': '>=',
            'at most': '<=',
            'less than or equal to': '<='
        }
        
        # Define sorting keywords
        self.sort_patterns = {
            'ascending': 'ASC',
            'descending': 'DESC',
            'increasing': 'ASC',
            'decreasing': 'DESC',
            'highest': 'DESC',
            'lowest': 'ASC',
            'most': 'DESC',
            'least': 'ASC'
        }
        
        # Define field mappings
        self.field_mappings = {
            'sales': 's.total_amount',
            'revenue': 's.total_amount',
            'amount': 's.total_amount',
            'quantity': 's.quantity',
            'units': 's.quantity',
            'price': 'p.price',
            'stock': 'p.stock',
            'region': 'c.region',
            'customer': 'c.name',
            'product': 'p.name',
            'category': 'p.category',
            'date': 's.date'
        }

    def _validate_query(self, query: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate if the query can be answered with available data
        Returns: (is_valid, suggestion, extracted_components)
        """
        query_lower = query.lower()
        invalid_terms = []
        suggestions = []
        
        # Check for unavailable metrics
        unavailable_metrics = [
            ('profit', 'We don\'t have profit data, but you can query sales or revenue'),
            ('tax', 'Tax information is not available, but you can query total sales'),
            ('discount', 'Discount data is not available, but you can query sales amounts'),
            ('returns', 'Return data is not available, but you can query sales'),
            ('shipping', 'Shipping data is not available'),
            ('cost', 'Cost data is not available, but you can query sales price'),
        ]
        
        for term, suggestion in unavailable_metrics:
            if term in query_lower:
                invalid_terms.append(term)
                suggestions.append(suggestion)
        
        # Check for unavailable dimensions
        unavailable_dimensions = [
            ('country', 'Country data is not available, but you can query by region'),
            ('city', 'City data is not available, but you can query by region'),
            ('state', 'State data is not available, but you can query by region'),
            ('age', 'Customer age data is not available'),
            ('gender', 'Customer gender data is not available'),
        ]
        
        for term, suggestion in unavailable_dimensions:
            if term in query_lower:
                invalid_terms.append(term)
                suggestions.append(suggestion)
        
        # If invalid terms found, generate alternative query suggestion
        if invalid_terms:
            alternative_query = query_lower
            for term, suggestion in zip(invalid_terms, suggestions):
                alternative_query = alternative_query.replace(term, self._get_alternative_term(term))
            
            return False, f"Cannot process query with {', '.join(invalid_terms)}. {' '.join(suggestions)}. Try: '{alternative_query}'", {}
        
        # Extract valid components
        components = {
            'metric': self._extract_metric(query_lower),
            'dimension': self._extract_dimension(query_lower),
            'time_period': self._extract_time_condition(query_lower),
            'filters': self._extract_comparison(query_lower),
            'grouping': self._extract_grouping(query_lower),
            'sorting': self._extract_sorting(query_lower),
            'limit': self._extract_limit(query_lower)
        }
        
        return True, "", components

    def _get_alternative_term(self, invalid_term: str) -> str:
        """Get alternative term for invalid query components"""
        alternatives = {
            'profit': 'revenue',
            'tax': 'total sales',
            'discount': 'sales',
            'returns': 'sales',
            'shipping': 'sales',
            'cost': 'price',
            'country': 'region',
            'city': 'region',
            'state': 'region',
            'age': 'customer',
            'gender': 'customer'
        }
        return alternatives.get(invalid_term, 'sales')

    def _extract_metric(self, query: str) -> Dict[str, Any]:
        """Extract the main metric from the query"""
        for metric_name, metric_info in self.metrics.items():
            if metric_name in query:
                return metric_info
        return self.metrics['sales']  # default to sales metric

    def _extract_dimension(self, query: str) -> List[str]:
        """Extract relevant dimensions from the query"""
        dimensions = []
        dimension_keywords = {
            'region': ('c.region', 'customers c'),
            'product': ('p.name', 'products p'),
            'category': ('p.category', 'products p'),
            'customer': ('c.name', 'customers c'),
            'date': ('s.date', None)
        }
        
        for keyword, (field, table) in dimension_keywords.items():
            if keyword in query:
                dimensions.append({'field': field, 'join': table})
        
        return dimensions

    def _extract_aggregation(self, query: str) -> str:
        """Extract aggregation function from query"""
        query_lower = query.lower()
        for agg_key, agg_func in self.aggregations.items():
            if agg_key in query_lower:
                return agg_func
        return 'SUM'  # default aggregation

    def _extract_time_condition(self, query: str) -> str:
        """Extract time-related conditions"""
        query_lower = query.lower()
        conditions = []
        
        for time_key, time_condition in self.time_patterns.items():
            if time_key in query_lower:
                conditions.append(time_condition)
                
        # Handle custom date ranges
        date_range_pattern = r'between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})'
        date_range_match = re.search(date_range_pattern, query_lower)
        if date_range_match:
            start_date, end_date = date_range_match.groups()
            conditions.append(f"s.date BETWEEN '{start_date}' AND '{end_date}'")
            
        return ' AND '.join(conditions) if conditions else ''

    def _extract_comparison(self, query: str) -> List[str]:
        """Extract comparison conditions"""
        query_lower = query.lower()
        conditions = []
        
        # Look for numeric comparisons
        for comp_key, comp_op in self.comparisons.items():
            pattern = f"{comp_key}\s+(\d+(?:\.\d+)?)"
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                value = match.group(1)
                # Determine which field to compare based on context
                field = 's.total_amount'  # default to amount
                if 'quantity' in query_lower or 'units' in query_lower:
                    field = 's.quantity'
                elif 'price' in query_lower:
                    field = 'p.price'
                elif 'stock' in query_lower:
                    field = 'p.stock'
                conditions.append(f"{field} {comp_op} {value}")
                
        return conditions

    def _extract_grouping(self, query: str) -> Tuple[str, str]:
        """Extract grouping field and necessary joins"""
        query_lower = query.lower()
        joins = []
        group_by = None
        
        # Check for specific grouping patterns
        if 'by region' in query_lower or 'per region' in query_lower:
            group_by = 'c.region'
            joins.append('JOIN customers c ON s.customer_id = c.id')
        elif 'by product' in query_lower or 'per product' in query_lower or 'by item' in query_lower:
            group_by = 'p.name'
            joins.append('JOIN products p ON s.product_id = p.id')
        elif 'by category' in query_lower or 'per category' in query_lower:
            group_by = 'p.category'
            joins.append('JOIN products p ON s.product_id = p.id')
        elif 'by customer' in query_lower or 'per customer' in query_lower:
            group_by = 'c.name'
            joins.append('JOIN customers c ON s.customer_id = c.id')
        elif 'by date' in query_lower or 'per date' in query_lower:
            group_by = 'date(s.date)'
        elif 'by month' in query_lower or 'per month' in query_lower:
            group_by = "strftime('%Y-%m', s.date)"
        elif 'by year' in query_lower or 'per year' in query_lower:
            group_by = "strftime('%Y', s.date)"
        
        # If no specific grouping found, try to infer from context
        if not group_by:
            if 'region' in query_lower:
                group_by = 'c.region'
                joins.append('JOIN customers c ON s.customer_id = c.id')
            elif 'product' in query_lower or 'item' in query_lower:
                group_by = 'p.name'
                joins.append('JOIN products p ON s.product_id = p.id')
            elif 'category' in query_lower:
                group_by = 'p.category'
                joins.append('JOIN products p ON s.product_id = p.id')
            elif 'customer' in query_lower:
                group_by = 'c.name'
                joins.append('JOIN customers c ON s.customer_id = c.id')
        
        return group_by, ' '.join(joins)

    def _extract_sorting(self, query: str) -> Tuple[str, str]:
        """Extract sorting field and direction"""
        query_lower = query.lower()
        direction = 'DESC'  # default sort direction
        
        # Check for sort direction
        for sort_key, sort_dir in self.sort_patterns.items():
            if sort_key in query_lower:
                direction = sort_dir
                break
        
        # Determine sort field based on context
        sort_field = 'total'  # default sort field
        if 'quantity' in query_lower or 'units' in query_lower:
            sort_field = 'quantity'
        elif 'average' in query_lower or 'avg' in query_lower:
            sort_field = 'average'
            
        return sort_field, direction

    def _extract_limit(self, query: str) -> str:
        """Extract result limit"""
        query_lower = query.lower()
        
        # Look for specific number patterns
        limit_patterns = [
            r'top\s+(\d+)',
            r'first\s+(\d+)',
            r'(\d+)\s+best',
            r'(\d+)\s+most',
            r'limit\s+(\d+)',
            r'show\s+(\d+)'
        ]
        
        for pattern in limit_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return f"LIMIT {match.group(1)}"
        
        # Check for specific keywords
        if any(word in query_lower for word in ['top', 'best', 'highest', 'lowest']):
            return "LIMIT 5"  # default limit for top/best queries
            
        return ""

    async def generate_sql_with_ai(self, natural_language_query: str) -> Tuple[str, str]:
        """
        Use AI to convert natural language to SQL
        Returns: (sql_query, explanation)
        """
        try:
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured. Falling back to rule-based processing.")
            
            # Construct the prompt
            prompt = f"""
            Given the following database schema:
            {self.schema_definition}
            
            Convert this natural language query to SQL:
            "{natural_language_query}"
            
            Requirements:
            1. Use proper table joins
            2. Include appropriate WHERE clauses
            3. Handle aggregations if needed
            4. Use proper GROUP BY if needed
            5. Add ORDER BY if relevant
            6. Include LIMIT if specified
            
            Also provide a brief explanation of what the query does.
            
            Format the response as:
            SQL: <the SQL query>
            Explanation: <brief explanation>
            """
            
            # Call OpenAI API
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that converts natural language to SQL queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Extract SQL and explanation from response
            content = response.choices[0].message.content
            sql_match = re.search(r'SQL:\s*(.*?)(?=Explanation:|$)', content, re.DOTALL)
            explanation_match = re.search(r'Explanation:\s*(.*?)$', content, re.DOTALL)
            
            sql_query = sql_match.group(1).strip() if sql_match else ""
            explanation = explanation_match.group(1).strip() if explanation_match else ""
            
            # Validate the generated SQL
            self._validate_generated_sql(sql_query)
            
            return sql_query, explanation
            
        except Exception as e:
            logger.warning(f"AI-based generation failed: {str(e)}. Falling back to rule-based processing.")
            return None, None

    def _validate_generated_sql(self, sql_query: str) -> None:
        """
        Validate the AI-generated SQL query
        """
        required_patterns = [
            (r'\bFROM\b.*\bsales\b', "Query must use the sales table"),
            (r'\bJOIN\b.*\b(products|customers)\b', "Query must include proper table joins"),
            (r'\bWHERE\b|\bGROUP BY\b|\bORDER BY\b', "Query must include appropriate clauses")
        ]
        
        for pattern, error_message in required_patterns:
            if not re.search(pattern, sql_query, re.IGNORECASE):
                raise ValueError(f"Invalid SQL generated: {error_message}")

    async def generate_sql(self, natural_language_query: str) -> str:
        """
        Convert natural language to SQL using AI first, then fall back to rule-based
        """
        try:
            logger.info(f"Processing query: {natural_language_query}")
            
            # Try AI-based generation first
            sql_query, explanation = await self.generate_sql_with_ai(natural_language_query)
            
            if sql_query:
                logger.info(f"AI generated SQL: {sql_query}")
                logger.info(f"Explanation: {explanation}")
                return sql_query
            
            # Fall back to rule-based processing
            logger.info("Falling back to rule-based processing")
            return self._generate_sql_rule_based(natural_language_query)
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {str(e)}", exc_info=True)
            raise Exception(f"Error generating SQL query: {str(e)}")

    def _generate_sql_rule_based(self, natural_language_query: str) -> str:
        """
        Original rule-based SQL generation (existing implementation)
        """
        # Validate query against available data
        is_valid, suggestion, components = self._validate_query(natural_language_query)
        
        if not is_valid:
            logger.warning(f"Invalid query detected: {suggestion}")
            raise ValueError(suggestion)
        
        # Extract components and generate SQL as before
        agg_func = self._extract_aggregation(natural_language_query)
        group_by, joins = self._extract_grouping(natural_language_query)
        time_condition = self._extract_time_condition(natural_language_query)
        comparisons = self._extract_comparison(natural_language_query)
        sort_field, sort_direction = self._extract_sorting(natural_language_query)
        limit = self._extract_limit(natural_language_query)
        
        # Build WHERE clause
        where_conditions = []
        if time_condition:
            where_conditions.append(time_condition)
        where_conditions.extend(comparisons)
        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        
        # Build the complete SQL query
        select_clause = f"SELECT {group_by}" if group_by else "SELECT 'Total' as period"
        agg_column = f"{agg_func}({metric})"
        
        sql_query = f"""
            {select_clause},
            {agg_column} as total
            FROM sales s
            {joins}
            {where_clause}
            {f'GROUP BY {group_by}' if group_by else ''}
            ORDER BY total {sort_direction}
            {limit}
        """
        
        # Clean up the query
        sql_query = ' '.join(sql_query.split())
        logger.info(f"Rule-based generated SQL: {sql_query}")
        return sql_query

    def explain_query(self, sql_query: str) -> str:
        """
        Generate a natural language explanation of the SQL query
        """
        try:
            logger.info(f"Generating explanation for SQL query: {sql_query}")
            explanation_parts = []
            
            # Extract and explain the SELECT clause
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE)
            if select_match:
                columns = select_match.group(1).strip()
                if 'SUM' in columns:
                    explanation_parts.append("This query calculates the total")
                elif 'AVG' in columns:
                    explanation_parts.append("This query calculates the average")
                elif 'COUNT' in columns:
                    explanation_parts.append("This query counts")
                elif 'MIN' in columns:
                    explanation_parts.append("This query finds the minimum")
                elif 'MAX' in columns:
                    explanation_parts.append("This query finds the maximum")
                
            # Explain grouping
            if 'GROUP BY' in sql_query:
                group_match = re.search(r'GROUP BY\s+(.*?)(?=ORDER BY|LIMIT|$)', sql_query, re.IGNORECASE)
                if group_match:
                    group_field = group_match.group(1).strip()
                    explanation_parts.append(f"grouped by {group_field.split('.')[-1]}")
            
            # Explain conditions
            if 'WHERE' in sql_query:
                where_match = re.search(r'WHERE\s+(.*?)(?=GROUP BY|ORDER BY|LIMIT|$)', sql_query, re.IGNORECASE)
                if where_match:
                    conditions = where_match.group(1).strip()
                    explanation_parts.append(f"filtered by {conditions}")
            
            # Explain ordering
            if 'ORDER BY' in sql_query:
                if 'DESC' in sql_query:
                    explanation_parts.append("sorted in descending order")
                else:
                    explanation_parts.append("sorted in ascending order")
            
            # Explain limit
            if 'LIMIT' in sql_query:
                limit_match = re.search(r'LIMIT\s+(\d+)', sql_query, re.IGNORECASE)
                if limit_match:
                    explanation_parts.append(f"showing top {limit_match.group(1)} results")
            
            explanation = ' '.join(explanation_parts) + '.'
            logger.info(f"Generated explanation: {explanation}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating query explanation: {str(e)}", exc_info=True)
            return "This query retrieves data from the database."