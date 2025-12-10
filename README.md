# **JudgeMeNot Tabulation System**

**Project for App Dev, IAS, and SE Courses**

Welcome to the repository for the **JudgeMeNot** system\! This is a modular **Flet** application (Python) designed to provide a secure, real-time tabulation solution for school events, pageants, and quiz bees.

## **About the Project**

**JudgeMeNot** replaces traditional paper-based scoring with a digital, automated platform. It ensures transparency and accuracy by allowing Judges to submit scores via a secure interface while the system automatically calculates weighted averages and rankings in real-time.

### **Key Features**

* **Event Flexibility:** Supports both **Pageants** (Criteria-based scoring) and **Quiz Bees** (Right/Wrong scoring with clincher rounds).  
* **Real-Time Tabulation:** Leaderboards update instantly as scores are submitted.  
* **Role-Based Security:** Distinct portals for **Admins**, **Judges**, **Tabulators**, and **Viewers**.  
* **Audit Logging:** Tracks every login, score submission, and configuration change for security compliance (IAS).  
* **Automated Reports:** One-click generation of official results in **PDF** and **Excel** formats.

## **Tech Stack**

* **Frontend & Backend:** [Flet](https://flet.dev/) (Python)  
* **Database:** MySQL (8.0+)  
* **ORM:** SQLAlchemy  
* **Security:** bcrypt for password hashing  
* **Reporting:** reportlab (PDF), openpyxl (Excel)

## **Quick Start Guide**

### **1\. Clone the Repository**

git clone \<YOUR\_REPO\_LINK\>  
cd JudgeMeNot\_System

### **2\. Set Up Virtual Environment**

It is highly recommended to use a virtual environment to manage dependencies.

\# Windows  
python \-m venv venv  
venv\\Scripts\\activate

\# Mac/Linux  
python3 \-m venv venv  
source venv/bin/activate

### **3\. Install Dependencies**

pip install \-r requirements.txt

### **4\. Configure Database**

1. Ensure **XAMPP** (or MySQL Server) is running.  
2. Create an empty database named judgemenot\_db.  
3. Run the initialization script to create tables and the default Admin account:  
   python init\_db.py

   **Default Admin Credentials:**  
   * Username: admin  
   * Password: admin123

### **5\. Run the Application**

flet run main.py

*The app will launch in your default web browser or as a desktop window.*

## **Project Structure**

JudgeMeNot\_System/  
├── core/               \# Database connection & settings  
├── models/             \# Database Tables (SQLAlchemy Models)  
├── services/           \# Business Logic (Calculations, Auth, Export)  
├── views/              \# UI Screens (Login, Dashboard, Scoring)  
├── assets/             \# Images and static files  
├── main.py             \# Application Entry Point & Routing  
└── init\_db.py          \# Database setup script

## **Team Roles & Assignments**

| Member Name | Role | Primary Responsibilities |
| :---- | :---- | :---- |
| **Guiller Angelo Hermoso** | **Project Lead / Backend, UI, Documentation**  | Core architecture, database design, tabulation logic (Pageant/Quiz) |
| **John Careal Morandarte** | **Frontend & Design, QA, Documentation**  | UI implementation (Flet), responsive design, Judges' interface, Leaderboard visualization. (and other assigned tasks) |
| **Harvey Lloyd Palacios** | **Security & QA, Documentation, Frontend**  | Audit logging implementation, user role verification, testing strategies, security compliance. (and other assigned tasks) |

## **License**

This project is created for academic purposes.
