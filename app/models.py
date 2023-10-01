from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from .databases import Base
import uuid

generated_uuid = str(uuid.uuid4()).replace('-', '')


# Users Database model
class Users(Base):

    __tablename__ = "users"

    id = Column(Integer,
                primary_key=True,
                nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    profile_pic = Column(String, default=None)
    updated_by = Column(TIMESTAMP(timezone=True),
                        nullable=False,
                        server_default=text("now()"))
