"""
obj_user.py
The module defines this CMSUser model, providing user authentication and management
"""

from sqlalchemy import Column, Integer, String
from src.security.security_utils import PasswordHasher
from ...db.database import Base
import sys
import os


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

class CMSUser(Base):
    """
    Represents a user in the CMS system.

    Attributes:
        id (int): The unique identifier for the user.
        user_name (str): The username of the user.
        user_pswd (str): The hashed password of the user.
        user_email (str): The unique email address of the user.
        permission_lvl (int): The permission level of the user.

    Methods:
        set_password: Hashes and sets the user's password.
        check_password: Verifies a password against the stored hash.
        login: Class method to authenticate a user by email and password.
    """
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
