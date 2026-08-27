# 🌐 NetSage AI
### AI-Assisted Cisco Network Diagnostic Platform

## 📌 Overview

NetSage AI is an intelligent network troubleshooting platform developed as part of the Cisco Virtual Internship. It combines deterministic rule-based validation with Google Gemini AI to assist network engineers in diagnosing Cisco network issues quickly and accurately.

The platform analyzes network case data, validates configurations using predefined Cisco rules, generates AI-powered diagnostic recommendations, and records engineer decisions through an audit workflow.

---

## 🎯 Problem Statement

Network troubleshooting is often time-consuming and requires experienced engineers to analyze large amounts of device output.

NetSage AI reduces troubleshooting time by:
- Performing deterministic Cisco rule validation
- Generating AI-assisted root cause analysis
- Requiring human approval before implementation
- Maintaining a complete audit trail of engineer decisions

---

## ✨ Features

- 📂 Load and review Cisco network cases
- 🔍 Deterministic Rule Checker
- 🤖 AI Diagnosis using Google Gemini
- 👨‍💻 Engineer Review (Approve / Edit / Reject)
- 📝 Engineer Notes
- 📊 Interactive Dashboard Analytics
- 📈 Plotly Charts
- 📁 Audit Log Management
- 📥 Download Audit Log
- 🎨 Cisco-inspired Streamlit interface

---

## 🛠️ Technology Stack

### Frontend
- Streamlit

### Backend
- Python

### AI
- Google Gemini API

### Data Processing
- Pandas

### Visualization
- Plotly

### Configuration
- Python Dotenv

---

## 🏗️ System Workflow

1. User selects a network case.
2. Rule Checker analyzes Cisco show outputs.
3. Gemini AI generates a diagnosis.
4. Engineer reviews the recommendation.
5. Decision is stored in the Audit Log.
6. Dashboard updates analytics automatically.

---

## 📂 Project Structure

```text
NetSage-AI/
│── app.py
│── requirements.txt
│── README.md
│── .env
│
├── data/
│   ├── cases.csv
│   └── audit_log.csv
│
├── src/
│   ├── ai_engine.py
│   ├── checker.py
│   ├── dashboard.py
│   ├── logger.py
│   └── parser.py
│
├── assets/
└── prompts/
```

---

## 🚀 Installation

### Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/NetSage-AI.git
```

### Navigate to the project

```bash
cd NetSage-AI
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure Gemini API

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

### Run the application

```bash
streamlit run app.py
```

---

## 📊 Dashboard Features

- Total Cases
- Cases Reviewed
- AI Diagnoses Generated
- Approval Rate
- Issue Distribution
- Severity Distribution
- OSI Layer Distribution
- Engineer Decision Analytics
- Recent Activity

---

## 🔐 Human-in-the-Loop Workflow

NetSage AI does not automatically apply configuration changes.

Every AI recommendation must be reviewed by a network engineer before implementation.

Available decisions:
- ✅ Approve
- ✏️ Edit Recommendation
- ❌ Reject

---

## 📸 Screenshots

Add screenshots of:

- Dashboard
- Case Review
- Rule Validation
- AI Diagnosis
- Engineer Review
- Audit Log

---

## 🔮 Future Enhancements

- Multi-device troubleshooting
- Live Cisco device integration
- Automated configuration validation
- Multi-user authentication
- Real-time monitoring
- Predictive network analytics

---

## 👥 Team

**Cisco Virtual Internship Project**

Team Members:

- Devansh Soni
- Janhvi Hardainiya
---

## 🙏 Acknowledgements

- Cisco Networking Academy
- Google Gemini API
- Streamlit
- Plotly
- Python Community

---

## 📄 License

This project was developed for educational purposes as part of the Cisco Virtual Internship Program.