from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, ForeignKey, Identity, TEXT, DateTime, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, relationship

class base(DeclarativeBase):
    pass

class User(base):
    __tablename__ = 'users'

    user_id: Mapped[int] = MappedColumn(Identity(always=True, start=1, increment=1), primary_key=True)

    username: Mapped[str] = MappedColumn(String(100))

    hashed_password : Mapped[str] = MappedColumn(String(100))

    email: Mapped[str] = MappedColumn(String(100), unique=True)

    phone: Mapped[str] = MappedColumn(String(20))

    default_address: Mapped[str] = MappedColumn(TEXT)


    orders: Mapped[List["Order"]] = relationship(back_populates="user", cascade='all, delete-orphan')

    tickets: Mapped[List["Ticket"]] = relationship(back_populates="user", cascade='all, delete-orphan')


class Order(base):
    __tablename__ = 'orders'

    order_id: Mapped[int] = MappedColumn(Identity(always=True, start=1, increment=1), primary_key=True)

    user_id: Mapped[int] = MappedColumn(ForeignKey("users.user_id"), nullable=False)

    status: Mapped[str] = MappedColumn(String(50), default='Pending')

    order_date: Mapped[datetime] = MappedColumn(DateTime, server_default=func.now())

    expected_delivery_date: Mapped[datetime] = MappedColumn(DateTime, server_default=func.now())

    shipping_address: Mapped[str] = MappedColumn(TEXT)

    total_amount: Mapped[float] = MappedColumn(Numeric(10, 2), nullable=False)


    user: Mapped["User"] = relationship(back_populates='orders')

    invoice: Mapped[Optional["Invoice"]] = relationship(back_populates="order", cascade='all, delete-orphan')

    refunds: Mapped[List["Refund"]] = relationship(back_populates="order", cascade='all, delete-orphan')

    tickets: Mapped[List["Ticket"]] = relationship(back_populates="order")


class Invoice(base):
    __tablename__ = 'invoices'

    invoice_id: Mapped[int] = MappedColumn(Identity(always=True, start=1, increment=1), primary_key=True)

    order_id: Mapped[int] = MappedColumn(ForeignKey("orders.order_id", ondelete="CASCADE"), unique=True, nullable=False)

    issue_date: Mapped[datetime] = MappedColumn(DateTime, server_default=func.now())

    pdf_url: Mapped[str] = MappedColumn(TEXT, nullable=True)


    order: Mapped["Order"] = relationship(back_populates="invoice")


class Refund(base):
    __tablename__ = 'refunds'

    refund_id: Mapped[int] = MappedColumn(Identity(always=True, start=1, increment=1), primary_key=True)

    order_id: Mapped[int] = MappedColumn(ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)

    status: Mapped[str] = MappedColumn(String(50), default='Initiated')

    refund_amount: Mapped[float] = MappedColumn(Numeric(10, 2), nullable=False)

    created_at: Mapped[datetime] = MappedColumn(DateTime, server_default=func.now())


    order: Mapped["Order"] = relationship(back_populates="refunds")


class Ticket(base):
    __tablename__ = 'tickets'

    ticket_id: Mapped[int] = MappedColumn(Identity(always=True, start=1, increment=1), primary_key=True)

    user_id: Mapped[int] = MappedColumn(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

    order_id: Mapped[int] = MappedColumn(ForeignKey("orders.order_id", ondelete="SET NULL"), nullable=True)

    issue_type: Mapped[str] = MappedColumn(String(50), nullable=True)

    status: Mapped[str] = MappedColumn(String(50), default='Open')

    created_at: Mapped[datetime] = MappedColumn(DateTime, server_default=func.now())


    user: Mapped["User"] = relationship(back_populates="tickets")

    order: Mapped[Optional["Order"]] = relationship(back_populates="tickets")
