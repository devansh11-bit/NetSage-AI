# NetSage AI

NetSage AI is a Cisco Virtual Internship project: an AI-assisted network troubleshooting platform built with Python and Streamlit.

## Project status

This repository currently contains only the initial project structure. Application logic will be added one module at a time.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. When the Streamlit interface is implemented, it will be started with:

   ```powershell
   streamlit run app.py
   ```

## Gemini setup

To use the optional AI Diagnosis page, create a `.env` file in the project root and add your Gemini API key:

```text
GEMINI_API_KEY=your_api_key_here
```

The app uses Gemini only to generate an advisory diagnosis. It never applies network configuration changes.

## Project structure

```text
NetSage-AI/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── cases.csv
│   └── audit_log.csv
├── src/
│   ├── checker.py
│   ├── ai_engine.py
│   ├── parser.py
│   ├── dashboard.py
│   └── logger.py
├── assets/
└── prompts/
```

## Folders and files

- `app.py` — future Streamlit entry point.
- `data/` — local project data, including troubleshooting cases and audit records.
- `src/` — Python modules, separated by responsibility to keep the app easy to understand.
- `assets/` — future static files such as images, icons, or styling assets.
- `prompts/` — future AI prompt templates, kept separate from Python code.
- `requirements.txt` — Python packages needed to run the project.
- `README.md` — setup instructions and project documentation.
