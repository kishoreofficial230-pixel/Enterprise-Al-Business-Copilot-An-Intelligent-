from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime

from app.database.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    product_name = Column(String(255), nullable=False)

    category = Column(String(100), nullable=True)

    quantity = Column(Integer, nullable=False)

    amount = Column(Float, nullable=False)

    customer_name = Column(String(255), nullable=True)

    sale_date = Column(
        DateTime,
        default=datetime.utcnow
    )