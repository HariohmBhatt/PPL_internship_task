"""User model."""

from typing import TYPE_CHECKING

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.quiz import Quiz
    from app.models.submission import Submission


class User(Base):
    """User model for authentication and ownership."""
    
    username: Mapped[str] = mapped_column(
        String(50), 
        unique=True, 
        index=True, 
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True, 
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Relationships
    quizzes: Mapped[list["Quiz"]] = relationship(
        back_populates="creator", 
        cascade="all, delete-orphan"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_user_username_email", "username", "email"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
