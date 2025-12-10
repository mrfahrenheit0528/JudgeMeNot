# **4\. Code Documentation**

## **4.1 Repository Structure**

.  
├── core/               \# Database config (Singleton pattern)  
├── models/             \# SQLAlchemy ORM Models  
├── services/           \# Business Logic (Calculations, Auth)  
├── views/              \# Flet UI Components  
│   ├── config/         \# Admin Configuration Screens  
│   └── ...             \# Dashboard, Login, Leaderboard views  
├── assets/             \# Images and static files  
├── main.py             \# Entry point & Routing  
└── init\_db.py          \# Database bootstrapper

## **4.2 Requirements (requirements.txt)**

* flet: The core UI framework.  
* sqlalchemy: ORM for database interaction.  
* pymysql: MySQL driver for Python.  
* bcrypt: Password hashing utility.  
* openpyxl: For exporting results to Excel.  
* reportlab: For generating PDF reports.  
* python-dotenv: Loading environment variables.

## **4.3 Key Algorithms**

### **Weighted Average Calculation (services/pageant\_service.py)**

Scores are calculated using a **hierarchical sum**: 

*Total = sum of all(SegmentScore * SegmentWeight)*

**Where:** 

*SegmentScore = sum of all(CriteriaAverage * CriteriaWeight)*

### **Deadlock Detection (services/quiz\_service.py)**

In the event of a tie for the final qualifying spot (e.g., Rank 5), the system checks:

1. Are scores identical?  
2. Is there a "Clean Winner" above the cutoff?  
3. If a tie exists at the cutoff boundary, the system prompts the Admin to generate a **Clincher Round** specifically for the tied participants.

## **4.4 Emerging Technologies**
Real-Time Data Streaming
The system uses a real-time data streaming layer for Quiz Bee competitions to instantly synchronize point-based scores across all connected devices. 

Tabulators input results for each question as Correct or Wrong, and the system automatically calculates team scores in real-time. Administrators and audience screens receive immediate updates, ensuring accurate and transparent scoring. 

This layer relies on a stable local network and a single host server to distribute updates without delay.

* **Flet (Flutter for Python):** Allows for rapid prototyping of reactive UIs without learning Dart/JavaScript.  
* **ReportLab PDF Gen:** Programmatic generation of vector-based PDFs ensures high-quality printouts for official signing.