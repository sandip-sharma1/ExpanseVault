import sys
import csv
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog, QDateEdit, QComboBox, QDialog
)
from PyQt6.QtCore import Qt, QDate
# Remove QtCharts import
# from PyQt6.QtCharts import QChart, QChartView, QPieSeries
import mysql.connector
from PyQt6.QtGui import QFont, QColor

# Add matplotlib imports
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Database configuration
"""
I recommand you configuring your MySQL database in your own way, but for testing purposes, I have included a default configuration here.
Make sure to update the DB_CONFIG dictionary with your actual database credentials and settings.
"""
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Root123@",  
    "database": "expensevault"
}

# --- Database Setup and Connection Functions ---

def get_db_connection():
    """Establish a connection to the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        QMessageBox.critical(None, "Database Error", f"Failed to connect: {e}")
        return None

def ensure_database():
    """Create the database if it doesn't exist."""
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Error creating database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def initialize_database():
    """Initialize tables for categories and expenses, adding missing columns if necessary."""
    print("\n--- INITIALIZING DATABASE TABLES ---")
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed in initialize_database()")
        return
    try:
        cursor = conn.cursor()
        
        # Check existing tables to identify any that might be mistakenly created
        print("Checking existing tables...")
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found tables: {tables}")
        
        # Create categories table if it doesn't exist
        print("Creating categories table if it doesn't exist")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL
            )
        """)
        
        # Check if there are tables that should be categories
        potential_categories = []
        for table in tables:
            # Skip our main tables
            if table not in ['categories', 'expenses', 'category_limits']:
                potential_categories.append(table)
                
        if potential_categories:
            print(f"Found {len(potential_categories)} tables that might be mistakenly created as tables instead of categories")
            
            # First, check if these categories already exist in the categories table
            for cat_name in potential_categories:
                cursor.execute("SELECT COUNT(*) FROM categories WHERE name = %s", (cat_name,))
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print(f"Adding '{cat_name}' to categories table")
                    try:
                        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (cat_name,))
                    except mysql.connector.Error as e:
                        print(f"Error adding '{cat_name}' to categories: {e}")
            
            # Now ask if user wants to drop these mistaken tables
            conn.commit()
            print("Added potential categories to the categories table")
        
        # Create expenses table if it doesn't exist
        print("Creating expenses table if it doesn't exist")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                date DATE NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)
        
        # Create category_limits table if it doesn't exist
        print("Creating category_limits table if it doesn't exist")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_limits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category_id INT NOT NULL,
                limit_amount DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        """)
        
        # Check and add category_id column to expenses if missing
        cursor.execute("SHOW COLUMNS FROM expenses LIKE 'category_id'")
        if not cursor.fetchone():
            print("Adding category_id column to expenses table")
            cursor.execute("""
                ALTER TABLE expenses
                ADD COLUMN category_id INT NOT NULL,
                ADD FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            """)
        
        conn.commit()
        print("Database tables initialized successfully")
    except mysql.connector.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()
        print("--- DATABASE INITIALIZATION COMPLETE ---\n")

def clean_database():
    """Clean up mistakenly created tables that should be categories."""
    print("\n--- CLEANING DATABASE ---")
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed in clean_database()")
        return False
        
    try:
        cursor = conn.cursor()
        
        # Check existing tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Filter out our main tables
        potential_categories = [t for t in tables if t not in ['categories', 'expenses', 'category_limits']]
        
        if not potential_categories:
            print("No tables to clean up")
            return True
            
        print(f"Found {len(potential_categories)} tables that appear to be mistakenly created categories:")
        for table in potential_categories:
            print(f"  - {table}")
            
        # Drop each mistaken table
        for table in potential_categories:
            try:
                print(f"Dropping table '{table}'")
                cursor.execute(f"DROP TABLE `{table}`")
            except mysql.connector.Error as e:
                print(f"Error dropping table '{table}': {e}")
                
        conn.commit()
        print("Database cleaned successfully")
        return True
    except mysql.connector.Error as e:
        print(f"Error cleaning database: {e}")
        return False
    finally:
        conn.close()
        print("--- DATABASE CLEANING COMPLETE ---\n")

def setup_database():
    """Set up the database and tables."""
    print("\n=== SETTING UP DATABASE ===")
    ensure_database()
    initialize_database()
    clean_database()
    print("=== DATABASE SETUP COMPLETE ===\n")

# --- Database Functions ---

def get_categories():
    """Retrieve all category names."""
    print("\n--- FETCHING CATEGORIES FROM DATABASE ---")
    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed in get_categories()")
        return []
    try:
        cursor = conn.cursor()
        # First check if the categories table exists
        cursor.execute("SHOW TABLES LIKE 'categories'")
        if not cursor.fetchone():
            print("Error: 'categories' table doesn't exist!")
            return []
            
        print("Executing query: SELECT name FROM categories ORDER BY name")
        cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(categories)} categories: {categories}")
        return categories
    except mysql.connector.Error as e:
        print(f"Database error in get_categories: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in get_categories: {e}")
        return []
    finally:
        conn.close()
        print("--- CATEGORY FETCH COMPLETE ---\n")

def add_category(name):
    """Add a new category."""
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
        conn.commit()
        return True, f"Category '{name}' added"
    except mysql.connector.Error as e:
        if e.errno == 1062:  # Duplicate entry
            return False, f"Category '{name}' already exists"
        return False, f"Error adding category: {e}"
    finally:
        conn.close()

def remove_category(name):
    """Remove a category and its expenses."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE name = %s", (name,))
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Error removing category: {e}")
        return False
    finally:
        conn.close()

def get_category_id(name):
    """Get the ID of a category by name."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except mysql.connector.Error as e:
        print(f"Error getting category id: {e}")
        return None
    finally:
        conn.close()

def get_expenses(category_name, start_date=None, end_date=None):
    """Retrieve expenses for a category with optional date filtering."""
    print(f"\n--- FETCHING EXPENSES ---")
    print(f"Category: {category_name}")
    print(f"Date range: {start_date} to {end_date}")
    
    conn = get_db_connection()
    if not conn:
        print("ERROR: Database connection failed in get_expenses")
        return [], 0
        
    try:
        cursor = conn.cursor()
        
        # First check if the category exists
        cursor.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
        category_result = cursor.fetchone()
        
        if not category_result:
            print(f"ERROR: Category '{category_name}' not found in database")
            return [], 0
            
        category_id = category_result[0]
        print(f"Found category ID: {category_id}")
        
        # Build and execute query to get expenses
        query = """
            SELECT e.id, e.amount, e.date
            FROM expenses e
            JOIN categories c ON e.category_id = c.id
            WHERE c.name = %s
        """
        params = [category_name]
        if start_date:
            query += " AND e.date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND e.date <= %s"
            params.append(end_date)
        query += " ORDER BY e.date DESC"
        
        print(f"Executing query: {query}")
        print(f"With parameters: {params}")
        
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        print(f"Fetched {len(expenses)} expense records")
        
        # Calculate total
        total_query = query.replace("e.id, e.amount, e.date", "SUM(e.amount)")
        cursor.execute(total_query, params)
        total_result = cursor.fetchone()
        total = total_result[0] or 0
        print(f"Total expenses: {total}")
        
        return expenses, total
    except mysql.connector.Error as e:
        print(f"Database error in get_expenses: {e}")
        return [], 0
    except Exception as e:
        print(f"Unexpected error in get_expenses: {e}")
        import traceback
        traceback.print_exc()
        return [], 0
    finally:
        conn.close()
        print("--- EXPENSE FETCHING COMPLETE ---\n")

