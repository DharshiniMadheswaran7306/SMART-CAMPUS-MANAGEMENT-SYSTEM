Smart Campus Management System

A web-based Smart Campus Management System developed using Python, Flask, SQLite, HTML, CSS, Jinja2, and SMTP. The system provides student authentication, attendance tracking, event management, smart canteen ordering, reward points, and email notification services.

📌 Features

🔐 Authentication Module
Student login using unique User ID and Password.
Session-based authentication using Flask.

👤 Student Profile Module
Displays student information.
Includes Name, Register Number, Department, Classroom, and Email ID.

📅 Attendance Module
Tracks attendance records.
Displays absent days using a calendar view.
Calculates attendance percentage automatically.

🎉 Event Management Module
Allows administrators to add and manage campus events.
Supports Hackathons, Workshops, Conferences, Paper Presentations, and more.

📧 Event Notification Module
Sends email notifications to students whenever a new event is added.

🍽 Smart Canteen Module
Online food ordering system for students.
Food delivery is restricted to break periods:
10:45 AM – 11:05 AM
12:05 PM – 01:00 PM
02:45 PM – 03:00 PM

🛒 Order Management Module
Maintains order details and order status.
Supports delivery location and payment information.

📦 Stock Management Module
Each food item has a stock limit of 100.
Displays "Out of Stock" when the limit is reached.

🔄 Restocking Module
Allows administrators to restock food items.
Makes unavailable items available again.

⭐ Credit Points Module
Students earn points for every purchase.
Free meals are awarded after reaching 100 points.

📨 Email Notification System
Uses Gmail SMTP.

🛠 Technologies Used
Technology         	Purpose
Python 3.13       	Backend Development
Flask             	Web Framework
SQLite	            Database Management
HTML5	              Frontend Structure
CSS3	              User Interface Design
Jinja2	            Dynamic Web Templates
SMTP	              Email Notifications

📂 Project Structure
smart_campus/
│
├── app.py
├── smart_campus.db
├── requirements.txt
├── README.md
├── fix_emails.sql
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── attendance.html
│   ├── events.html
│   ├── canteen.html
│   ├── checkout.html
│   ├── credits.html
│   ├── order_success.html
│   ├── admin_events.html
│   ├── admin_canteen.html
│   ├── student_emails.html
│   └── test_email.html
│
└── static/
    ├── css/
    │    └── style.css
    └── images/

    🗄 Database Tables

The system uses SQLite database with the following tables:

Students
Attendance
Events
Menu Items
Orders
Credit Points

📋 Software Requirements
Python 3.8 or Higher
Flask
SQLite3
HTML5
CSS3
Jinja2
VS Code 
Windows 

🚀 Installation
Clone the Repository
git clone https://github.com/your-username/smart-campus-management-system.git
cd smart-campus-management-system

Install Dependencies
pip install -r requirements.txt

or

pip install flask
Run the Application
python app.py

Open:

http://127.0.0.1:5000
📧 Email Configuration

This project uses Gmail SMTP for sending notifications.

In app.py, configure:

EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_16_character_app_password"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

Note: Use a Gmail App Password instead of your regular Gmail password.

📷 System Modules
Authentication Module
Dashboard Module
Student Profile Module
Attendance Module
Events Module
Event Notification Module
Smart Canteen Module
Order Management Module
Stock Management Module
Restocking Module
Credit Points Module
Email Notification Module
Database Module

🔄 Workflow
Student Login
      ↓
Dashboard
      ↓
Profile / Attendance / Events / Canteen
      ↓
Place Order
      ↓
Stock Validation
      ↓
Credit Points Update
      ↓
Order Processing
      ↓
Delivery During Break Time
      ↓
Admin Management
      ↓
Email Notifications

##Python Concepts Used

Variables and Data Types
Conditional Statements
Loops
Functions and Modular Programming
Lists and Dictionaries
File Handling
Object-Oriented Programming (Basic Level)
SQLite Database Connectivity
Flask Framework
HTML and CSS Integration
Session Management
SMTP Email Protocol
Form Handling using Flask

##Future Enhancements

Online Payment Integration
QR Code Based Attendance
Mobile Application Support
AI-Based Food Recommendation
Real-Time Notifications
Cloud Database Integration
Admin Analytics Dashboard

Conclusion
The Smart Campus Management System provides an efficient platform for managing student information, attendance, campus events, and smart canteen services. The integration of automated email notifications and reward-based food ordering enhances communication and improves the overall campus experience.

👩‍💻 Developed By
DHARSHINI MADHESWARAN AND DEEPIKA SREE S R
B.E Computer Science and Engineering
M. Kumarasamy College of Engineering (MKCE)

📄 License
This project is developed for educational purposes and academic use.
© 2026 Smart Campus Management System. All Rights Reserved.

