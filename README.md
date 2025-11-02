# Appointment App

A Flask-based web application for scheduling and managing mock interview appointments. Candidates can browse available time slots, make a booking, and receive automated confirmation emails. Administrators can log in to review upcoming or completed interviews, cancel bookings, and trigger notification emails.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Screenshots](#screenshots)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [Email Notifications](#email-notifications)
- [Running the Application](#running-the-application)
- [Available Routes](#available-routes)
- [Styling](#styling)
- [Deployment Notes](#deployment-notes)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features
- Responsive booking interface with animated loading indicators and validation feedback.
- Daily availability view that prevents double-booking time slots and rejects past dates.
- Admin dashboard that separates upcoming and completed interviews.
- Admin-controlled cancellation workflow that sends cancellation emails to candidates.
- REST endpoint for fetching available slots for a given date (used by the booking page).
- Secure password hashing for the admin login.
- Configurable MySQL and SMTP connections driven by environment variables.

## Architecture
- **Backend**: Flask application (`app.py`) using `flask-mysqldb` for database access and `Flask-Mail` for transactional email.
- **Frontend**: HTML templates (`templates/`) rendered with Jinja2 and enhanced with vanilla JavaScript for dynamic slot loading.
- **Styling**: Centralized CSS (`static/style.css`) with CSS variables, gradients, and custom animations.
- **Persistence**: MySQL database storing appointment bookings and admin credentials.

## Screenshots
Screenshots are not included in this repository. You can generate them locally by running the application and capturing the UI from your browser.

## Prerequisites
- Python 3.10+
- MySQL Server 8.0+
- An SMTP account for sending transactional emails (Gmail, Outlook, or any provider that supports SMTP).
- (Optional) `virtualenv` or another tool for creating Python virtual environments.

## Installation
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Appointment-App
   ```
2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```
3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables
Create a `.env` file in the project root with the following keys:

```env
# Flask
FLASK_SECRET_KEY=replace_with_random_secret

# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=appointments

# SMTP / Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password_or_app_password
```

> **Tip:** If you use Gmail, create an App Password and enable "Less Secure Apps" or use OAuth according to Google's latest policy.

The application loads these values through `python-dotenv` (`load_dotenv()` in `app.py`).

## Database Schema
Create the database and tables before running the application:

```sql
CREATE DATABASE IF NOT EXISTS appointments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE appointments;

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    slot VARCHAR(10) NOT NULL,
    interview_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
```

### Admin Account
Insert an admin record with a hashed password. You can generate a hash using Flask's shell or Python:

```python
from werkzeug.security import generate_password_hash
print(generate_password_hash("your_admin_password"))
```

Then insert the admin row:

```sql
INSERT INTO admin (username, password)
VALUES ('admin', '<paste_generated_hash_here>')
ON DUPLICATE KEY UPDATE password = VALUES(password);
```

## Email Notifications
- Booking confirmations and cancellation notices are sent via the configured SMTP server.
- Emails are composed using `Flask-Mail` (`Message` objects in `app.py`).
- Ensure that your SMTP provider allows sending from the specified account and that less-secure access (if required) is enabled.

## Running the Application
1. Ensure the `.env` file and database tables are configured.
2. Start the Flask development server:
   ```bash
   python app.py
   ```
   The app runs on `http://127.0.0.1:5000/` by default.
3. Access the admin dashboard at `http://127.0.0.1:5000/admin` (you will be redirected to the login page if not authenticated).

For production, use a WSGI server such as Gunicorn:

```bash
gunicorn -b 0.0.0.0:8000 app:app
```

## Available Routes
| Route | Methods | Description |
|-------|---------|-------------|
| `/` | GET, POST | Booking form. POST submissions create a booking, send confirmation email, and prevent double-booking.
| `/admin` | GET, POST | Admin dashboard. GET renders bookings; POST handles cancellations and sends notification emails. Requires login.
| `/login` | GET, POST | Admin login form. Validates hashed password stored in the `admin` table.
| `/logout` | GET | Ends the admin session.
| `/get_available_slots` | GET | Returns JSON payload with available time slots for a given `date` query parameter.

## Styling
- All styles live in `static/style.css` and use CSS variables for theming.
- The layout implements a glassmorphism aesthetic, responsive grid, and animated backgrounds.
- JavaScript in `templates/index.html` enhances the UX with dynamic slot loading, form validation, and visual feedback.

## Deployment Notes
- Configure environment variables via your hosting provider's secret management system.
- Ensure the SMTP provider allows connections from your hosting environment.
- Run database migrations manually using the SQL statements above or automate them via your deployment pipeline.
- Disable `debug=True` in production by using an environment variable (e.g., `FLASK_DEBUG=0`) or adjusting the entry point.

## Troubleshooting
| Issue | Resolution |
|-------|------------|
| `mysqlclient` fails to install | Install MySQL client libraries (e.g., `sudo apt-get install libmysqlclient-dev`) before running `pip install`. |
| "Slot already booked" warning | The requested time slot is already taken for that date. Choose a different slot. |
| Emails are not delivered | Verify SMTP credentials, port/TLS settings, and check provider logs for rejected messages. |
| Unable to log in as admin | Confirm the hashed password in the database matches the password you are entering. |

## License
This project does not currently specify a license. Add one if you plan to distribute or open-source the application.
