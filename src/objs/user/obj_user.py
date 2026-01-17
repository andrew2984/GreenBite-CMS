from sqlalchemy import Column, Integer, String
from ...db.database import Base
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from src.security.security_utils import PasswordHasher

class CMSUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=False)
    user_pswd = Column(String, nullable=False)  # Now stores hashed password
    user_email = Column(String, nullable=False, unique=True)
    permission_lvl = Column(Integer, nullable=False)

    def set_password(self, password: str):
        self.user_pswd = PasswordHasher.hash_password(password)
    
    def check_password(self, password: str) -> bool:
        return PasswordHasher.verify_password(password, self.user_pswd)

    @classmethod
    def login(cls, db, user_email, user_pswd):
        user = db.query(cls).filter_by(user_email=user_email).first()
        
        if not user:
            return None

        if user.check_password(user_pswd):
            return user
        
        return None