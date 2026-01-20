"""
Database config for CMS

This module sets up the SQLAlchemy database engine, session factory,
and declarative base for ORM models.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Local SQLite database file
DATABASE_URL = "sqlite:///cms.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
