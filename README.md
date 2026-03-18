✈️ RoamBudget
RoamBudget is a full-stack group travel expense coordinator designed to help friends track, split, and manage trip costs in real-time. No more "who owes what" spreadsheets—just a clean interface to keep the trip stress-free.

🚀 Features
Real-time Tracking: Add expenses instantly as they happen.

Automatic Splitting: Calculates "Cost Per Person" dynamically based on group size.

Category Analytics: Visual breakdown of spending (Lodging, Food, Transport, etc.).

Mobile Responsive: A Tailwind-powered frontend that works on any device.

RESTful API: A high-performance FastAPI backend connected to a PostgreSQL database.

🛠️ Tech Stack
Backend: FastAPI (Python)

Database: Supabase (PostgreSQL)

Frontend: HTML5, JavaScript (ES6+), and Tailwind CSS

Deployment: Render (API) and GitHub Pages (Web)

📖 API Documentation
The API follows REST principles and includes built-in Swagger documentation:

Base URL: https://your-new-render-url.onrender.com

Interactive Docs: /docs

Endpoints
GET /expenses - Retrieve all trip expenses.

POST /expenses - Create a new expense entry.

PATCH /expenses/{id} - Update specific expense details.

DELETE /expenses/{id} - Remove an expense.

🔧 Installation & Setup
Clone the repository:

Bash
git clone https://github.com/CodeBryce/RoamBudget.git
Install dependencies:

Bash
pip install -r requirements.txt
Environment Variables:
Set up a .env file with your Supabase credentials:

Plaintext
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here
