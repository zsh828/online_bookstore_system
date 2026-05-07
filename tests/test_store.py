import pytest
from src.store import BookStore
from src.models import User, Book, Order


@pytest.fixture
def store():
    return BookStore()


class TestUserManagement:
    def test_register_user_success(self, store):
        user = store.register_user("Alice", "alice@example.com", "password123")
        assert user.username == "Alice"
        assert user.email == "alice@example.com"
        assert user.membership_level == "普通"
        assert user.points == 0
        assert user.user_id in store.users

    def test_register_user_invalid_email(self, store):
        with pytest.raises(ValueError, match="Invalid email format"):
            store.register_user("Bob", "bob-at-example.com", "password123")

    def test_register_user_duplicate_email(self, store):
        store.register_user("Alice", "alice@example.com", "password123")
        with pytest.raises(ValueError, match="Email already registered"):
            store.register_user("Alice2", "alice@example.com", "password123")

    def test_login_user_success(self, store):
        store.register_user("Alice", "alice@example.com", "password123")
        user = store.login_user("alice@example.com", "password123")
        assert user.email == "alice@example.com"

    def test_login_user_wrong_password(self, store):
        store.register_user("Alice", "alice@example.com", "password123")
        with pytest.raises(ValueError, match="Incorrect password"):
            store.login_user("alice@example.com", "wrongpassword")

    def test_login_user_not_found(self, store):
        with pytest.raises(ValueError, match="User not found"):
            store.login_user("nonexistent@example.com", "password")

    def test_add_points_and_upgrade(self, store):
        user = store.register_user("Alice", "alice@example.com", "pass")
        # Upgrade to Silver
        store.add_points(user.user_id, 1000)
        assert user.membership_level == "银卡"
        assert user.points == 1000
        
        # Upgrade to Gold
        store.add_points(user.user_id, 4000)
        assert user.membership_level == "金卡"
        assert user.points == 5000

    def test_add_negative_points_raises_error(self, store):
        user = store.register_user("Alice", "alice@example.com", "pass")
        with pytest.raises(ValueError, match="Points added cannot be negative"):
            store.add_points(user.user_id, -10)


class TestBookManagement:
    def test_add_book_success(self, store):
        book = store.add_book("ISBN123", "Python Book", "Author A", 50.0, 10, "Tech")
        assert book.title == "Python Book"
        assert book.isbn == "ISBN123"
        assert book.isbn in store.books

    def test_add_book_duplicate_isbn(self, store):
        store.add_book("ISBN123", "Python Book", "Author A", 50.0, 10, "Tech")
        with pytest.raises(ValueError, match="Book with this ISBN already exists"):
            store.add_book("ISBN123", "Another Book", "Author B", 60.0, 5, "Tech")

    def test_search_books_by_title(self, store):
        store.add_book("ISBN1", "Python Programming", "Author A", 50.0, 10, "Tech")
        store.add_book("ISBN2", "Java Programming", "Author B", 60.0, 10, "Tech")
        
        results = store.search_books(keyword="Python")
        assert len(results) == 1
        assert results[0].title == "Python Programming"

    def test_search_books_by_author(self, store):
        store.add_book("ISBN1", "Python Programming", "Author A", 50.0, 10, "Tech")
        store.add_book("ISBN2", "Java Programming", "Author A", 60.0, 10, "Tech")
        
        results = store.search_books(author="Author A")
        assert len(results) == 2

    def test_search_books_no_match(self, store):
        store.add_book("ISBN1", "Python", "Author A", 50.0, 10, "Tech")
        results = store.search_books(keyword="NonExistent")
        assert len(results) == 0

    def test_get_book_not_found(self, store):
        with pytest.raises(ValueError, match="Book not found"):
            store.get_book("INVALID_ISBN")

    def test_update_stock(self, store):
        book = store.add_book("ISBN1", "Book", "Auth", 10.0, 5, "Cat")
        store.update_stock("ISBN1", 10)
        assert book.stock == 10

    def test_update_stock_negative_raises_error(self, store):
        store.add_book("ISBN1", "Book", "Auth", 10.0, 5, "Cat")
        with pytest.raises(ValueError, match="Stock cannot be negative"):
            store.update_stock("ISBN1", -1)


