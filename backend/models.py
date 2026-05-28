from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    in_stock = Column(Boolean, default=True)
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)

    telegram_id = Column(String, nullable=True)
    telegram_username = Column(String, nullable=True)

    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)

    city = Column(String, nullable=True)
    warehouse = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    comment = Column(String, nullable=True)

    status = Column(String, default="new")