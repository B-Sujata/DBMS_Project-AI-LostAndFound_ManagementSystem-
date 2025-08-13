# TY_DBMS_Project-LostAndFound_ManagementSystem-

Lost and Found Management System: A web app to report, track, and match lost and found items with admin verification and notifications. Built with Flask, PostgreSQL, and JS.

# Lost and Found Management System

## Overview

The Lost and Found Management System is a web-based application designed to help institutions efficiently manage and track lost and found items. Users can report lost or found belongings by providing detailed information such as item name, description, category, date, location, and contact details. The system allows users to search and filter through the database to find matching items.

Administrators verify and approve listings to ensure the database remains accurate and trustworthy. The platform also sends notifications when possible matches are found, speeding up the process of returning items to their rightful owners.

## Features

- User registration and authentication
- Report lost or found items with detailed descriptions
- Search and filter items in the database
- Admin verification and approval of listings
- Notification system for matching items
- Secure database management using PostgreSQL

## Technology Stack

- Backend: Python (Flask)
- Database: PostgreSQL
- Frontend: HTML, CSS, JavaScript

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/your-repo.git
   ```

2. Navigate to the project directory:
   cd your-repo

3. Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate # On Windows use: venv\Scripts\activate

4. Install dependencies:

pip install -r requirements.txt

5.Set up PostgreSQL and configure database connection in the application.

6.Run the Flask app:

flask run

Usage
Register as a user to report lost or found items.

Search the database for matching items.

Admins can verify and approve item listings.

Receive notifications for potential matches.

Contributing
Contributions are welcome! Please fork the repo and create a pull request.
