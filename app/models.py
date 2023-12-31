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

    id = Column(Integer, primary_key=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    profile_pic = Column(String, default=None)
    updated_by = Column(TIMESTAMP(timezone=True),
                        nullable=False,
                        server_default=text("now()"))


class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer,
                     ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False)
    caption = Column(String, nullable=False, default=None)
    post_image = Column(String, default=None)
    is_published = Column(Boolean, server_default="TRUE", nullable=False)
    updated_by = Column(TIMESTAMP(timezone=True),
                        nullable=False,
                        server_default=text("now()"))

    user_detail = relationship("Users")


class Votes(Base):
    __tablename__ = "votes"

    user_id = Column(Integer,
                     ForeignKey("users.id", ondelete="CASCADE"),
                     primary_key=True)
    post_id = Column(Integer,
                     ForeignKey("posts.post_id", ondelete="CASCADE"),
                     primary_key=True)

    post_detail = relationship("Post")
