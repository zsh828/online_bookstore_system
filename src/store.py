from src.models import (
    User, Book, CartItem, Order, OrderItem, 
    validate_email, hash_password
)
from typing import List, Dict, Optional, Tuple
import copy


class BookStore:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.books: Dict[str, Book] = {}
        self.carts: Dict[str, List[CartItem]] = {}  # user_id -> list of CartItem
        self.orders: Dict[str, Order] = {}

    # --- 用户管理 ---

    def register_user(self, username: str, email: str, password: str) -> User:
        if not validate_email(email):
            raise ValueError("Invalid email format")
        
        # Check if user already exists (by email or username ideally, but here by ID generation simplicity we check logic)
        # For this simple model, we assume unique IDs are generated. Let's use a simple counter or UUID based on email uniqueness check?
        # To keep it simple and robust, let's generate a user_id. In real app, check DB for existing email/username.
        # Here, we will just ensure no duplicate email in our dict keys for simplicity of lookup, 
        # or better, maintain a separate index. But the prompt asks for specific fields.
        # Let's use email as a unique identifier for users to avoid collisions easily in memory.
        
        # Actually, let's generate a UUID for user_id but check if email is already taken.
        for u in self.users.values():
            if u.email == email:
                raise ValueError("Email already registered")
        
        user_id = f"U{len(self.users)+1:04d}"
        password_hash = hash_password(password)
        user = User(user_id, username, email, password_hash)
        self.users[user_id] = user
        
        # Initialize empty cart
        self.carts[user_id] = []
        
        return user

    def login_user(self, email: str, password: str) -> User:
        target_user = None
        for u in self.users.values():
            if u.email == email:
                target_user = u
                break
        
        if not target_user:
            raise ValueError("User not found")
        
        if target_user.password_hash != hash_password(password):
            raise ValueError("Incorrect password")
            
        return target_user

    def get_user(self, user_id: str) -> User:
        if user_id not in self.users:
            raise ValueError("User not found")
        return self.users[user_id]

    def add_points(self, user_id: str, amount: int) -> int:
        user = self.get_user(user_id)
        new_points = user.add_points(amount)
        user.update_membership()
        return new_points

    # --- 图书管理 ---

    def add_book(self, isbn: str, title: str, author: str, price: float, stock: int, category: str) -> Book:
        if price < 0 or stock < 0:
            raise ValueError("Price and stock must be non-negative")
        
        if isbn in self.books:
            raise ValueError("Book with this ISBN already exists")
            
        book = Book(isbn, title, author, price, stock, category)
        self.books[isbn] = book
        return book

    def search_books(self, keyword: str = None, author: str = None, isbn: str = None) -> List[Book]:
        results = []
        for book in self.books.values():
            match = True
            if keyword:
                if keyword.lower() not in book.title.lower() and keyword.lower() not in book.author.lower():
                    match = False
            if author:
                if author.lower() not in book.author.lower():
                    match = False
            if isbn:
                if isbn != book.isbn:
                    match = False
            
            if match:
                results.append(book)
        return results

    def get_book(self, isbn: str) -> Book:
        if isbn not in self.books:
            raise ValueError("Book not found")
        return self.books[isbn]

    def update_stock(self, isbn: str, new_stock: int):
        book = self.get_book(isbn)
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
        book.stock = new_stock

    # --- 购物车管理 ---

    def get_cart(self, user_id: str) -> List[CartItem]:
        if user_id not in self.carts:
            raise ValueError("User not found")
        return self.carts[user_id]

    def add_to_cart(self, user_id: str, isbn: str, quantity: int):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        user = self.get_user(user_id)
        book = self.get_book(isbn)
        
        if not book.check_stock(quantity):
            raise ValueError(f"Insufficient stock for book {isbn}")
        
        cart = self.carts[user_id]
        
        # Check if item already in cart
        existing_item = None
        for item in cart:
            if item.isbn == isbn:
                existing_item = item
                break
        
        if existing_item:
            new_qty = existing_item.quantity + quantity
            # Check if adding more exceeds stock
            if not book.check_stock(new_qty - existing_item.quantity):
                 raise ValueError(f"Insufficient stock for additional quantity")
            existing_item.quantity = new_qty
        else:
            cart.append(CartItem(isbn, quantity))

    def remove_from_cart(self, user_id: str, isbn: str):
        cart = self.carts[user_id]
        original_len = len(cart)
        self.carts[user_id] = [item for item in cart if item.isbn != isbn]
        
        if len(self.carts[user_id]) == original_len:
            raise ValueError("Item not found in cart")

    def update_cart_quantity(self, user_id: str, isbn: str, quantity: int):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        cart = self.carts[user_id]
        book = self.get_book(isbn)
        
        for item in cart:
            if item.isbn == isbn:
                if not book.check_stock(quantity - item.quantity):
                     raise ValueError("Insufficient stock for requested quantity")
                item.quantity = quantity
                return
        
        raise ValueError("Item not found in cart")

    def clear_cart(self, user_id: str):
        self.carts[user_id] = []

    # --- 订单管理 ---

    def create_order(self, user_id: str) -> Order:
        user = self.get_user(user_id)
        cart = self.carts[user_id]
        
        if not cart:
            raise ValueError("Cart is empty")
        
        # Validate stock again and prepare order items
        order_items = []
        total_amount = 0.0
        
        for item in cart:
            book = self.get_book(item.isbn)
            if not book.check_stock(item.quantity):
                raise ValueError(f"Insufficient stock for book {book.isbn} during checkout")
            
            subtotal = book.price * item.quantity
            order_items.append(OrderItem(
                isbn=book.isbn,
                title=book.title,
                unit_price=book.price,
                quantity=item.quantity,
                subtotal=subtotal
            ))
            total_amount += subtotal
        
        # Calculate Discount
        discount_rate = 1.0
        if user.membership_level == "银卡":
            discount_rate = 0.95
        elif user.membership_level == "金卡":
            discount_rate = 0.90
            
        discount_amount = total_amount * (1 - discount_rate)
        final_amount = total_amount - discount_amount
        
        # Deduct Stock
        for item in cart:
            book = self.get_book(item.isbn)
            book.reduce_stock(item.quantity)
        
        # Create Order Object
        order_id = f"O{len(self.orders)+1:04d}"
        order = Order(order_id, user_id, order_items, total_amount, discount_amount, final_amount)
        self.orders[order_id] = order
        
        # Clear Cart
        self.clear_cart(user_id)
        
        return order

    def pay_order(self, order_id: str):
        order = self.get_order(order_id)
        order.pay()
        
        # Add points to user
        user = self.get_user(order.user_id)
        # 1 yuan = 1 point. Usually points are integers.
        points_earned = int(order.final_amount)
        self.add_points(order.user_id, points_earned)

    def cancel_order(self, order_id: str):
        order = self.get_order(order_id)
        order.cancel()
        
        # Restore Stock
        for item in order.items:
            book = self.get_book(item.isbn)
            book.stock += item.quantity
            
        # Note: Points were not awarded yet because status was PENDING until pay().
        # If paid then cancelled, usually points should be deducted, but prompt says "Cancel: restore stock and cart".
        # Prompt doesn't explicitly mention point deduction on cancel, only "restore stock and cart".
        # Since points are added ON PAYMENT, cancelling a pending order doesn't involve points.
        # If the prompt implied cancelling a PAID order, it would be complex. 
        # Based on "Order Status Incorrect" error handling, we can only cancel PENDING orders.
        
        # Re-add to cart? Prompt says "restore ... cart".
        # However, standard e-commerce often removes cancelled orders from view.
        # Let's interpret "restore cart" as putting items back into the user's cart so they can buy them again.
        user_id = order.user_id
        current_cart = self.carts[user_id]
        
        for item in order.items:
            # Find if already in cart
            existing = None
            for c_item in current_cart:
                if c_item.isbn == item.isbn:
                    existing = c_item
                    break
            
            if existing:
                existing.quantity += item.quantity
            else:
                current_cart.append(CartItem(item.isbn, item.quantity))

    def get_order(self, order_id: str) -> Order:
        if order_id not in self.orders:
            raise ValueError("Order not found")
        return self.orders[order_id]

    # --- 销售统计 ---

    def get_sales_stats(self, category: str = None) -> List[Tuple[str, int]]:
        """Returns list of (title, total_sold_count) sorted by count descending"""
        sales_count = {}
        
        for order in self.orders.values():
            # Only consider completed/paid orders for sales stats? Or all non-cancelled?
            # Typically "Sales" implies successful transactions.
            if order.status == Order.STATUS_CANCELLED:
                continue
                
            for item in order.items:
                if category:
                    book = self.get_book(item.isbn)
                    if book.category != category:
                        continue
                        
                if item.title in sales_count:
                    sales_count[item.title] += item.quantity
                else:
                    sales_count[item.title] = item.quantity
                    
        # Sort by count descending
        sorted_sales = sorted(sales_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_sales