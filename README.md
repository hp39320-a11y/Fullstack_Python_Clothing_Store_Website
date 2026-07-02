# 🌟 UrbanWear - Premium E-Commerce Platform

Welcome to **UrbanWear**, a modern, high-fashion e-commerce storefront and admin management platform built with Django, CSS Custom Properties, and vanilla Javascript. The project features a premium glassmorphic visual aesthetic, seamless asynchronous AJAX shopping flows, a dedicated custom admin dashboard, and highly secure environment configuration management.

---

## 🚀 Key Features

*   **Premium Visual Experience**: Clean Zara/AJIO-inspired user interface featuring glassmorphic navigation headers (`backdrop-filter: blur(16px)`), modern typography (Google Fonts *Outfit* & *Playfair Display*), harmonious HSL colors, and micro-interactive product card hover animations.
*   **Dynamic Theme Toggler**: Instantly switches between Dark Mode and Light Mode, persists choice across pages using local storage, and syncs automatically with system preferences.
*   **Asynchronous Shopping Flows**: Standard GET-redirect bugs are eliminated. Add-to-cart and wishlist saves use asynchronous JavaScript `fetch` API, showing responsive toast notifications and updating header cart count badges in real-time.
*   **Secure Environment Configuration**: Sensitive variables (Django `SECRET_KEY`, database configs, and Razorpay API tokens) are secured in a local `.env` environment file.
*   **Razorpay Payment Integration**: Integrated payment checkout flow for direct card/UPI payments with robust try-except error catching for invalid credentials.
*   **Custom Admin Dashboard**: Fully custom admin panel (`adminpanel` app) separated from standard Django admin to manage products, categories, active discount coupons, and customer orders.

---

## 📂 Project Directory Structure

```text
clothingstore_web/
│
├── storeproject/                    # Main Django Project folder
│   ├── adminpanel/                  # Custom Admin Dashboard Application
│   │   ├── templates/               # Dashboard HTML templates (orders, coupons, etc.)
│   │   ├── urls.py                  # Dashboard routing
│   │   └── views.py                 # Dashboard admin business logic
│   │
│   ├── storeapp/                    # Core Storefront Application
│   │   ├── static/                  # Static assets
│   │   │   ├── css/                 # Modernized modular stylesheets (style.css, cart.css, login.css)
│   │   │   └── js/                  # AJAX cart hooks and toast engine (toast.js)
│   │   ├── templates/               # Clean semantic HTML templates (index.html, base.html, shop.html)
│   │   ├── models.py                # Database schema (Products, Cart, Order, Coupon, Profile)
│   │   ├── urls.py                  # Storefront routing
│   │   └── views.py                 # Cart hooks, Razorpay callback, checkout views
│   │
│   ├── storeproject/                # Django project configurations
│   │   ├── settings.py              # Secure settings file reading variables from .env
│   │   └── urls.py                  # Root route configurations
│   │
│   ├── db.sqlite3                   # Synchronized SQLite database containing demo data
│   └── manage.py                    # Django administration script
│
├── .env                             # Local developer secrets (Ignored by Git)
├── .env.example                     # Environment setup template
└── .gitignore                       # Explicit files and folders ignored by Git
```

---

## 🔒 Security & Environment Setup

This project uses environment variables to secure credentials. A zero-dependency parser reads the settings dynamically when Django starts up.

### Environment Variable Guide

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `SECRET_KEY` | Secret cryptographic key used by Django. | `django-insecure-...` |
| `DEBUG` | Enables/Disables diagnostic debugger. | `True` for development, `False` for production |
| `ALLOWED_HOSTS` | Hosts allowed to run the website. | `127.0.0.1,localhost` |
| `RAZORPAY_KEY_ID` | API key from your Razorpay Dashboard. | `rzp_test_...` |
| `RAZORPAY_KEY_SECRET` | Secret key from your Razorpay Dashboard. | `Owffq...` |

### Getting Started with Secrets

1. Locate `.env.example` in the project root.
2. Duplicate or rename `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Update the credentials in `.env` with your actual development keys.

---

## ⚙️ Installation & Setup

Follow these steps to configure your local development environment:

### 1. Prerequisites
- Python 3.10+
- `pip` package manager

### 2. Configure Virtual Environment & Packages
Create and activate a virtual environment, then install requirements:

```bash
# Create environment
python -m venv environment

# Activate on Windows (cmd/powershell):
.\environment\Scripts\activate

