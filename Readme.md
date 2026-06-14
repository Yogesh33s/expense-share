# Expense Share Application

## Project Overview

Expense Share is a full-stack web application designed to help users manage shared expenses within groups. Users can create groups, add and manage expenses, import expense data from CSV files, review import reports, and view balance summaries with settlement recommendations.

The application provides a complete workflow for tracking shared spending and determining how group members should settle outstanding balances.

---

## Live Deployment

### Frontend

https://expense-share-mu.vercel.app

### Backend API

https://expense-share-api-8t09.onrender.com

---

## Features

### Authentication

* User Registration
* User Login
* JWT Authentication
* Protected Routes
* Logout Functionality

### Dashboard

* User Welcome Screen
* Quick Navigation
* Summary Statistics
* Access to all major modules

### Group Management

* Create Groups
* View Groups
* Edit Groups
* Delete Groups
* Group Details View

### Expense Management

* Add Expenses
* Edit Expenses
* Delete Expenses
* View Expense Lists
* Associate Expenses with Groups
* Validation and Error Handling

### CSV Import

* Upload CSV Files
* Process Expense Records
* Detect Data Anomalies
* Generate Import Reports

### Import Report Viewer

* View Import History
* Inspect Processing Results
* Review Detected Anomalies
* View Processing Statistics

### Balance Dashboard

* Group Balances
* User Balances
* Net Balance Calculations
* Settlement Recommendations

### Settlement Recommendations

The application calculates optimized settlement transactions showing:

* Who should pay
* Who should receive
* Settlement amount

---

## Technology Stack

### Frontend

* React
* Vite
* React Router DOM
* Axios
* CSS

### Backend

* Flask
* Flask-CORS
* SQLAlchemy
* PyJWT

### Database

* SQLite

### Deployment

* Vercel (Frontend)
* Render (Backend)

---

## Project Structure

```text
expense-share/
│
├── src/
│   ├── backend/
│   │   ├── controllers/
│   │   ├── models/
│   │   ├── services/
│   │   └── app.py
│   │
│   ├── importer/
│   │
│   └── frontend/
│       ├── public/
│       ├── src/
│       │   ├── components/
│       │   ├── context/
│       │   ├── pages/
│       │   ├── routes/
│       │   ├── services/
│       │   └── App.jsx
│
├── README.md
├── DECISIONS.md
├── SCOPE.md
├── AI_USAGE.md
└── requirements.txt
```

---

## Database

The application uses SQLite for persistence.

Database file:

```text
expense_share.db
```

Main entities:

### Users

* id
* name
* email
* password_hash

### Groups

* id
* name
* description

### Group Members

* id
* user_id
* group_id

### Expenses

* id
* group_id
* paid_by
* amount
* description
* date

### Import Logs

* id
* filename
* status
* processed_rows
* skipped_rows
* anomaly_count

---

## Backend Setup

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Backend

```bash
python src/backend/app.py
```

Backend runs on:

```text
http://localhost:5000
```

Health Check:

```text
http://localhost:5000/health
```

---

## Frontend Setup

Navigate to frontend:

```bash
cd src/frontend
```

Install dependencies:

```bash
npm install
```

Run development server:

```bash
npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

## Production Build

```bash
cd src/frontend
npm run build
```

Build output:

```text
src/frontend/dist
```

---

## Environment Configuration

Frontend API configuration:

```env
VITE_API_URL=https://expense-share-api-8t09.onrender.com/api
```

Backend configuration:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///expense_share.db
```

---

## API Overview

### Authentication

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/profile/:id
```

### Groups

```text
GET    /api/groups
POST   /api/groups
PUT    /api/groups/:id
DELETE /api/groups/:id
```

### Expenses

```text
GET    /api/expenses
POST   /api/expenses
PUT    /api/expenses/:id
DELETE /api/expenses/:id
```

### Imports

```text
POST /api/imports
GET  /api/imports
GET  /api/imports/:id
```

### Balances

```text
GET /api/balances
GET /api/balances/settlements
```

---

## Testing

Backend Tests:

```bash
python src/backend/test_backend.py
```

Importer Tests:

```bash
python src/importer/test_importer.py
```

Frontend Build Verification:

```bash
npm run build
```

---

## Known Limitations

* SQLite is used for simplicity and local deployment.
* Free Render instances may take time to wake up after inactivity.
* Authentication profile retrieval uses a simplified implementation.
* UI styling is functional but can be further enhanced.

---

## Future Improvements

* PostgreSQL support
* User invitations to groups
* Real-time updates
* Advanced analytics dashboard
* Export reports to PDF
* Email notifications
* Improved UI/UX design
* Role-based permissions

---

## Author

Yogesh Ranwa

Developed as part of the Spreetail Assignment Submission.
