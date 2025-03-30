from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String)
    price = Column(Float)
    stock = Column(Integer)

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    region = Column(String)

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    product_id = Column(Integer, ForeignKey("products.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    quantity = Column(Integer)
    total_amount = Column(Float)

    product = relationship("Product")
    customer = relationship("Customer")

# Sample data
sample_products = [
    {"name": "Laptop", "category": "Electronics", "price": 999.99, "stock": 50},
    {"name": "Smartphone", "category": "Electronics", "price": 699.99, "stock": 100},
    {"name": "Headphones", "category": "Accessories", "price": 99.99, "stock": 200},
    {"name": "Tablet", "category": "Electronics", "price": 499.99, "stock": 75},
    {"name": "Smartwatch", "category": "Electronics", "price": 299.99, "stock": 150},
]

sample_customers = [
    {"name": "John Doe", "email": "john@example.com", "region": "North"},
    {"name": "Jane Smith", "email": "jane@example.com", "region": "South"},
    {"name": "Bob Johnson", "email": "bob@example.com", "region": "East"},
    {"name": "Alice Brown", "email": "alice@example.com", "region": "West"},
]

sample_sales = [
    {"date": "2024-01-01", "product_id": 1, "customer_id": 1, "quantity": 2, "total_amount": 1999.98},
    {"date": "2024-01-02", "product_id": 2, "customer_id": 2, "quantity": 1, "total_amount": 699.99},
    {"date": "2024-01-03", "product_id": 3, "customer_id": 3, "quantity": 3, "total_amount": 299.97},
    {"date": "2024-01-04", "product_id": 4, "customer_id": 4, "quantity": 1, "total_amount": 499.99},
    {"date": "2024-01-05", "product_id": 5, "customer_id": 1, "quantity": 2, "total_amount": 599.98},
] 