class TestShoppingCart:
    def test_add_to_cart_success(self, store):
        store.add_book("ISBN1", "Book", "Auth", 10.0, 100, "Cat")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 2)
        cart = store.get_cart(user.user_id)
        assert len(cart) == 1
        assert cart[0].isbn == "ISBN1"
        assert cart[0].quantity == 2

    def test_add_to_cart_insufficient_stock(self, store):
        store.add_book("ISBN1", "Book", "Auth", 10.0, 5, "Cat")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            store.add_to_cart(user.user_id, "ISBN1", 10)

    def test_add_to_cart_non_existent_book(self, store):
        user = store.register_user("Alice", "alice@test.com", "pass")
        with pytest.raises(ValueError, match="Book not found"):
            store.add_to_cart(user.user_id, "INVALID", 1)

    def test_add_same_item_multiple_times(self, store):
        store.add_book("ISBN1", "Book", "Auth", 10.0, 100, "Cat")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 2)
        store.add_to_cart(user.user_id, "ISBN1", 3)
        
        cart = store.get_cart(user.user_id)
        assert cart[0].quantity == 5

    def test_remove_from_cart(self, store):
        store.add_book("ISBN1", "Book", "Auth", 10.0, 100, "Cat")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 2)
        store.remove_from_cart(user.user_id, "ISBN1")
        
        assert len(store.get_cart(user.user_id)) == 0

    def test_remove_from_cart_empty_raises_error(self, store):
        user = store.register_user("Alice", "alice@test.com", "pass")
        with pytest.raises(ValueError, match="Item not found in cart"):
            store.remove_from_cart(user.user_id, "ISBN1")

    def test_update_cart_quantity(self, store):
        store.add_book("ISBN1", "Book", "Auth", 10.0, 100, "Cat")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 2)
        store.update_cart_quantity(user.user_id, "ISBN1", 5)
        
        cart = store.get_cart(user.user_id)
        assert cart[0].quantity == 5

    def test_clear_cart(self, store):
        store.add_book("ISBN1", "Book", "Auth", 10.0, 100, "Cat")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 2)
        store.clear_cart(user.user_id)
        
        assert len(store.get_cart(user.user_id)) == 0