def add_expense(category_name, amount, date):
    """Add a new expense.
    
    Args:
        category_name (str): Category name.
        amount (float): Expense amount.
        date (str): Date in YYYY-MM-DD format.

    Returns:
        tuple: (success, message)
    """
    category_id = get_category_id(category_name)
    if not category_id:
        return False, f"Category '{category_name}' does not exist"
    
    try:
        amount = float(amount)
        if amount <= 0:
            return False, "Amount must be positive"
    except (ValueError, TypeError):
        return False, "Invalid amount format"
    
    conn = get_db_connection()
    if not conn:
        return False, "Failed to connect to database"
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (category_id, amount, date) VALUES (%s, %s, %s)",
            (category_id, amount, date)
        )
        conn.commit()
        return True, "Expense added successfully"
    except mysql.connector.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()

def delete_expense(expense_id):
    """Delete an expense by ID."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as e:
        print(f"Error deleting expense: {e}")
        return False
    finally:
        conn.close()

def update_expense(expense_id, amount, date):
    """Update an existing expense with reliable transaction handling."""
    print("--- EXPENSE UPDATE START ---")
    print(f"Updating expense ID: {expense_id}")
    print(f"New amount: {amount}")
    print(f"New date: {date} (type: {type(date)})")
    
    # Ensure we have a valid connection
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Database connection established")
    except mysql.connector.Error as e:
        print(f"Connection error: {e}")
        return False
        
    try:
        # Format the date properly
        if isinstance(date, str):
            date_str = date
        else:
            date_str = date.strftime("%Y-%m-%d")
            
        print(f"Formatted date: {date_str}")
            
        # Create cursor
        cursor = conn.cursor()
        
        # Execute update query
        query = "UPDATE expenses SET amount = %s, date = %s WHERE id = %s"
        values = (float(amount), date_str, int(expense_id))
        
        print(f"Executing: {query} with values {values}")
        cursor.execute(query, values)
        
        # Explicitly commit the transaction
        conn.commit()
        print("Transaction committed")
        
        # Check if the update was successful
        if cursor.rowcount > 0:
            print(f"Successfully updated {cursor.rowcount} row(s)")
            return True
        else:
            print("Update failed: No rows affected")
            # Check if the expense exists
            cursor.execute("SELECT COUNT(*) FROM expenses WHERE id = %s", (expense_id,))
            count = cursor.fetchone()[0]
            if count == 0:
                print(f"Expense ID {expense_id} doesn't exist")
            return False
            
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("Connection closed")
        print("--- EXPENSE UPDATE END ---")

def get_category_totals():
    """Get total expenses per category for the pie chart."""
    conn = get_db_connection()
    if not conn:
        return {}
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.name, SUM(e.amount)
            FROM expenses e
            JOIN categories c ON e.category_id = c.id
            GROUP BY c.name
        """)
        return dict(cursor.fetchall())
    except mysql.connector.Error as e:
        print(f"Error fetching totals: {e}")
        return {}
    finally:
        conn.close()

# Add these functions for handling category limits after the get_category_totals function
def set_category_limit(category_id, limit_amount):
    """Set or update a spending limit for a category."""
    print(f"Setting limit for category ID {category_id} to Rs{limit_amount}")
    conn = get_db_connection()
    if not conn:
        print("Database connection failed in set_category_limit")
        return False, "Database connection failed"
    
    try:
        cursor = conn.cursor()
        
        # Check if limit already exists
        cursor.execute("SELECT id FROM category_limits WHERE category_id = %s", (category_id,))
        existing_limit = cursor.fetchone()
        
        if existing_limit:
            # Update existing limit
            print(f"Updating existing limit record {existing_limit[0]}")
            cursor.execute(
                "UPDATE category_limits SET limit_amount = %s WHERE category_id = %s",
                (limit_amount, category_id)
            )
            message = f"Spending limit updated to Rs{limit_amount:.2f}"
        else:
            # Insert new limit
            print(f"Inserting new limit record")
            cursor.execute(
                "INSERT INTO category_limits (category_id, limit_amount) VALUES (%s, %s)",
                (category_id, limit_amount)
            )
            message = f"Spending limit set to Rs{limit_amount:.2f}"
            
        conn.commit()
        print(f"Database committed successfully: {message}")
        return True, message
    except mysql.connector.Error as e:
        print(f"Database error in set_category_limit: {e}")
        return False, f"Database error: {e}"
    finally:
        conn.close()
        print("Database connection closed")

def get_category_limit(category_id):
    """Get the spending limit for a category."""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT limit_amount FROM category_limits WHERE category_id = %s", (category_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except mysql.connector.Error as e:
        print(f"Error getting category limit: {e}")
        return None
    finally:
        conn.close()

def get_category_spending(category_id, start_date=None, end_date=None):
    """Get the total spending for a category with optional date range."""
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        cursor = conn.cursor()
        query = "SELECT SUM(amount) FROM expenses WHERE category_id = %s"
        params = [category_id]
        
        if start_date:
            query += " AND date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND date <= %s"
            params.append(end_date)
            
        cursor.execute(query, params)
        result = cursor.fetchone()
        return float(result[0]) if result[0] else 0
    except mysql.connector.Error as e:
        print(f"Error getting category spending: {e}")
        return 0
    finally:
        conn.close()

def check_limit_exceeded(category_id, current_month=True):
    """Check if a category's spending exceeds its limit.
    
    Args:
        category_id: The category ID to check
        current_month: If True, only check the current month's expenses
        
    Returns:
        tuple: (exceeded, spent, limit) where exceeded is a boolean
    """
    limit = get_category_limit(category_id)
    if not limit:
        return False, 0, 0  # No limit set
    
    start_date = None
    end_date = None
    
    if current_month:
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
        
    # Calculate spending for the specified period (current month by default)
    spent = get_category_spending(category_id, start_date, end_date)
    return spent > limit, spent, limit

