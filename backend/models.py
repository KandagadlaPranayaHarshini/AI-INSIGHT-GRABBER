from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="user", cascade="all, delete-orphan")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    missing_values = Column(Integer, default=0)
    duplicate_rows = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="datasets")
    insights = relationship("Insight", back_populates="dataset", cascade="all, delete-orphan")
    charts = relationship("ChartConfig", back_populates="dataset", cascade="all, delete-orphan")


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    insight_title = Column(String(255), nullable=False)
    insight_text = Column(Text, nullable=False)
    category = Column(String(50), default="General Summary")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    dataset = relationship("Dataset", back_populates="insights")
    user = relationship("User", back_populates="insights")


class ChartConfig(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    chart_type = Column(String(50), nullable=False)  # scatter, bar, line, histogram
    x_axis = Column(String(100), nullable=False)
    y_axis = Column(String(100), nullable=True)
    chart_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    dataset = relationship("Dataset", back_populates="charts")