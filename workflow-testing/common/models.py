from enum import Enum as PyEnum

from pydantic.alias_generators import to_camel
from sqlmodel import Field, Relationship, SQLModel


class OrderStatus(str, PyEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"


class User(SQLModel, table=True):
    __tablename__: str = "users"
    location_code: str
    user_email: str = Field(unique=True, index=True)
    user_id: int | None = Field(default=None, primary_key=True)

    orders: list["Order"] = Relationship(back_populates="user")

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True


class Product(SQLModel, table=True):
    __tablename__: str = "products"
    name: str
    price: float
    location_code: str
    product_id: int | None = Field(default=None, primary_key=True)

    inventory_levels: "InventoryLevel" = Relationship(back_populates="product")
    orders: list["Order"] = Relationship(back_populates="product")

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True


class InventoryLevel(SQLModel, table=True):
    __tablename__: str = "inventory_levels"
    inventory: int
    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.product_id", unique=True)

    product: "Product" = Relationship(back_populates="inventory_levels")

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True


class Order(SQLModel, table=True):
    __tablename__: str = "orders"
    inventory: int
    order_request_id: str
    user_id: int = Field(foreign_key="users.user_id")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    product_id: int = Field(foreign_key="products.product_id")
    order_id: int | None = Field(default=None, primary_key=True)

    user: "User" = Relationship(back_populates="orders")
    product: "Product" = Relationship(back_populates="orders")

    class Config:
        alias_generator = to_camel
        populate_by_name = True
        from_attributes = True
