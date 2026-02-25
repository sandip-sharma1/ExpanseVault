# ExpanseVault
This is a personal Finance manager app,That uses your database to store data..

--ExpenseVault – Smart Expense Tracker (PyQt6 + MySQL)--

ExpenseVault is a desktop-based expense tracking application built using Python (PyQt6) and MySQL.
It allows users to:
Organize expenses by category
Set monthly spending limits
Track spending visually with charts
Filter expenses by date
Export reports to CSV
Get alerts when budgets are exceeded
This project combines a clean dark-themed UI with a robust MySQL backend for persistent data storage.


-- Features --
1) Category Management
Add new categories
Remove categories
Automatically handles mistaken database tables
Categories stored in MySQL

2) Expense Management
Add expenses with date and amount
Edit existing expenses
Delete expenses
Filter expenses by date range
Quick filter: Current Month
View total spending per category
Export expenses to CSV

3) Visual Analytics
Pie chart of expense distribution
Color-coded slices
Displays percentage contribution
Shows total expense amount

4) Monthly Budget Limits
Set monthly spending limit per category
Set limits for all categories at once
Inline editing of limits
Clear limits anytime
Visual indicators:
🟢 Safe
🟠 Warning (80%+ used)
🔴 Exceeded
⚠️ Smart Alerts
Alert on main screen if limits are exceeded
Pop-up warning when adding expense that crosses limit
Live spending calculation for current month

5) Database Auto Setup
Automatically:
Creates database if missing
Creates required tables
Repairs incorrect tables
Cleans up invalid structures


--- Technologies Used---
Python 3
PyQt6 – GUI framework
MySQL – Database
mysql-connector-python – DB connection
matplotlib – Pie chart visualization


--- Database Structure ---
The application uses 3 main tables:
1) categories
Field	Type
id	INT (Primary Key)
name	VARCHAR (Unique)

2) expenses
Field	Type
id	INT (Primary Key)
category_id	INT (Foreign Key)
amount	DECIMAL(10,2)
date	DATE


3) category_limits
Field	Type
id	INT (Primary Key)
category_id	INT (Foreign Key)
limit_amount	DECIMAL(10,2)


How to use this ?
step 1--->Configure your database as follows
    DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Root123@",  
    "database": "expensevault"
    }
this is the default database configuration i have used during development.

step 2--->Make sure that all the requirements for this project  are installed