def get_all_category_limits_with_spending():
    """Get all categories with their limits and current spending."""
    print("Fetching all categories with limits and spending data")
    conn = get_db_connection()
    if not conn:
        print("Database connection failed in get_all_category_limits_with_spending")
        return []
    
    try:
        cursor = conn.cursor()
        
        # Get all categories
        print("Executing query to fetch all categories")
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        categories = cursor.fetchall()
        print(f"Found {len(categories)} categories in database")
        
        if not categories:
            print("No categories found in database")
            return []
            
        result = []
        today = datetime.now()
        start_date = datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
        
        for cat_id, cat_name in categories:
            print(f"Processing category {cat_name} (ID: {cat_id})")
            try:
                # Get limit if exists
                cursor.execute("SELECT limit_amount FROM category_limits WHERE category_id = %s", (cat_id,))
                limit_result = cursor.fetchone()
                limit = float(limit_result[0]) if limit_result else None
                print(f"  - Limit: {limit}")
                
                # Get current month spending
                cursor.execute(
                    "SELECT SUM(amount) FROM expenses WHERE category_id = %s AND date >= %s", 
                    (cat_id, start_date)
                )
                spent_result = cursor.fetchone()
                spent = float(spent_result[0]) if spent_result[0] else 0
                print(f"  - Spent: {spent}")
                
                # Check if exceeded
                exceeded = False
                if limit is not None:
                    exceeded = spent > limit
                    
                result.append({
                    'id': cat_id,
                    'name': cat_name,
                    'limit': limit,
                    'spent': spent,
                    'exceeded': exceeded
                })
            except Exception as e:
                print(f"Error processing category {cat_name}: {e}")
                # Continue with other categories even if one fails
            
        print(f"Returning data for {len(result)} categories")
        return result
    except mysql.connector.Error as e:
        print(f"Database error in get_all_category_limits_with_spending: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error in get_all_category_limits_with_spending: {e}")
        return []
    finally:
        conn.close()
        print("Database connection closed")

# --- UI Classes ---

class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expense Tracker")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: black; color: white;")
        
        # Store references to windows to prevent garbage collection
        self.category_window = None
        self.expense_view_window = None
        self.add_expense_window = None
        self.chart_window = None
        self.limit_window = None
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Expense Tracker")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Add alert indicator for exceeded limits
        self.alert_label = QLabel("")
        self.alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alert_label.setWordWrap(True)
        layout.addWidget(self.alert_label)
        self.check_for_limit_alerts()
        
        buttons = [
            ("View Expenses", self.open_view_categories),
            ("Add Expense", self.open_add_categories),
            ("Manage Limits", self.open_limits),
            ("View Chart", self.show_chart),
            ("Exit", self.close)
        ]
        for text, slot in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("background-color: #333333; color: white; border: 1px solid white;")
            btn.clicked.connect(slot)
            layout.addWidget(btn)
        
        central_widget.setLayout(layout)

    def check_for_limit_alerts(self):
        """Check for categories that have exceeded their limits and show alert."""
        exceeded_categories = []
        
        categories_with_limits = get_all_category_limits_with_spending()
        for cat in categories_with_limits:
            if cat['limit'] and cat['exceeded']:
                exceeded_categories.append(cat['name'])
        
        if exceeded_categories:
            if len(exceeded_categories) == 1:
                alert_text = f"⚠️ Warning: '{exceeded_categories[0]}' has exceeded its monthly budget limit!"
            else:
                cat_list = ", ".join(f"'{cat}'" for cat in exceeded_categories)
                alert_text = f"⚠️ Warning: {len(exceeded_categories)} categories have exceeded their monthly budget limits: {cat_list}"
                
            self.alert_label.setText(alert_text)
            self.alert_label.setStyleSheet("color: red; font-weight: bold; border: 2px solid red; padding: 10px; margin: 10px; border-radius: 5px; background-color: rgba(255, 0, 0, 0.1);")
        else:
            self.alert_label.setText("")
            self.alert_label.setStyleSheet("")

    def open_view_categories(self):
        self.category_window = CategorySelectionWindow(self.view_expenses)
        self.category_window.show()

    def open_add_categories(self):
        self.category_window = CategorySelectionWindow(self.add_expense)
        self.category_window.show()
        
    def open_limits(self):
        print("--- Opening CategoryLimitsWindow ---")
        try:
            self.limit_window = CategoryLimitsWindow()
            self.limit_window.show()
            print("--- CategoryLimitsWindow opened successfully ---")
        except Exception as e:
            print(f"Error opening CategoryLimitsWindow: {e}")
            import traceback
            traceback.print_exc()

    def view_expenses(self, category):
        self.expense_view_window = ExpenseViewWindow(category)
        self.expense_view_window.show()

    def add_expense(self, category):
        self.add_expense_window = AddExpenseWindow(category)
        self.add_expense_window.show()

    def show_chart(self):
        print("Opening chart window...")
        self.chart_window = ChartWindow()
        self.chart_window.show()

