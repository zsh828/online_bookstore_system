import re
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class User:
    def __init__(self, user_id: str, username: str, email: str, password_hash: str, 
                 membership_level: str = "普通", points: int = 0):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.membership_level = membership_level
        self.points = points

    def add_points(self, amount: int):
        if amount < 0:
            raise ValueError("Points added cannot be negative")
        self.points += amount
        return self.points

    def update_membership(self):
        """自动升级会员等级"""
        if self.points >= 5000 and self.membership_level != "金卡":
            self.membership_level = "金卡"
        elif self.points >= 1000 and self.membership_level == "普通":
            self.membership_level = "银卡"
        # 注意：通常降级逻辑较复杂，这里仅实现升级。若需降级可在此扩展。
        return self.membership_level


class Book:
    def __init__(self, isbn: str, title: str, author: str, price: float, stock: int, category: str):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.price = price
        self.stock = stock
        self.category = category

    def check_stock(self, quantity: int) -> bool:
        return self.stock >= quantity

    def reduce_stock(self, quantity: int):
        if not self.check_stock(quantity):
            raise ValueError(f"Insufficient stock for book {self.isbn}. Available: {self.stock}, Requested: {quantity}")
        self.stock -= quantity


class CartItem:
    def __init__(self, isbn: str, quantity: int):
        self.isbn = isbn
        self.quantity = quantity


class OrderItem:
    def __init__(self, isbn: str, title: str, unit_price: float, quantity: int, subtotal: float):
        self.isbn = isbn
        self.title = title
        self.unit_price = unit_price
        self.quantity = quantity
        self.subtotal = subtotal


class Order:
    STATUS_PENDING = "待支付"
    STATUS_PAID = "已支付"
    STATUS_CANCELLED = "已取消"

    def __init__(self, order_id: str, user_id: str, items: List[OrderItem], 
                 total_amount: float, discount_amount: float, final_amount: float, 
                 status: str = STATUS_PENDING):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total_amount = total_amount
        self.discount_amount = discount_amount
        self.final_amount = final_amount
        self.status = status
        self.created_at = datetime.now()

    def pay(self):
        if self.status != Order.STATUS_PENDING:
            raise ValueError(f"Cannot pay for order with status: {self.status}")
        self.status = Order.STATUS_PAID

    def cancel(self):
        if self.status != Order.STATUS_PENDING:
            raise ValueError(f"Cannot cancel order with status: {self.status}")
        self.status = Order.STATUS_CANCELLED


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()