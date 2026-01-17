from sqlalchemy import Column, Integer, String
from ...db.database import Base

class CMSUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_name = Column(String, nullable=False)
    user_pswd = Column(String, nullable=False)
    user_email = Column(String, nullable=False)
    permission_lvl = Column(Integer, nullable=False)

    @classmethod
    def login(cls, db, user_email, user_pswd):
        return db.query(cls).filter_by(user_email=user_email, user_pswd=user_pswd).first()