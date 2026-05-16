# 💰 ExpenseVault - Smart Personal Finance Manager

> A desktop-based expense tracking application built with **Python (PyQt6)** and **MySQL**. Manage your finances intelligently with real-time budget alerts and visual analytics.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-Latest-green?logo=qt&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange?logo=mysql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

</div>

---

## 📑 Table of Contents

- [ Key Features](#-key-features)
- [ Tech Stack](#️-tech-stack)
- [ Quick Start](#-quick-start)
- [ Installation](#-installation)
- [ How to Use](#-how-to-use)
- [ Database Structure](#-database-structure)
- [ Feature Details](#-feature-details)
- [ Advanced Features](#-advanced-features)
- [ Troubleshooting](#-troubleshooting)
- [ Usage Scenarios](#-usage-scenarios)
- [ Contributing](#-contributing)
- [ License](#-license)

---

##  Key Features

###  **Category Management**
- ✅ Add/remove expense categories dynamically
- ✅ Store categories permanently in MySQL database
- ✅ Automatic database repair and validation
- ✅ Handle mistaken database structures automatically

###  **Expense Management**
- ✅ Add expenses with date and amount
- ✅ Edit existing expenses inline
- ✅ Delete expenses with confirmation
- ✅ Filter expenses by custom date ranges
- ✅ Quick filter for current month
- ✅ View total spending per category
- ✅ **Export to CSV** for external analysis

###  **Visual Analytics**
- ✅ **Interactive Pie Chart** showing expense distribution
- ✅ Color-coded slices for easy identification
- ✅ Percentage contribution display
- ✅ Total expense amount visualization
- ✅ Real-time chart updates

### 💰 **Monthly Budget Limits**
- ✅ Set spending limits per category
- ✅ Set uniform limits across all categories
- ✅ Inline editing of limits
- ✅ Clear limits anytime
- ✅ **Visual Status Indicators:**
  - 🟢 **Safe** - Under 80% of limit
  - 🟠 **Warning** - 80%+ of limit used
  - 🔴 **Exceeded** - Over the limit

### ⚠️ **Smart Alert System**
- ✅ Real-time alert on main screen when limits exceeded
- ✅ Pop-up warning when adding expense that crosses limit
- ✅ Live spending calculation for current month
- ✅ Detailed over-budget information

###  **Database Auto-Setup**
- ✅ Automatically creates database if missing
- ✅ Auto-creates required tables with proper structure
- ✅ Repairs incorrect or corrupted tables
- ✅ Cleans up invalid database structures
- ✅ Foreign key relationships maintained

---

## Tech Stack

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.8+ | Programming language |
| **PyQt6** | Latest | GUI framework |
| **MySQL** | 8.0+ | Database management |
| **mysql-connector-python** | Latest | Database connectivity |
| **matplotlib** | Latest | Chart visualization |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.8 or higher installed
- MySQL Server running locally
- pip package manager

### Installation in 3 Steps

```bash
# Step 1: Clone the repository
git clone https://github.com/sandip-sharma1/ExpanseVault.git
cd ExpanseVault

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Configure database (see Installation section)
# Then run the application
python Expensevault.py
```

---

##  Installation

### Step 1: System Requirements
```bash
# Check Python version
python --version  # Should be 3.8 or higher

# Verify MySQL is running
mysql --version
```

### Step 2: Install Python Dependencies
```bash
pip install PyQt6
pip install mysql-connector-python
pip install matplotlib
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

### Step 3: Configure MySQL Database

**Option A: Automatic Setup (Recommended)**

The application will automatically create the database and tables on first run. Just ensure your MySQL credentials match the configuration.

**Option B: Manual Setup**

1. Open MySQL and create the database:
```sql
CREATE DATABASE IF NOT EXISTS expensevault;
USE expensevault;

-- Create categories table
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

-- Create expenses table
CREATE TABLE expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Create category_limits table
CREATE TABLE category_limits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    limit_amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);
```

### Step 4: Configure Database Connection

Edit the database configuration in `Expensevault.py` (lines 27-32):

```python
DB_CONFIG = {
    "host": "localhost",           # MySQL host
    "user": "root",                # MySQL username
    "password": "Root123@",        # MySQL password
    "database": "expensevault"     # Database name
}
```

**Default credentials are:**
- Host: `localhost`
- User: `root`
- Password: `Root123@`
- Database: `expensevault`

### Step 5: Run the Application

```bash
python Expensevault.py
```

A loading dialog will appear showing database setup progress. After setup completes, the main application window opens.

---

##  How to Use

### Main Menu
When you launch ExpanseVault, you'll see 5 main options:

```
┌─────────────────────────────────────┐
│     Expense Tracker Main Menu       │
├─────────────────────────────────────┤
│  1. View Expenses      [View data]  │
│  2. Add Expense        [Add data]   │
│  3. Manage Limits      [Set budgets]│
│  4. View Chart         [Analytics]  │
│  5. Exit               [Quit app]   │
└─────────────────────────────────────┘
```

### 📝 Adding a Category

1. Click **"Add Expense"** from main menu
2. Click **"Add Category"** button
3. Enter category name (e.g., "Groceries", "Entertainment")
4. Category is saved to database immediately

### 💵 Adding an Expense

1. Click **"Add Expense"** from main menu
2. Select the category from the list
3. Enter the amount (e.g., 50.00)
4. Select the date using the calendar popup
5. Click **"Submit"**

**Smart Alerts:**
- If expense exceeds monthly limit, you'll see a warning popup
- Main screen shows alert if any category is over budget

### 👁️ Viewing Expenses

1. Click **"View Expenses"** from main menu
2. Select a category
3. **Filter by Date:** Set start and end dates
4. **Quick Filters:** Click "Current Month" for current month expenses
5. Click **"Filter"** to apply

**In the expense view, you can:**
- **Edit:** Click "Edit" button to modify amount/date
- **Delete:** Click "Delete" button to remove (with confirmation)
- **Export:** Click "Export to CSV" to save to file
- **Set Limit:** Click "Set Limit" to set budget for category

### 📊 Viewing Analytics

1. Click **"View Chart"** from main menu
2. A pie chart displays expense distribution by category
3. **Chart shows:**
   - Category names
   - Percentage of total spending
   - Total expense amount at bottom
   - Color-coded slices for easy identification

### 💰 Managing Budget Limits

1. Click **"Manage Limits"** from main menu
2. Table shows all categories with:
   - Current limit
   - Monthly spending
   - Status (Safe/Warning/Exceeded)

**In Manage Limits window, you can:**
- **Set Limit:** Click "Set Limit" for specific category
- **Clear Limit:** Click "Clear" to remove budget cap
- **Set All Limits:** Click "Set All Limits" for all categories
- **Refresh:** Click "Refresh" to update data

---

## 🗄️ Database Structure

### Table 1: `categories`
| Field | Type | Description |
|-------|------|-------------|
| `id` | INT (PK) | Unique category identifier |
| `name` | VARCHAR(255) | Category name (unique) |

**Example:**
```sql
INSERT INTO categories (name) VALUES ('Groceries');
INSERT INTO categories (name) VALUES ('Entertainment');
INSERT INTO categories (name) VALUES ('Transportation');
```

### Table 2: `expenses`
| Field | Type | Description |
|-------|------|-------------|
| `id` | INT (PK) | Unique expense identifier |
| `category_id` | INT (FK) | Reference to categories table |
| `amount` | DECIMAL(10,2) | Expense amount (up to ₹99,999,999.99) |
| `date` | DATE | Date of expense |

**Example:**
```sql
INSERT INTO expenses (category_id, amount, date) 
VALUES (1, 500.00, '2024-05-15');
```

### Table 3: `category_limits`
| Field | Type | Description |
|-------|------|-------------|
| `id` | INT (PK) | Unique limit identifier |
| `category_id` | INT (FK) | Reference to categories table |
| `limit_amount` | DECIMAL(10,2) | Monthly spending limit |

**Example:**
```sql
INSERT INTO category_limits (category_id, limit_amount) 
VALUES (1, 5000.00);  -- ₹5000 monthly limit for Groceries
```

### Relationships
```
categories
    ├── expenses (1:N) - One category has many expenses
    └── category_limits (1:1) - One category has one limit
```

---

## 💡 Feature Details

### 🎨 Dark Theme UI
- Professional dark-themed interface
- Reduces eye strain for extended use
- Modern color scheme with visual feedback

### 🔒 Data Persistence
- All data stored securely in MySQL
- Automatic backup with proper foreign keys
- Cascading deletes prevent orphaned records

###  User-Friendly Design
- Intuitive navigation between windows
- Clear error messages and feedback
- Popup dialogs for confirmations

###  Real-Time Calculations
- Live expense totals per category
- Current month spending auto-calculated
- Percentage calculations for budget status

###  CSV Export
Export expenses to CSV format:
```csv
ID,Amount,Date
1,500.00,2024-05-15
2,300.00,2024-05-16
3,200.00,2024-05-17
```

---

## 🔧 Advanced Features

### 📊 Budget Status Visualization
The app uses color coding for quick budget assessment:

| Status | Color | Indicator | Meaning |
|--------|-------|-----------|---------|
| Safe | 🟢 Green | Under 80% | Budget is comfortable |
| Warning | 🟠 Orange | 80-99% | Approaching limit, be careful |
| Exceeded | 🔴 Red | 100%+ | Over budget, reduce spending |
| No Limit | ⚪ White | N/A | No budget set for category |

###  Automatic Database Validation
The application automatically:
1. **Checks** if database exists, creates if missing
2. **Validates** table structure on startup
3. **Repairs** corrupted or incomplete tables
4. **Cleans** mistaken database structures
5. **Maintains** referential integrity

###  Date Filtering
Advanced date range filtering:
- Select custom start and end dates
- One-click "Current Month" filter
- Formatted date picker with calendar
- Historical expense tracking

###  Category Analytics
- See total spending per category
- Identify spending patterns
- Plan budgets based on history
- Visual comparison with pie chart

---

## ❓ Troubleshooting

### ❌ Problem: "Failed to connect to database"

**Solution:**
1. Verify MySQL is running:
   ```bash
   mysql -u root -p
   ```
2. Check database credentials in `Expensevault.py`:
   ```python
   DB_CONFIG = {
       "host": "localhost",
       "user": "root",
       "password": "Root123@",
       "database": "expensevault"
   }
   ```
3. Update credentials to match your MySQL setup
4. Restart the application

### ❌ Problem: "Database not found"

**Solution:**
1. The app should auto-create the database
2. If it doesn't, create manually:
   ```sql
   CREATE DATABASE expensevault;
   ```
3. Restart the application

### ❌ Problem: "No categories found"

**Solution:**
1. Add a category first through the UI
2. Or insert manually:
   ```sql
   USE expensevault;
   INSERT INTO categories (name) VALUES ('My Category');
   ```

### ❌ Problem: "Table structure is invalid"

**Solution:**
1. The app will auto-repair on startup
2. If issue persists, drop and recreate tables:
   ```sql
   USE expensevault;
   DROP TABLE expenses;
   DROP TABLE category_limits;
   DROP TABLE categories;
   ```
3. Restart the application (it will recreate tables)

### ❌ Problem: "Pie chart not showing"

**Solution:**
1. Ensure you have expenses in the database
2. Verify matplotlib is installed:
   ```bash
   pip install --upgrade matplotlib
   ```
3. Add some expenses and try again

### ❌ Problem: "Cannot add expense - category doesn't exist"

**Solution:**
1. Create the category first
2. Or add category through "Add Expense" → "Add Category"
3. Refresh and try again

### ✅ Debug Mode
For troubleshooting, check the console output:
1. The app prints database operations to console
2. Look for "ERROR" messages
3. Database initialization is logged in detail
4. All SQL queries are printed for verification

---

## 📚 Usage Scenarios

### 📋 Scenario 1: Monthly Budget Planning
1. **Create Categories:**
   - Groceries
   - Entertainment
   - Transportation
   - Utilities
   - Dining Out

2. **Set Monthly Limits:**
   - Groceries: ₹5,000
   - Entertainment: ₹2,000
   - Transportation: ₹3,000
   - Utilities: ₹1,500
   - Dining Out: ₹2,500

3. **Track Spending:**
   - Add expenses as you spend
   - Watch alerts when approaching limits
   - View chart to see spending distribution

### 📊 Scenario 2: Expense Analysis
1. Add all your monthly expenses
2. View Chart to see where money goes
3. Filter by date to analyze specific periods
4. Export to CSV for spreadsheet analysis
5. Adjust budget limits based on patterns

### 🎯 Scenario 3: Finding Budget Leaks
1. Look at Visual Chart
2. Identify highest spending categories
3. Filter high-spending category by week
4. Find problematic expenses
5. Set limit to prevent future overspending

### 💰 Scenario 4: Savings Goal Achievement
1. Set tight budget limits
2. Track spending daily
3. Get alerts when overspending
4. View remaining budget for month
5. Adjust expenses to meet goals

---


---

## 📋 License

This project is licensed under the **MIT License** - see the LICENSE file for details.

---

##  Acknowledgments

- PyQt6 for the GUI framework
- MySQL for robust database management
- matplotlib for beautiful visualizations

---

<div align="center">

</div>
