# **📂 JudgeMeNot Tabulation System**

**Project for App Dev, IAS, and SE Courses**

Welcome to the repository for the **JudgeMeNot** system\! This is a modular Flet application (Python) using a MySQL database.

## **👥 Team Roles & Assignments**

| Member | Role | Primary Responsibility |
| :---- | :---- | :---- |
| **Elmo** | **Lead Programmer** | Core Architecture, Database Models, Tabulation Logic, Routing (main.py) |
| **Teammate 1** | **UI/UX Developer** | **Login Screen** (views/login\_view.py) \- Design the interface for authentication. |
| **Teammate 2** | **Security UI Dev** | **Audit Log Viewer** (views/audit\_log\_view.py) \- Design the security reporting table. |
| **Docs Team** | **QA & Documentation** | Create test cases, update the User Manual, and maintain the Threat Model. |

---

**🛠️ Setting Up Your Environment (Do this first\!)**

Before you write any code, you must set up your laptop correctly.

### **1\. Clone the Repository**

Open your terminal or Git Bash and run:

```Bash

git clone \<YOUR\_GITHUB\_REPO\_LINK\_HERE\>  
cd JudgeMeNot\_System
```
### **2\. Create the Virtual Environment**

We use a virtual environment to keep our libraries organized. **Do not skip this.**

**Windows:**

```Bash

python \-m venv venv  
venv\\Scripts\\activate
```
*(If you see (venv) appear at the start of your command line, it worked\!)*

**Mac/Linux:**

```Bash

python3 \-m venv venv  
source venv/bin/activate
```
### **3\. Install Dependencies**

We have a list of required libraries (Flet, SQLAlchemy, etc.). Install them all at once:

```Bash

pip install \-r requirements.txt
```
*\> **Note:** Do not uninstall any libraries even if they look unfamiliar (e.g., anyio, httpx). Flet needs them to run.*

### **4\. Database Setup (MySQL)**

1. Make sure **XAMPP** (or MySQL Server) is running.  
2. Create a blank database named judgemenot\_db.  
3. Run our setup script to create the tables and the Admin user:  
   ```Bash  
   python init\_db.py
   ```
---

**🚀 How to Contribute (The Workflow)**

**⚠️ IMPORTANT:** Never push directly to the main branch. Always work on your own branch.

### **Step 1: Create a Branch**

Whenever you start a new task (e.g., "Designing Login"), create a new branch:

```Bash

git checkout \-b feature/login-screen
```
### **Step 2: Write Your Code**

You can test your specific file by adding this temporary code at the bottom of your file:

```Python

if \_\_name\_\_ \== "\_\_main\_\_":  
    ft.app(target=LoginView) \# Change to your function name
```
*Run it with python views/login\_view.py to see your work.*

### **Step 3: Push Your Changes**

Once you are happy with your code:

```Bash

git add .  
git commit \-m "Added layout for login screen"  
git push origin feature/login-screen
```
### **Step 4: Create a Pull Request (PR)**

1. Go to our GitHub page.  
2. You will see a button "Compare & Pull request". Click it.  
3. **I** will review your code and merge it into the main system.

---

**📂 Project Structure (Where things go)**

We are using a modular design. Please stick to these folders:

* core/ ➝ Settings and Database connection (Don't touch unless asked).  
* models/ ➝ Database Tables (User, Event, Score).  
* views/ ➝ **YOUR WORKSPACE.** All UI screens go here.  
* services/ ➝ Backend logic (Calculations, Auth checks).  
* main.py ➝ The entry point that runs the whole app.

---

**❓ FAQ / Troubleshooting**

Q: I get a "Module not found" error.  
A: You probably forgot to activate your virtual environment. Run venv\\Scripts\\activate. and install the requirements 
Q: The database isn't connecting.  
A: Check if XAMPP MySQL is running.  