class CategorySelectionWindow(QWidget):
    """Window for selecting and managing categories."""
    def __init__(self, action):
        super().__init__()
        self.action = action
        self.setWindowTitle("Select Category")
        self.setGeometry(100, 100, 300, 400)
        self.setStyleSheet("background-color: black; color: white;")
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        
        # Add status label to show messages when no categories exist
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #FFCC66; margin: 10px;")
        self.layout.addWidget(self.status_label)
        
        self.update_categories()
        
        add_btn = QPushButton("Add Category")
        add_btn.setStyleSheet("background-color: #333333; color: white; border: 1px solid white;")
        add_btn.clicked.connect(self.add_category)
        self.layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Category")
        remove_btn.setStyleSheet("background-color: #333333; color: white; border: 1px solid white;")
        remove_btn.clicked.connect(self.remove_category)
        self.layout.addWidget(remove_btn)
        
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet("background-color: #333333; color: white; border: 1px solid white;")
        back_btn.clicked.connect(self.close)
        self.layout.addWidget(back_btn)
        
        self.setLayout(self.layout)

    def update_categories(self):
        print("Updating category selection window")
        # Clear existing category buttons
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if isinstance(widget, QPushButton) and widget.text() not in ["Add Category", "Remove Category", "Back"]:
                self.layout.removeWidget(widget)
                widget.deleteLater()
                
        # Get categories from database
        categories = get_categories()
        
        if not categories:
            self.status_label.setText("No categories found. Please add a category first.")
            self.status_label.setStyleSheet("color: #FF9966; font-size: 12pt; margin: 20px;")
            print("No categories found to display")
            return
        else:
            self.status_label.setText("")
            
        print(f"Adding {len(categories)} category buttons to window")
        
        # Create buttons for each category
        for category in categories:
            btn = QPushButton(category)
            btn.setStyleSheet("background-color: #333333; color: white; border: 1px solid white;")
            btn.clicked.connect(lambda checked, c=category: self.select_category(c))
            self.layout.insertWidget(0, btn)

    def select_category(self, category):
        self.action(category)
        self.close()

    def add_category(self):
        name, ok = QInputDialog.getText(self, "Add Category", "Enter category name:")
        if ok and name.strip():
            success, message = add_category(name.strip())
            if success:
                self.update_categories()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)

    def remove_category(self):
        categories = get_categories()
        if not categories:
            QMessageBox.information(self, "Info", "No categories to remove")
            return
        category, ok = QInputDialog.getItem(self, "Remove Category", "Select category:", categories, 0, False)
        if ok:
            reply = QMessageBox.question(self, "Confirm", f"Delete '{category}' and all its expenses?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes and remove_category(category):
                self.update_categories()
                QMessageBox.information(self, "Success", f"Deleted '{category}'")

class ExpenseViewWindow(QWidget):
    """Window for viewing and managing expenses."""
    def __init__(self, category):
        print(f"--- Initializing ExpenseViewWindow for category: {category} ---")
        super().__init__()
        self.category = category
        self.setWindowTitle(f"{category} Expenses")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: black; color: white;")
        self.edit_window = None  # Store reference to edit window
        
        try:
            self.init_ui()
            print("--- ExpenseViewWindow initialized successfully ---")
        except Exception as e:
            print(f"ERROR initializing ExpenseViewWindow: {e}")
            import traceback
            traceback.print_exc()
            # Show error message directly on the window
            error_layout = QVBoxLayout()
            error_label = QLabel(f"Error loading expense view: {str(e)}")
            error_label.setStyleSheet("color: red; background-color: black; padding: 20px;")
            error_label.setWordWrap(True)
            error_layout.addWidget(error_label)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.close)
            error_layout.addWidget(close_btn)
            
            self.setLayout(error_layout)

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Add a header with category name and limit info
        self.category_id = get_category_id(self.category)
        self.limit_label = QLabel()
        self.update_limit_info()
        layout.addWidget(self.limit_label)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Start Date:"))
        
        # Default to first day of current month instead of a month ago
        current_date = QDate.currentDate()
        first_of_month = QDate(current_date.year(), current_date.month(), 1)
        self.start_date = QDateEdit(first_of_month)
        self.start_date.setStyleSheet("background-color: #333333; color: white;")
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("End Date:"))
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setStyleSheet("background-color: #333333; color: white;")
        filter_layout.addWidget(self.end_date)
        
        # Add a "Current Month" button for quick filtering
        current_month_btn = QPushButton("Current Month")
        current_month_btn.setStyleSheet("background-color: #333333; color: white;")
        current_month_btn.clicked.connect(self.set_current_month)
        filter_layout.addWidget(current_month_btn)
        
        filter_btn = QPushButton("Filter")
        filter_btn.setStyleSheet("background-color: #333333; color: white;")
        filter_btn.clicked.connect(self.update_table)
        filter_layout.addWidget(filter_btn)
        layout.addLayout(filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Amount", "Date", "Edit", "Delete"])
        self.table.setStyleSheet("background-color: black; color: white; border: 1px solid white;")
        layout.addWidget(self.table)
        
        self.total_label = QLabel("Total: Rs0.00")
        layout.addWidget(self.total_label)
        
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export to CSV")
        export_btn.setStyleSheet("background-color: #333333; color: white;")
        export_btn.clicked.connect(self.export_to_csv)
        button_layout.addWidget(export_btn)
        
        set_limit_btn = QPushButton("Set Limit")
        set_limit_btn.setStyleSheet("background-color: #333333; color: white;")
        set_limit_btn.clicked.connect(self.set_category_limit)
        button_layout.addWidget(set_limit_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #333333; color: white;")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.update_table()
        
    def update_limit_info(self):
        """Update the limit information display."""
        print(f"Updating limit info for category: {self.category}")
        try:
            if not self.category_id:
                print(f"No category ID found for {self.category}")
                self.limit_label.setText(f"Category: {self.category}")
                return
                
            print(f"Found category ID: {self.category_id}, checking limit...")
            # When checking limit exceeded, we still want to show all expenses based on the filter
            # so we pass current_month=True just for the limit display, but not for expense fetching
            exceeded, spent, limit = check_limit_exceeded(self.category_id)
            print(f"Limit check result: exceeded={exceeded}, spent={spent}, limit={limit}")
            
            if limit:
                percentage = (spent / limit) * 100 if limit > 0 else 0
                
                if exceeded:
                    style = "color: red; font-weight: bold;"
                    status = f"EXCEEDED! (Rs{spent-limit:.2f} over)"
                elif percentage >= 80:
                    style = "color: orange; font-weight: bold;"
                    status = f"WARNING! ({percentage:.1f}% used)"
                else:
                    style = "color: green; font-weight: bold;"
                    status = f"{percentage:.1f}% used"
                
                self.limit_label.setText(
                    f"Category: {self.category} | " 
                    f"Monthly Limit: Rs{limit:.2f} | "
                    f"Spent: Rs{spent:.2f} | {status}"
                )
                self.limit_label.setStyleSheet(style)
            else:
                self.limit_label.setText(
                    f"Category: {self.category} | "
                    f"No monthly limit set | "
                    f"Spent this month: Rs{spent:.2f}"
                )
                self.limit_label.setStyleSheet("color: white;")
            print("Limit info updated successfully")
        except Exception as e:
            print(f"ERROR in update_limit_info: {e}")
            import traceback
            traceback.print_exc()
            # Set a safe default if there's an error
            self.limit_label.setText(f"Category: {self.category}")
            self.limit_label.setStyleSheet("color: white;")
        
    def set_category_limit(self):
        """Open dialog to set a spending limit for this category."""
        if not self.category_id:
            QMessageBox.critical(self, "Error", "Could not find category ID")
            return
            
        current_limit = get_category_limit(self.category_id) or 0
        
        limit, ok = QInputDialog.getDouble(
            self, 
            "Set Monthly Limit", 
            f"Set monthly spending limit for {self.category}:",
            current_limit,
            0,
            1000000,
            2
        )
        
        if ok:
            success, message = set_category_limit(self.category_id, limit)
            if success:
                self.update_limit_info()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)

    def export_to_csv(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        expenses, _ = get_expenses(self.category, start, end)
        with open(f"{self.category}_expenses.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Amount", "Date"])
            for e in expenses:
                writer.writerow([e[0], e[1], e[2].strftime("%Y-%m-%d")])
        QMessageBox.information(self, "Success", "Exported to CSV")

    def update_table(self):
        """Update the expenses table with filtered data."""
        print("--- UPDATING EXPENSE TABLE ---")
        try:
            # Get date range from filters
            start = self.start_date.date().toString("yyyy-MM-dd")
            end = self.end_date.date().toString("yyyy-MM-dd")
            print(f"Date range: {start} to {end}")
            
            # Get expenses for the selected category and date range
            print(f"Getting expenses for category: {self.category}")
            expenses, total = get_expenses(self.category, start, end)
            print(f"Retrieved {len(expenses)} expenses, total: {total}")
            
            # Update the limit info in case it changed
            print("Updating limit info...")
            self.update_limit_info()
            
            # Clear the table and set row count
            print("Setting up table...")
            self.table.clearContents()
            self.table.setRowCount(len(expenses))
            
            # Populate the table with expense data
            print(f"Populating table with {len(expenses)} rows...")
            for i, (id_, amount, date) in enumerate(expenses):
                print(f"Row {i}: ID={id_}, Amount={amount}, Date={date}")
                
                # Make sure all data is properly converted to strings
                id_item = QTableWidgetItem(str(id_))
                amount_item = QTableWidgetItem(f"Rs{amount:.2f}")
                
                # Ensure date is properly formatted
                if isinstance(date, datetime):
                    date_str = date.strftime("%Y-%m-%d")
                else:
                    date_str = str(date)
                date_item = QTableWidgetItem(date_str)
                
                # Add items to table with proper flags
                self.table.setItem(i, 0, id_item)
                self.table.setItem(i, 1, amount_item)
                self.table.setItem(i, 2, date_item)
                
                # Create edit button
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("background-color: #3357FF; color: white;")
                edit_btn.clicked.connect(lambda checked, eid=id_, amt=amount, d=date: self.edit_expense(eid, amt, d))
                self.table.setCellWidget(i, 3, edit_btn)
                
                # Create delete button
                del_btn = QPushButton("Delete")
                del_btn.setStyleSheet("background-color: #FF5733; color: white;")
                del_btn.clicked.connect(lambda checked, eid=id_: self.delete_expense(eid))
                self.table.setCellWidget(i, 4, del_btn)
            
            # Update total label
            self.total_label.setText(f"Total: Rs{total:.2f}")
            print("--- TABLE UPDATE COMPLETE ---")
            
        except Exception as e:
            print(f"ERROR updating expense table: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error message to user
            error_msg = f"Failed to update expenses: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            
            # Set fallback empty table
            self.table.clearContents()
            self.table.setRowCount(0)
            self.total_label.setText("Total: Rs0.00")
    
    def edit_expense(self, expense_id, amount, date):
        """Open a dialog to edit an expense."""
        try:
            # Create and show edit window
            dialog = QDialog(self)
            dialog.setWindowTitle("Edit Expense")
            dialog.setStyleSheet("background-color: black; color: white;")
            dialog.setMinimumWidth(300)
            
            # Create layout
            layout = QVBoxLayout()
            
            # Add amount field
            layout.addWidget(QLabel("Amount:"))
            amount_edit = QLineEdit(str(amount))
            amount_edit.setStyleSheet("background-color: #333333; color: white;")
            layout.addWidget(amount_edit)
            
            # Add date field
            layout.addWidget(QLabel("Date:"))
            
            # Convert string date to QDate if necessary
            if isinstance(date, str):
                qdate = QDate.fromString(date, "yyyy-MM-dd")
            elif isinstance(date, datetime):
                qdate = QDate(date.year, date.month, date.day)
            else:
                qdate = QDate.currentDate()
                
            date_edit = QDateEdit(qdate)
            date_edit.setStyleSheet("background-color: #333333; color: white;")
            date_edit.setCalendarPopup(True)
            layout.addWidget(date_edit)
            
            # Add button layout
            button_layout = QHBoxLayout()
            
            save_btn = QPushButton("Save")
            save_btn.setStyleSheet("background-color: #33FF57; color: black;")
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setStyleSheet("background-color: #FF5733; color: white;")
            
            button_layout.addWidget(save_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            
            # Connect buttons
            save_btn.clicked.connect(lambda: self.save_edited_expense(dialog, expense_id, amount_edit, date_edit))
            cancel_btn.clicked.connect(dialog.reject)
            
            # Show dialog
            dialog.exec()
            
        except Exception as e:
            print(f"Error opening edit dialog: {e}")
            QMessageBox.critical(self, "Error", f"Could not open edit window: {str(e)}")
    
    def save_edited_expense(self, dialog, expense_id, amount_edit, date_edit):
        """Save changes to an edited expense."""
        try:
            # Get new values
            new_amount = float(amount_edit.text())
            if new_amount <= 0:
                QMessageBox.warning(dialog, "Invalid Amount", "Amount must be greater than zero")
                return
                
            new_date = date_edit.date().toString("yyyy-MM-dd")
            
            # Update expense in database
            if update_expense(expense_id, new_amount, new_date):
                dialog.accept()
                self.update_table()
                QMessageBox.information(self, "Success", "Expense updated successfully")
            else:
                QMessageBox.critical(dialog, "Error", "Failed to update expense")
        except ValueError:
            QMessageBox.warning(dialog, "Invalid Input", "Please enter a valid number for amount")
        except Exception as e:
            print(f"Error saving edited expense: {e}")
            QMessageBox.critical(dialog, "Error", f"Error: {str(e)}")
    
    def delete_expense(self, expense_id):
        """Delete an expense after confirmation."""
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this expense?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if delete_expense(expense_id):
                self.update_table()
                QMessageBox.information(self, "Success", "Expense deleted successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to delete expense")

    def set_current_month(self):
        """Set the date filters to the current month and update the table."""
        current_date = QDate.currentDate()
        first_of_month = QDate(current_date.year(), current_date.month(), 1)
        
        # Set the dates
        self.start_date.setDate(first_of_month)
        self.end_date.setDate(current_date)
        
        # Update the table to reflect the new date range
        self.update_table()

class AddExpenseWindow(QWidget):
    """Window for adding new expenses."""
    def __init__(self, category):
        print(f"--- Initializing AddExpenseWindow for category: {category} ---")
        super().__init__()
        self.category = category
        self.setWindowTitle(f"Add - {category}")
        self.setGeometry(100, 100, 300, 200)
        self.setStyleSheet("background-color: black; color: white;")
        
        try:
            self.init_ui()
            print("--- AddExpenseWindow initialized successfully ---")
        except Exception as e:
            print(f"ERROR initializing AddExpenseWindow: {e}")
            import traceback
            traceback.print_exc()
            # Show error message directly on the window
            error_layout = QVBoxLayout()
            error_label = QLabel(f"Error loading add expense window: {str(e)}")
            error_label.setStyleSheet("color: red; background-color: black; padding: 20px;")
            error_label.setWordWrap(True)
            error_layout.addWidget(error_label)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.close)
            error_layout.addWidget(close_btn)
            
            self.setLayout(error_layout)

    def init_ui(self):
        print(f"Setting up UI for category: {self.category}")
        layout = QVBoxLayout()
        
        # Add limit information at the top
        try:
            category_id = get_category_id(self.category)
            print(f"Retrieved category ID: {category_id}")
            if category_id:
                limit = get_category_limit(category_id)
                spent = get_category_spending(category_id, datetime.now().strftime("%Y-%m-01"), None)
                print(f"Retrieved limit: {limit}, spent: {spent}")
                
                # Convert values to float to ensure consistent types
                if limit is not None:
                    limit = float(limit)
                spent = float(spent)
                
                if limit:
                    remaining = limit - spent
                    percentage = (spent / limit) * 100
                    limit_text = f"Monthly limit: Rs{limit:.2f}\nSpent: Rs{spent:.2f} ({percentage:.1f}%)\nRemaining: Rs{remaining:.2f}"
                    
                    if spent > limit:
                        limit_color = "red"
                    elif spent >= 0.8 * limit:
                        limit_color = "orange"
                    else:
                        limit_color = "green"
                else:
                    limit_text = f"No monthly limit set\nSpent this month: Rs{spent:.2f}"
                    limit_color = "white"
                    
                limit_info = QLabel(limit_text)
                limit_info.setStyleSheet(f"color: {limit_color}; font-weight: bold; margin-bottom: 10px;")
                layout.addWidget(limit_info)
        except Exception as e:
            print(f"Error displaying limit information: {e}")
            # Add a simple label instead of the detailed limit info
            layout.addWidget(QLabel(f"Adding expense for: {self.category}"))
        
        layout.addWidget(QLabel(f"Amount for {self.category}:"))
        self.amount_entry = QLineEdit()
        self.amount_entry.setStyleSheet("background-color: #333333; color: white;")
        layout.addWidget(self.amount_entry)
        
        layout.addWidget(QLabel("Date:"))
        self.date_entry = QDateEdit(QDate.currentDate())
        self.date_entry.setStyleSheet("background-color: #333333; color: white;")
        self.date_entry.setCalendarPopup(True)  # Add calendar popup for better UX
        layout.addWidget(self.date_entry)
        
        submit_btn = QPushButton("Submit")
        submit_btn.setStyleSheet("background-color: #333333; color: white;")
        submit_btn.clicked.connect(self.submit)
        layout.addWidget(submit_btn)
        
        # Add a cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #444444; color: white;")
        cancel_btn.clicked.connect(self.close)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)
        print("AddExpenseWindow UI setup complete")

    def submit(self):
        try:
            amount_text = self.amount_entry.text().strip()
            if not amount_text:
                raise ValueError("Amount cannot be empty")
            
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            date = self.date_entry.date().toString("yyyy-MM-dd")
            print(f"Submitting expense: {self.category}, Rs{amount}, {date}")
            
            success, message = add_expense(self.category, amount, date)
            if success:
                QMessageBox.information(self, "Success", message)
                
                # Check if limit is exceeded after adding expense
                category_id = get_category_id(self.category)
                if category_id:
                    exceeded, spent, limit = check_limit_exceeded(category_id)
                    
                    # Ensure consistent types for calculations
                    if limit:
                        limit = float(limit)
                    spent = float(spent)
                    
                    if exceeded and limit > 0:
                        over_amount = spent - limit
                        percentage = (spent / limit) * 100
                        
                        alert_msg = QMessageBox(self)
                        alert_msg.setIcon(QMessageBox.Icon.Warning)
                        alert_msg.setWindowTitle("⚠️ SPENDING LIMIT EXCEEDED ⚠️")
                        alert_msg.setText(f"<h3 style='color: red;'>Budget Alert!</h3>")
                        alert_msg.setInformativeText(
                            f"<p>Your spending for <b>{self.category}</b> has exceeded the monthly limit!</p>"
                            f"<p>Limit: <b>Rs{limit:.2f}</b><br>"
                            f"Current spending: <b>Rs{spent:.2f}</b> ({percentage:.1f}%)<br>"
                            f"Over by: <b>Rs{over_amount:.2f}</b></p>"
                            f"<p>Consider adjusting your spending or increasing your budget.</p>"
                        )
                        alert_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                        alert_msg.setDefaultButton(QMessageBox.StandardButton.Ok)
                        alert_msg.exec()
                
                self.close()
            else:
                QMessageBox.critical(self, "Error", message)
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
        except Exception as e:
            print(f"Unexpected error in submit: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

class ChartWindow(QWidget):
    """Window for displaying expense distribution pie chart using matplotlib."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expense Distribution")
        self.setGeometry(100, 100, 800, 600)  # Larger size for better visibility
        self.setStyleSheet("background-color: black; color: white;")
        self.init_ui()

    def init_ui(self):
        print("Initializing chart window UI...")
        layout = QVBoxLayout()
        
        # Add a status label at the top with better styling
        self.status_label = QLabel("Loading expense chart...")
        self.status_label.setStyleSheet("color: white; font-weight: bold; font-size: 14pt; margin-bottom: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        try:
            # First check if there are any categories
            categories = get_categories()
            if not categories:
                self.status_label.setText("No expense categories found")
                message = QLabel("Please add expense categories before viewing the chart.")
                message.setStyleSheet("color: #FF9966; font-size: 12pt; margin: 20px;")
                message.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(message)
            else:
                # Try to get category totals
                totals = get_category_totals()
                print(f"Retrieved category totals: {totals}")
                
                if not totals:
                    self.status_label.setText("No expenses found in any category")
                    message = QLabel("Add some expenses to see the expense distribution chart.")
                    message.setStyleSheet("color: #FF9966; font-size: 12pt; margin: 20px;")
                    message.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(message)
                else:
                    # Create matplotlib chart
                    self.status_label.setText("Expense Distribution Chart")
                    print("Creating matplotlib pie chart...")
                    
                    # Convert dictionary to lists for matplotlib
                    categories = list(totals.keys())
                    amounts = [float(val) for val in totals.values()]
                    
                    # Create the figure and canvas
                    self.figure = Figure(figsize=(8, 6), facecolor='black')
                    self.canvas = FigureCanvas(self.figure)
                    
                    # Create the pie chart
                    ax = self.figure.add_subplot(111)
                    ax.set_facecolor('black')
                    
                    # Vibrant colors for the pie slices
                    colors = [
                        "#FF5733", "#33FF57", "#3357FF", "#FF33A8", "#33FFF5",
                        "#FFD133", "#B133FF", "#FF8333", "#33FFBD", "#7BFF33"
                    ]
                    
                    # Create the pie chart with percentages
                    wedges, texts, autotexts = ax.pie(
                        amounts, 
                        labels=categories,
                        autopct='%1.1f%%',
                        startangle=90,
                        colors=colors,
                        explode=[0.1 if float(amount)/sum(amounts) > 0.2 else 0 for amount in amounts],
                        shadow=True,
                        textprops={'color': 'white', 'weight': 'bold'}
                    )
                    
                    # Customize the percentage text
                    for autotext in autotexts:
                        autotext.set_size(10)
                        autotext.set_weight('bold')
                        
                    # Add a title
                    ax.set_title('Expense Distribution by Category', color='white', fontsize=16, pad=20)
                    
                    # Add total amount information
                    total_amount = sum(amounts)
                    total_text = f"Total Expenses: Rs{total_amount:.2f}"
                    self.figure.text(0.5, 0.02, total_text, ha='center', color='white', fontsize=12)
                    
                    # Equal aspect ratio ensures that pie is drawn as a circle
                    ax.axis('equal')
                    
                    # Add the canvas to the layout
                    layout.addWidget(self.canvas)
                    print("Matplotlib chart created successfully")
                    
                    # Force the canvas to update
                    self.canvas.draw()
        
        except Exception as e:
            print(f"Error creating chart: {e}")
            self.status_label.setText("Error Creating Chart")
            error_msg = QLabel(f"An error occurred while creating the chart:")
            error_details = QLabel(f"{str(e)}")
            tech_note = QLabel("Check the console for technical details.")
            
            error_msg.setStyleSheet("color: #FF6666; font-size: 12pt; margin-top: 20px;")
            error_details.setStyleSheet("color: #FF9999; font-size: 11pt; margin: 5px 20px;")
            tech_note.setStyleSheet("color: #CCCCCC; font-size: 10pt;")
            
            error_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tech_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            layout.addWidget(error_msg)
            layout.addWidget(error_details)
            layout.addWidget(tech_note)
        
        # Add close button with better styling
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            background-color: #333333; 
            color: white;
            padding: 8px;
            font-size: 12pt;
            margin-top: 15px;
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        print("Chart window UI initialization complete")

# Add the CategoryLimitsWindow class for managing spending limits
class CategoryLimitsWindow(QWidget):
    """Window for viewing and setting category spending limits."""
    def __init__(self):
        print("--- CategoryLimitsWindow constructor start ---")
        super().__init__()
        self.setWindowTitle("Category Spending Limits")
        self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet("background-color: black; color: white;")
        try:
            self.init_ui()
            print("--- CategoryLimitsWindow initialized successfully ---")
        except Exception as e:
            print(f"Error in CategoryLimitsWindow initialization: {e}")
            import traceback
            traceback.print_exc()
        
    def init_ui(self):
        print("--- CategoryLimitsWindow init_ui start ---")
        layout = QVBoxLayout()
        
        # Add header label
        header = QLabel("Monthly Spending Limits by Category")
        header.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Add instructions
        instructions = QLabel(
            "Set monthly spending limits for each category. "
            "You'll receive alerts when your spending approaches or exceeds these limits."
        )
        instructions.setStyleSheet("color: #CCCCCC; margin-bottom: 15px;")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Add a status label to display errors or info
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #FFCC66; margin: 10px;")
        layout.addWidget(self.status_label)
        
        # Create the table
        print("--- Creating table widget ---")
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Category", "Current Limit", "Monthly Spending", "Status", "Actions"])
        self.table.setStyleSheet("background-color: black; color: white; border: 1px solid white;")
        layout.addWidget(self.table)
        
        button_layout = QHBoxLayout()
        
        # Add button for creating a new category
        add_category_btn = QPushButton("Add Category")
        add_category_btn.setStyleSheet("background-color: #333333; color: white;")
        add_category_btn.clicked.connect(self.add_category)
        button_layout.addWidget(add_category_btn)
        
        # Add button for setting all limits
        set_all_btn = QPushButton("Set All Limits")
        set_all_btn.setStyleSheet("background-color: #333333; color: white;")
        set_all_btn.clicked.connect(self.set_all_limits)
        button_layout.addWidget(set_all_btn)
        
        # Add button for saving all changes
        save_all_btn = QPushButton("Save All Changes")
        save_all_btn.setStyleSheet("background-color: #3366CC; color: white; font-weight: bold;")
        save_all_btn.clicked.connect(self.save_all_changes)
        button_layout.addWidget(save_all_btn)
        
        # Add button for refreshing data
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet("background-color: #333333; color: white;")
        refresh_btn.clicked.connect(self.update_table)
        button_layout.addWidget(refresh_btn)
        
        # Add button for closing
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #333333; color: white;")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        print("--- About to update table ---")
        self.update_table()
        print("--- CategoryLimitsWindow init_ui complete ---")
    
    def save_all_changes(self):
        """Save all changes to category limits."""
        print("Saving all category limit changes...")
        success_count = 0
        error_count = 0
        
        # Get the current row count
        row_count = self.table.rowCount()
        
        # Loop through all rows
        for row in range(row_count):
            try:
                # Get category ID from the first column (assumed to be hidden or stored as user data)
                category_name = self.table.item(row, 0).text()
                category_id = get_category_id(category_name)
                
                if not category_id:
                    print(f"Could not find ID for category: {category_name}")
                    continue
                
                # Get the current limit text from the second column
                limit_item = self.table.item(row, 1)
                if not limit_item:
                    continue
                    
                limit_text = limit_item.text()
                
                # Convert text to a number, handling "Not set" case
                if limit_text == "Not set":
                    limit_amount = 0
                else:
                    # Remove Rs and convert to float
                    limit_amount = float(limit_text.replace('Rs', '').strip())
                
                # Save the limit to the database
                success, message = set_category_limit(category_id, limit_amount)
                
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    print(f"Error saving limit for {category_name}: {message}")
            
            except Exception as e:
                error_count += 1
                print(f"Error processing row {row}: {e}")
        
        # Show a message with the results
        if error_count == 0:
            QMessageBox.information(
                self, 
                "Success", 
                f"Successfully saved limits for {success_count} categories."
            )
        else:
            QMessageBox.warning(
                self, 
                "Partial Success", 
                f"Saved {success_count} categories, but encountered {error_count} errors.\n"
                f"See console for details."
            )
        
        # Refresh the table to show the latest data
        self.update_table()
        
    def add_category(self):
        """Add a new category."""
        name, ok = QInputDialog.getText(self, "Add Category", "Enter category name:")
        if ok and name.strip():
            success, message = add_category(name.strip())
            if success:
                QMessageBox.information(self, "Success", message)
                self.update_table()
            else:
                QMessageBox.critical(self, "Error", message)
        
    def update_table(self):
        """Update the table with category limits and spending info."""
        print("--- update_table method start ---")
        try:
            categories_data = get_all_category_limits_with_spending()
            print(f"Retrieved {len(categories_data)} categories with limit data")
            
            if not categories_data:
                self.status_label.setText("No categories found. Add a category to set spending limits.")
                self.status_label.setStyleSheet("color: #FF9966; font-size: 12pt; margin: 20px;")
                self.table.setRowCount(0)
                print("No categories to display in the table")
                return
            else:
                self.status_label.setText("")
            
            self.table.setRowCount(len(categories_data))
            
            for i, cat in enumerate(categories_data):
                # Category name
                name_item = QTableWidgetItem(cat['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make name non-editable
                self.table.setItem(i, 0, name_item)
                
                # Current limit - make this editable
                limit_text = f"Rs{cat['limit']:.2f}" if cat['limit'] else "Not set"
                limit_item = QTableWidgetItem(limit_text)
                if cat['limit'] is None:
                    limit_item.setToolTip("Double-click to set a limit")
                else:
                    limit_item.setToolTip("Double-click to edit limit")
                self.table.setItem(i, 1, limit_item)
                
                # Monthly spending - not editable
                spent_item = QTableWidgetItem(f"Rs{cat['spent']:.2f}")
                spent_item.setFlags(spent_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(i, 2, spent_item)
                
                # Status - not editable
                status_item = QTableWidgetItem()
                status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if cat['limit'] is None:
                    status_text = "No limit set"
                    status_color = "white"
                elif cat['exceeded']:
                    over_amount = cat['spent'] - cat['limit']
                    status_text = f"EXCEEDED by Rs{over_amount:.2f}"
                    status_color = "red"
                elif cat['spent'] >= 0.8 * (cat['limit'] or 0):
                    percentage = (cat['spent'] / cat['limit']) * 100
                    status_text = f"WARNING: {percentage:.1f}% used"
                    status_color = "orange"
                else:
                    percentage = (cat['spent'] / cat['limit']) * 100 if cat['limit'] and cat['limit'] > 0 else 0
                    status_text = f"{percentage:.1f}% of limit"
                    status_color = "green"
                    
                status_item.setText(status_text)
                status_item.setForeground(QColor(status_color))
                self.table.setItem(i, 3, status_item)
                
                # Actions button layout to contain multiple buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(2, 2, 2, 2)
                
                # Set limit button
                set_btn = QPushButton("Set Limit")
                set_btn.setStyleSheet("background-color: #333333; color: white;")
                set_btn.clicked.connect(lambda checked, cat_id=cat['id'], cat_name=cat['name']: 
                                    self.set_limit(cat_id, cat_name))
                action_layout.addWidget(set_btn)
                
                # Clear limit button (if limit exists)
                if cat['limit'] is not None:
                    clear_btn = QPushButton("Clear")
                    clear_btn.setStyleSheet("background-color: #444444; color: white;")
                    clear_btn.clicked.connect(lambda checked, cat_id=cat['id'], cat_name=cat['name']: 
                                        self.clear_limit(cat_id, cat_name))
                    action_layout.addWidget(clear_btn)
                
                self.table.setCellWidget(i, 4, action_widget)
            
            # Connect the cellDoubleClicked signal to handle inline editing
            self.table.cellDoubleClicked.connect(self.handle_cell_double_click)
            
            # Resize columns to fit content
            self.table.resizeColumnsToContents()
            print("--- update_table method complete ---")
        except Exception as e:
            print(f"Error in update_table: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Error loading categories: {str(e)}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def handle_cell_double_click(self, row, column):
        """Handle double-click on table cells for inline editing."""
        # Only handle limit column (column 1)
        if column != 1:
            return
            
        # Get category information
        category_name = self.table.item(row, 0).text()
        category_id = get_category_id(category_name)
        
        if not category_id:
            QMessageBox.critical(self, "Error", f"Could not find ID for category: {category_name}")
            return
            
        # Open dialog to edit limit
        self.set_limit(category_id, category_name)
        
    def set_limit(self, category_id, category_name):
        """Open dialog to set a spending limit for the selected category."""
        current_limit = get_category_limit(category_id) or 0
        
        limit, ok = QInputDialog.getDouble(
            self, 
            "Set Monthly Limit", 
            f"Set monthly spending limit for {category_name}:",
            current_limit,
            0,
            1000000,
            2
        )
        
        if ok:
            success, message = set_category_limit(category_id, limit)
            if success:
                QMessageBox.information(self, "Success", message)
                self.update_table()
            else:
                QMessageBox.critical(self, "Error", message)
                
    def clear_limit(self, category_id, category_name):
        """Clear the spending limit for the selected category."""
        reply = QMessageBox.question(
            self, 
            "Confirm", 
            f"Are you sure you want to remove the spending limit for '{category_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = set_category_limit(category_id, 0)
            if success:
                QMessageBox.information(self, "Success", f"Removed spending limit for '{category_name}'")
                self.update_table()
            else:
                QMessageBox.critical(self, "Error", message)
                
    def set_all_limits(self):
        """Set the same limit for all categories."""
        limit, ok = QInputDialog.getDouble(
            self, 
            "Set All Limits", 
            "Set the same monthly spending limit for all categories:",
            0,
            0,
            1000000,
            2
        )
        
        if ok:
            categories_data = get_all_category_limits_with_spending()
            
            success_count = 0
            error_count = 0
            for cat in categories_data:
                success, message = set_category_limit(cat['id'], limit)
                if success:
                    success_count += 1
                else:
                    error_count += 1
                    print(f"Error setting limit for {cat['name']}: {message}")
            
            if error_count == 0:
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Set Rs{limit:.2f} spending limit for all {success_count} categories"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Partial Success", 
                    f"Set limit for {success_count} categories, but encountered {error_count} errors.\n"
                    f"See console for details."
                )
                
            self.update_table()

# --- Main Execution ---

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Setup the database with more visibility
    print("Starting Expense Tracker application...")
    
    # Create loading dialog
    loading_dialog = QDialog()
    loading_dialog.setWindowTitle("Database Setup")
    loading_dialog.setFixedSize(400, 200)
    loading_dialog.setStyleSheet("background-color: black; color: white;")
    
    layout = QVBoxLayout()
    
    title = QLabel("Setting up Expense Tracker Database")
    title.setStyleSheet("font-size: 14pt; font-weight: bold;")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title)
    
    message = QLabel("Please wait while we configure the database...\n\nThis will identify and fix any issues with your categories.")
    message.setStyleSheet("font-size: 11pt;")
    message.setAlignment(Qt.AlignmentFlag.AlignCenter)
    message.setWordWrap(True)
    layout.addWidget(message)
    
    progress_message = QLabel("Working...")
    progress_message.setStyleSheet("font-style: italic; color: #CCCCCC;")
    progress_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(progress_message)
    
    loading_dialog.setLayout(layout)
    loading_dialog.show()
    
    # Process events to show the dialog before database work
    app.processEvents()
    
    # Setup the database
    setup_database()
    
    # Update dialog message
    progress_message.setText("Database setup complete!")
    app.processEvents()
    
    # Create and show the main application window
    window = MainWindow()
    window.show()
    
    # Close the loading dialog
    loading_dialog.close()
    
    sys.exit(app.exec())