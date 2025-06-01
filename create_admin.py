#!/usr/bin/env python3
"""
Script to create an admin user for the webscraper application
"""

import sys
import os
sys.path.append('/app')

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.models.database import Base
from src.models.user import User
from src.api.auth import get_password_hash
from src.core.config import settings

def create_admin_user():
    """Create admin user if it doesn't exist"""
    
    # Create database connection
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        
        if existing_admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@webscraper.local",
            hashed_password=get_password_hash("admin123456"),
            is_active=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123456")
        print("Email: admin@webscraper.local")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()