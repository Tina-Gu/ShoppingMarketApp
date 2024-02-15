# Online Shopping App

This project consists of a Django-powered backend and an Angular-driven frontend designed to provide a comprehensive online shopping experience. The application allows users to register, login, view products, add them to a shopping cart or wishlist, and manage orders.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.8
- Django
- Node.js
- npm 
- Angular CLI

### Installing

#### Backend Setup

1. Clone the repository to your local machine.
2. Navigate to the backend directory where `requirements.txt` is located.
3. Install the required Python packages:
```pip install -r requirements.txt```
4. Apply the migrations to create the database schema:
```python manage.py migrate```
5. Start the Django development server:
```python manage.py runserver```



#### Frontend Setup

1. Navigate to the frontend directory where `package.json` is located.
2. Install the required npm packages:
```npm install```
3. Start the Angular development server:
```ng serve```
4. Open your web browser and go to `http://localhost:4200` to view the application.

### Development

- Use Django admin to manage backend models and data.
- Utilize Angular CLI for generating components, services, and other frontend elements.