# Install dependencies (if pip command works on your terminal)
pip install django pillow razorpay reportlab
```

### 3. Apply Database Migrations
Synchronize your local database schema with Django models:
```bash
python storeproject/manage.py migrate
```

### 4. Create an Admin Account
To create a fresh administrator credentials account:
```bash
python storeproject/manage.py createsuperuser
```

---

## 🖥️ Running the Platform

This project separates public storefront interactions and the custom business dashboard for optimal performance:

### Start the Storefront (Port 8000)
Runs the customer-facing shopping application:
```bash
python storeproject/manage.py runserver 8000
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your web browser.

### Start the Admin Dashboard (Port 8001)
Runs the internal store management application:
```bash
python storeproject/manage.py runserver 8001
```
Open **[http://127.0.0.1:8001/admin-panel/login/](http://127.0.0.1:8001/admin-panel/login/)** in your web browser.

---

## 🔑 Default Credentials (Development)

The local SQLite database (`db.sqlite3`) contains pre-configured categories, products, and admin privileges for rapid testing.

*   **Public Superuser Login**:
    *   **Username**: `admin`
    *   **Password**: `admin123`
*   **Admin Dashboard URL**: [http://127.0.0.1:8001/admin-panel/login/](http://127.0.0.1:8001/admin-panel/login/)

---

## 🧪 Testing the Platform

You can verify the codebase integrity by running Django's automated unit tests:

```bash
# Run the complete test suite
python storeproject/manage.py test
```

This validates model behaviors, middleware configurations, and context processors.

---

## ☁️ Render Deployment Guide

Follow these steps to deploy this Django application successfully on **Render**:

### 1. Create a Web Service
On your Render Dashboard, click **New +** and select **Web Service** (do *not* select Static Site). Link it to your GitHub repository `Fullstack_Python_Clothing_Store_Website`.

### 2. Configure Service Settings
- **Environment**: `Python`
- **Branch**: `master`
- **Build Command**:
  ```bash
  pip install -r requirements.txt && python storeproject/manage.py collectstatic --noinput && python storeproject/manage.py migrate
  ```
- **Start Command**:
  ```bash
  gunicorn --chdir storeproject --bind 0.0.0.0:$PORT storeproject.wsgi:application
  ```

### 3. Add Environment Variables
Under the **Environment** tab of your Render Web Service, add the following variables:
- `SECRET_KEY`: *[Insert a secure random string]*
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `fullstack-python-clothing-store-website.onrender.com`
- `RAZORPAY_KEY_ID`: *[Your Razorpay Test Key]*
- `RAZORPAY_KEY_SECRET`: *[Your Razorpay Test Secret]*

---

## ⚠️ Important Production Database Notes

1. **SQLite is Ephemeral**: By default, Render web services have ephemeral local storage. Since `db.sqlite3` is in `.gitignore`, it will not be deployed with your code. Running `python storeproject/manage.py migrate` during the build phase will create a fresh, empty SQLite database. Any changes made to this database (e.g. creating categories, products, or new user accounts) will be lost whenever your Render service restarts or is redeployed.
2. **How to Persist Data**:
   - **Render Persistent Disk**: You can attach a Persistent Disk to your Render Web Service (e.g. mounted at `/data/`) and configure the `DATABASES` setting in `settings.py` to point to `/data/db.sqlite3` instead of the project directory.
   - **Managed Database (Recommended)**: For production systems, provision a managed PostgreSQL database (e.g. via Render PostgreSQL), add `psycopg2-binary` and `dj-database-url` to your `requirements.txt`, and update `settings.py` to use the database URL connection string.
3. **How to Seed Initial Data**:
   If you want to copy your local products, categories, and setup to the hosted Render database, you can export your local database contents to a JSON fixture and load it during deployment:
   - **Step A: Export your local data** (run locally in your terminal):
     ```bash
     python storeproject/manage.py dumpdata --exclude=auth.permission --exclude=contenttypes --indent 4 > storeproject/seed_data.json
     ```
   - **Step B: Commit and push** `storeproject/seed_data.json` to GitHub.
   - **Step C: Update Render Build Command**:
     Update your Render Build Command to load this data after migrations:
     ```bash
     pip install -r requirements.txt && python storeproject/manage.py collectstatic --noinput && python storeproject/manage.py migrate && python storeproject/manage.py loaddata storeproject/seed_data.json
     ```



