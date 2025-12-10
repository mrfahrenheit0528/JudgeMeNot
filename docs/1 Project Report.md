# **1\. Project Report: JudgeMeNot**

## **1.1 Executive Summary**

**JudgeMeNot** is a comprehensive, real-time tabulation system designed to modernize the scoring process for school events, pageants, and quiz bees. Traditional paper-based scoring is prone to calculation errors, slow results processing, and a lack of transparency. JudgeMeNot addresses these issues by providing a centralized, secure platform where Administrators configure events, Judges submit scores digitally, and Tabulators/Viewers witness real-time updates.

The system ensures data integrity through Role-Based Access Control (RBAC), automated calculation engines, and immutable audit logging, making it suitable for high-stakes internal organizational competitions.

## **1.2 Framework Chosen & Rationale**

**Core Framework: Flet (Python)**

* **Rationale:** Flet was selected for its ability to build multi-platform (Web, Desktop, Mobile) applications using a single Python codebase. This streamlined the development process by eliminating the need for separate frontend (JS/React) and backend languages, allowing the team to focus on complex tabulation logic.  
* **Database:** MySQL with SQLAlchemy ORM.  
* **Rationale:** Relational data storage was essential for the complex web of relationships between Events, Segments, Criteria, and Scores. SQLAlchemy provides secure, Pythonic database interactions, mitigating SQL injection risks.

## **1.3 Implemented Features**

### **Baseline Features**

1. **User Authentication:** Secure Login/Signup with password hashing (bcrypt).  
2. **Event Management:** CRUD operations for Pageants and Quiz Bees.  
3. **Dynamic Scoring:** Configurable segments (Prelims/Finals), criteria, and weights.  
4. **Real-time Tabulation:** Automated ranking and weighted average calculations.  
5. **RBAC:** distinct roles for Admins, Judges, Tabulators, and Viewers.

### **Enhancements (Emerging Tech & Advanced Logic)**

1. **Security Audit Logging:** Tracks sensitive actions (Login, Score Submission, Data Deletion) in a tamper-evident audit\_logs table.  
2. **Mobile "Kiosk" Mode:** Detects mobile User Agents (e.g., Android) and automatically locks the interface to the "Leaderboard/Viewer" mode to prevent unauthorized admin access on public display tablets.  
3. **Export Engine:** Generates official reports in Excel (.xlsx) and formatted PDF (.pdf) using openpyxl and reportlab.  
4. **Live Quiz Bee Mode:** Specialized interface with progress bars, deadlock detection, and automated "Clincher" round generation for tie-breaking.

## **1.4 Architecture & Module Overview**

The system follows a **Monolithic Service-Repository Pattern**.

* **Views (views/):** Handles UI rendering and user interaction (Flet Controls).  
* **Services (services/):** Contains business logic (e.g., PageantService for calculations, AuthService for security).  
* **Models (models/):** SQLAlchemy classes defining the database schema.  
* **Core (core/):** Database connection management and session handling.

**Diagram:**

```text
┌─────────────────────────────────────────────┐
│ Client Devices (Admin, Judges, Tabulators,  │
│ Audience Screens)                           │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Flet App                                    │
│ (UI + Event Logic)                          │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Security & Access Control                   │
│ (Authentication, Role-Based Access, Hashing)│
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Local Database                              │
│ (MySQL)                                     │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Real-Time Score Synchronization             │
│ (Ensures all devices see updated scores     │
│ instantly)                                  │
└─────────────────────────────────────────────┘

```

## **1.5 Threat Model & Security Controls**

| Threat | Risk Level | Mitigation / Control |
| :---- | :---- | :---- |
| **Score Manipulation** | High | **RBAC:** Judges can only score active segments. Once submitted, scores are locked. **Audit Logs:** Every score submission is timestamped and recorded. |
| **Unauthorized Access** | High | **Hashing:** Passwords stored using bcrypt. **Role Checks:** Middleware-like checks in main.py redirect unauthorized users. |
| **SQL Injection** | Medium | **ORM:** Use of SQLAlchemy parameterized queries prevents direct SQL injection. |
| **Kiosk Escape** | Low | **User-Agent Detection:** Mobile devices are forced into a read-only View mode via main.py. |

## **1.6 Design Decisions & Trade-offs**

* **Short Polling vs. WebSockets:**  
  * *Decision:* We used threaded Short Polling (checking DB every 2-3 seconds) for real-time score updates.  
  * *Trade-off:* While WebSockets are more efficient, Polling was simpler to implement within Flet's constraint and is sufficient for local network traffic (\<50 users).  
* **Local Database:**  
  * *Decision:* Application connects to a local MySQL instance.  
  * *Trade-off:* Requires the host machine to be on the same LAN as the judges. Simplifies deployment but limits remote access.

## **1.7 Limitations & Future Work**

* **Limitations:** The system currently relies on the host machine's local IP address. If the server IP changes, clients must be re-informed.  
* **Future Work:**  
  * Implement WebSocket support for instant, push-based updates.  
  * Cloud deployment for remote judging capabilities.  
  * Biometric login integration.