# Academic Performance Prediction System

A full-stack web application for predicting student academic performance using a rule-based prediction engine. Built with **Python Flask** (backend + ML), **Java Spring Boot** (alternative backend), and a **dark-themed glassmorphism UI**.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Default Credentials](#default-credentials)

---

## Features

- **Role-Based Access**: Admin, Staff, and Student dashboards with separate login flows
- **Student Management**: Add, edit, delete students with academic records
- **Academic Prediction**: Rule-based prediction engine (Pass/Fail, Risk Level, Grade)
- **Batch Prediction**: Predict all students at once
- **Analytics Dashboard**: Department-wise stats, risk distribution, pass/fail ratios
- **Search & Filter**: Real-time search with department, risk, and status filters
- **Pagination**: Client-side pagination for large student tables
- **CSV Export**: Download student data as CSV (all / by risk level)
- **PDF Reports**: Students can download their prediction report as PDF
- **REST API**: JSON API endpoints for programmatic access
- **Responsive Design**: Mobile-friendly with hamburger menu
- **Toast Notifications**: Animated toast alerts with auto-dismiss
- **Loading Indicators**: Full-screen loading overlay for form submissions

---

## Tech Stack

| Layer        | Technology                         |
| ------------ | ---------------------------------- |
| **Backend**  | Python 3.x, Flask, SQLAlchemy      |
| **Database** | SQLite (Python) / MySQL (Java)     |
| **Auth**     | Flask-Login, Werkzeug              |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla)  |
| **ML Model** | Rule-based prediction engine       |
| **PDF**      | ReportLab                          |
| **Alt Backend** | Java 17, Spring Boot, JPA       |
| **Testing**  | pytest                             |

---

## Project Structure

```
Update Version 1 Java/
├── backend/
│   ├── python/                  # Main Python Flask backend
│   │   ├── app.py               # Flask application factory
│   │   ├── config.py            # Configuration settings
│   │   ├── requirements.txt     # Python dependencies
│   │   ├── models/
│   │   │   ├── database.py      # SQLAlchemy models (User, Student, Academic, History)
│   │   │   └── ml_model.py      # Rule-based prediction engine
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication routes
│   │   │   ├── dashboard.py     # Dashboard routes (admin/staff/student)
│   │   │   └── api.py           # REST API endpoints (/api/v1/*)
│   │   └── tests/
│   │       ├── conftest.py      # Pytest fixtures
│   │       ├── test_ml_model.py # Unit tests for prediction model
│   │       └── test_routes.py   # Integration tests for routes
│   └── java/                    # Alternative Spring Boot backend
│       ├── pom.xml
│       └── src/main/java/com/academic/
├── frontend/
│   └── python_ui/
│       ├── static/css/          # Static CSS files
│       └── templates/           # Jinja2 HTML templates
│           ├── base.html        # Base template with layout & JS
│           ├── role_select.html # Role selection page
│           ├── login_form.html  # Login page
│           ├── admin_dashboard.html
│           ├── staff_dashboard.html
│           ├── student_dashboard.html
│           ├── enter_marks.html
│           └── api_docs.html    # API documentation page
└── README.md
```

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- (Optional) Java 17 + Maven for Spring Boot backend

### Python Backend Setup

```bash
# Navigate to the Python backend
cd backend/python

# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest
```

### Java Backend Setup (Optional)

```bash
cd backend/java
mvn clean install
```

> **Note**: The Java backend requires MySQL running on `localhost:3306` with credentials `root/root`.

---

## Running the Application

### Start the Python Flask Server

```bash
cd backend/python
python app.py
```

The application will be available at: **http://127.0.0.1:5000**

### Start the Java Spring Boot Server (Optional)

```bash
cd backend/java
mvn spring-boot:run
```

Available at: **http://localhost:8080**

---

## API Documentation

The application includes a built-in API documentation page accessible at:

**http://127.0.0.1:5000/dashboard/api-docs**

### API Endpoints Summary

| Method | Endpoint                    | Description                     |
| ------ | --------------------------- | ------------------------------- |
| GET    | `/api/v1/students`          | List students (search/filter/paginate) |
| GET    | `/api/v1/students/<reg_no>` | Get student details             |
| GET    | `/api/v1/stats`             | Dashboard statistics            |
| POST   | `/api/v1/predict/<reg_no>`  | Run prediction for a student    |

> All endpoints require authentication. Login via the web interface first.

---

## Testing

### Run All Tests

```bash
cd backend/python
python -m pytest tests/ -v
```

### Run Only ML Model Tests

```bash
python -m pytest tests/test_ml_model.py -v
```

### Run Only Route Integration Tests

```bash
python -m pytest tests/test_routes.py -v
```

### Test Coverage

- **ML Model Tests**: 18 test cases covering all risk levels, grades, bonuses, penalties, and edge cases
- **Route Tests**: 17 integration tests covering auth flows, access control, CRUD, and API endpoints

---

## Default Credentials

| Role    | Username/Reg No | Password   |
| ------- | --------------- | ---------- |
| Admin   | `admin`         | `admin123` |

> Staff and Student accounts are created by the Admin through the dashboard.

---

## Architecture

```
┌──────────────────────────────────────────┐
│             Frontend (Jinja2)            │
│  role_select → login → dashboard pages   │
│  Toast notifications, search, pagination │
└───────────────┬──────────────────────────┘
                │
    ┌───────────▼───────────┐
    │   Flask Application   │
    │   ├── auth routes     │
    │   ├── dashboard routes│
    │   └── API routes      │
    └───────────┬───────────┘
                │
    ┌───────────▼───────────┐
    │   Models & Services   │
    │   ├── SQLAlchemy ORM  │
    │   └── ML Prediction   │
    └───────────┬───────────┘
                │
    ┌───────────▼───────────┐
    │   SQLite Database     │
    │   ├── users           │
    │   ├── students        │
    │   ├── student_academics│
    │   └── prediction_history│
    └───────────────────────┘
```
