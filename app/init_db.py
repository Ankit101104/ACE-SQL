from models.database import engine, SessionLocal
from models.sample_data import Base, Product, Customer, Sale, sample_products, sample_customers, sample_sales
from datetime import datetime

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a new session
    db = SessionLocal()
    
    try:
        # Add sample products
        for product_data in sample_products:
            product = Product(**product_data)
            db.add(product)
        
        # Add sample customers
        for customer_data in sample_customers:
            customer = Customer(**customer_data)
            db.add(customer)
        
        # Add sample sales
        for sale_data in sample_sales:
            # Convert date string to datetime object
            sale_data['date'] = datetime.strptime(sale_data['date'], '%Y-%m-%d').date()
            sale = Sale(**sale_data)
            db.add(sale)
        
        # Commit the changes
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db() 