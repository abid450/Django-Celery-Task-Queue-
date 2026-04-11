# 📧 Django Celery Email Verification System

A production-ready **Email Verification System** built with Django, Django REST Framework (DRF), Celery, Redis, and JWT authentication.

![Django](https://img.shields.io/badge/Django-4.2-green?logo=django)
![DRF](https://img.shields.io/badge/DRF-3.14-red?logo=django)
![Celery](https://img.shields.io/badge/Celery-5.6-green?logo=celery)
![Redis](https://img.shields.io/badge/Redis-7.0-red?logo=redis)
![JWT](https://img.shields.io/badge/JWT-SimpleJWT-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| ✅ **User Registration** | Register with username, email, and password |
| ✅ **Email Verification** | 6-digit OTP sent via email (Celery background task) |
| ✅ **JWT Authentication** | Secure token-based authentication |
| ✅ **Resend Verification Code** | Request new verification code |
| ✅ **Password Change** | Authenticated users can change password |
| ✅ **Profile Management** | Update profile, bio, phone number |
| ✅ **Celery Tasks** | Asynchronous email sending |
| ✅ **Redis Cache** | Fast caching and message broker |
| ✅ **Swagger/ReDoc API Docs** | Interactive API documentation |
| ✅ **CORS Support** | Frontend integration ready |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Django 4.2** | Web Framework |
| **Django REST Framework** | API Development |
| **Celery** | Background Task Queue |
| **Redis** | Message Broker & Cache |
| **JWT** | Authentication |
| **PostgreSQL/SQLite** | Database |
| **Swagger/ReDoc** | API Documentation |
| **Gmail SMTP** | Email Sending |

---

## 📁 Project Structure

cl/
├── accounts/
│ ├── migrations/
│ ├── init.py
│ ├── admin.py
│ ├── apps.py
│ ├── models.py
│ ├── serializers.py
│ ├── tasks.py # Celery tasks
│ ├── urls.py
│ ├── utils.py
│ ├── views.py
│ └── permissions.py
├── cl/
│ ├── init.py
│ ├── celery.py # Celery configuration
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── templates/
├── static/
├── media/
├── logs/
├── manage.py
├── requirements.txt
└── README.md


---

## 🚀 Installation Guide

### Prerequisites
- Python 3.10+
- Redis Server
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/abid450/2Fa-Authentication-System.git
cd 2Fa-Authentication-System

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

Step 4: Configure Environment Variables
Create a .env file in the root directory:

env
SECRET_KEY=django-insecure-your-secret-key
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
Step 5: Run Migrations
bash
python manage.py makemigrations
python manage.py migrate
Step 6: Start Redis Server
bash
# Windows
redis-server --port 6380

# Mac/Linux
redis-server --port 6380
Step 7: Start Celery Worker
bash
# Windows
celery -A cl worker --loglevel=info -P eventlet

# Mac/Linux
celery -A cl worker --loglevel=info
Step 8: Start Celery Beat (Optional - for periodic tasks)
bash
celery -A cl beat --loglevel=info
Step 9: Run Django Server
bash
python manage.py runserver
📡 API Endpoints
Method	Endpoint	Description	Auth Required
POST	/users/	Register new user	❌
POST	/users/verify-email/	Verify email with OTP	❌
POST	/users/resend-verification/	Resend verification code	❌
POST	/token/	Login (get JWT tokens)	❌
POST	/token/refresh/	Refresh access token	❌
POST	/token/verify/	Verify JWT token	❌
POST	/users/change-password/	Change password	✅
GET	/users/me/	Get current user profile	✅
PUT/PATCH	/users/profile/	Update profile	✅
GET	/users/verification-status/	Check verification status	✅
GET	/docs/	Swagger API Documentation	❌
GET	/redoc/	ReDoc API Documentation	❌

📧 API Request Examples
1. User Registration

POST /users/
Content-Type: application/json

{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass@123",
    "password2": "SecurePass@123"
}

2. Verify Email

POST /users/verify-email/
Content-Type: application/json

{
    "email": "john@example.com",
    "verification_code": "123456"
}

3. Login (Get Tokens)
POST /token/
Content-Type: application/json

{
    "email": "john@example.com",
    "password": "SecurePass@123"
}

4. Get Current User (Authenticated)
GET /users/me/
Authorization: Bearer <access_token>

{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_email_verified": true,
    "date_joined": "2026-04-10T10:30:00Z"
}

📊 Celery Architecture
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Django    │────▶│    Redis    │────▶│   Celery    │
│    API      │     │   (Broker)  │     │   Worker    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           │                    ▼
                           │              ┌─────────────┐
                           │              │   Email     │
                           │              │   Sent ✅   │
                           │              └─────────────┘
                           ▼
                    ┌─────────────┐
                    │   Celery    │
                    │    Beat     │ (Periodic Tasks)
                    └─────────────┘