class TestOrderCreation:
    def test_create_order_success(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        store.add_book("ISBN2", "Book2", "Auth", 200.0, 100, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 1)
        store.add_to_cart(user.user_id, "ISBN2", 1)
        
        order = store.create_order(user.user_id)
        
        assert order.status == Order.STATUS_PENDING
        assert len(order.items) == 2
        assert order.total_amount == 300.0
        assert order.discount_amount == 0.0
        assert order.final_amount == 300.0
        
        # Stock reduced
        assert store.get_book("ISBN1").stock == 99
        assert store.get_book("ISBN2").stock == 99
        
        # Cart cleared
        assert len(store.get_cart(user.user_id)) == 0

    def test_create_order_with_discount_silver(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        # Upgrade to Silver
        store.add_points(user.user_id, 1000)
        
        store.add_to_cart(user.user_id, "ISBN1", 1)
        order = store.create_order(user.user_id)
        
        assert order.discount_amount == 5.0  # 100 * 0.05
        assert order.final_amount == 95.0

    def test_create_order_with_discount_gold(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        # Upgrade to Gold
        store.add_points(user.user_id, 5000)
        
        store.add_to_cart(user.user_id, "ISBN1", 1)
        order = store.create_order(user.user_id)
        
        assert order.discount_amount == 10.0  # 100 * 0.10
        assert order.final_amount == 90.0

    def test_create_order_empty_cart_raises_error(self, store):
        user = store.register_user("Alice", "alice@test.com", "pass")
        with pytest.raises(ValueError, match="Cart is empty"):
            store.create_order(user.user_id)

    def test_create_order_insufficient_stock_during_checkout(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 1, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 1)
        # Reduce stock manually to simulate race condition or previous purchase
        store.get_book("ISBN1").reduce_stock(1) 
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            store.create_order(user.user_id)


class TestPaymentAndCancellation:
    def test_pay_order_success(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 1)
        order = store.create_order(user.user_id)
        
        store.pay_order(order.order_id)
        
        assert order.status == Order.STATUS_PAID
        assert user.points == 100  # 100 yuan spent

    def test_pay_already_paid_order_raises_error(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 1)
        order = store.create_order(user.user_id)
        store.pay_order(order.order_id)
        
        with pytest.raises(ValueError, match="Cannot pay for order"):
            store.pay_order(order.order_id)

    def test_cancel_order_success(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 1)
        order = store.create_order(user.user_id)
        
        store.cancel_order(order.order_id)
        
        assert order.status == Order.STATUS_CANCELLED
        assert store.get_book("ISBN1").stock == 100  # Restored
        
        # Item back in cart
        cart = store.get_cart(user.user_id)
        assert len(cart) == 1
        assert cart[0].isbn == "ISBN1"
        assert cart[0].quantity == 1

    def test_cancel_pending_order_restores_stock_and_cart(self, store):
        # Same as above, ensuring logic holds
        store.add_book("ISBN1", "Book1", "Auth", 50.0, 10, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 2)
        order = store.create_order(user.user_id)
        
        store.cancel_order(order.order_id)
        
        assert store.get_book("ISBN1").stock == 10
        cart = store.get_cart(user.user_id)
        assert cart[0].quantity == 2

    def test_cancel_already_paid_order_raises_error(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        user = store.register_user("Alice", "alice@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 1)
        order = store.create_order(user.user_id)
        store.pay_order(order.order_id)
        
        with pytest.raises(ValueError, match="Cannot cancel order"):
            store.cancel_order(order.order_id)

    def test_get_order_not_found(self, store):
        with pytest.raises(ValueError, match="Order not found"):
            store.get_order("INVALID_ORDER_ID")


class TestSalesStats:
    def test_sales_stats_basic(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        store.add_book("ISBN2", "Book2", "Auth", 200.0, 100, "Tech")
        user1 = store.register_user("User1", "u1@test.com", "pass")
        user2 = store.register_user("User2", "u2@test.com", "pass")
        
        # User 1 buys 2 of Book1
        store.add_to_cart(user1.user_id, "ISBN1", 2)
        order1 = store.create_order(user1.user_id)
        store.pay_order(order1.order_id)
        
        # User 2 buys 1 of Book1 and 1 of Book2
        store.add_to_cart(user2.user_id, "ISBN1", 1)
        store.add_to_cart(user2.user_id, "ISBN2", 1)
        order2 = store.create_order(user2.user_id)
        store.pay_order(order2.order_id)
        
        stats = store.get_sales_stats()
        
        # Book1 sold 3 times, Book2 sold 1 time
        assert stats[0] == ("Book1", 3)
        assert stats[1] == ("Book2", 1)

    def test_sales_stats_filter_by_category(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        store.add_book("ISBN2", "Book2", "Auth", 200.0, 100, "Fiction")
        user = store.register_user("User1", "u1@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 5)
        store.add_to_cart(user.user_id, "ISBN2", 2)
        order = store.create_order(user.user_id)
        store.pay_order(order.order_id)
        
        tech_stats = store.get_sales_stats(category="Tech")
        assert len(tech_stats) == 1
        assert tech_stats[0] == ("Book1", 5)
        
        fiction_stats = store.get_sales_stats(category="Fiction")
        assert len(fiction_stats) == 1
        assert fiction_stats[0] == ("Book2", 2)
        
        # No books in other category
        other_stats = store.get_sales_stats(category="Other")
        assert len(other_stats) == 0

    def test_sales_stats_ignore_cancelled_orders(self, store):
        store.add_book("ISBN1", "Book1", "Auth", 100.0, 100, "Tech")
        user = store.register_user("User1", "u1@test.com", "pass")
        
        store.add_to_cart(user.user_id, "ISBN1", 5)
        order = store.create_order(user.user_id)
        store.cancel_order(order.order_id)
        
        stats = store.get_sales_stats()
        assert len(stats) == 0