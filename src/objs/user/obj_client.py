from sqlalchemy.orm import relationship
from ...db.database import Base
from .obj_user import CMSUser

class CMSClientUser(CMSUser):
    event = relationship("Event", back_populates="user")
    pass