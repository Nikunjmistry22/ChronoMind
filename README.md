# ChronoMind - Vibe Coding Project
**Entirely created by Claude AI with no involvement of human coding, apart from defining the use case and how AI can be applied.**

ChronoMind is an **agentic AI project** that allows users to **record or write text**, automatically transcribes recordings, analyzes text using **Google Gemini**, and structures insights (like timesheets) into a **CSV format**.

It’s designed for **personal productivity**, helping you capture, understand, and organize your daily notes, thoughts, or time logs seamlessly.

---

## Features

-  **Voice & Text Input** — Accepts both recorded audio and typed text.  
-  **Gemini AI Integration** — Uses Google’s Gemini model for transcription, text analysis, and structured data generation.  
-  **CSV Export** — Automatically generates structured outputs.  
-  **Agentic Context Awareness** — Learns from your “knowledge base.”  
-  **Custom Schema** — You define your own JSON schema for storing the extracted data.

---

##  High-Level Architecture

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/f34bbff5-b6bd-41c4-94c7-d323c46e36f3" />

---
##  Live Demo Pics

*Cannot Show confidential information of my personal timesheet sorry for the inconvinence.*

<img width="1366" height="686" alt="image (10)" src="https://github.com/user-attachments/assets/2cbd9939-f2f0-4ddc-83af-4399532fcddc" />

<img width="1180" height="635" alt="image (11)" src="https://github.com/user-attachments/assets/c87df54e-c0b0-4e98-a719-b9122f34dcca" />

<img width="1118" height="387" alt="image (13)" src="https://github.com/user-attachments/assets/58a3339c-0163-4237-9266-627e243a88a6" />

<img width="1131" height="584" alt="image (14)" src="https://github.com/user-attachments/assets/a4645470-ba53-4abc-8fab-875316b0ee1f" />

---

##  Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/chronomind.git
cd chronomind
```

### 2️⃣ Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

##  Environment Variables

Create a `.env` file in the project root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

###  How to get your Gemini API key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Log in with your Google account
3. Navigate to **Settings → API key**
4. Click **Create API Key**
5. Copy it and paste into your `.env` file as shown above

---

##  Knowledge Base Setup

ChronoMind uses a custom JSON-based knowledge base that defines the schema of information you want to extract.

Create a file named `knowledge_base.json` in your project root:

```json
[
  {
    "client_code": "C-999",
    "project_name": "Hackathon",
    "project_code": "HACK-01",
    "project_state": "Active",
    "phase": "",
    "phase_id": "",
    "task": "Development",
    "task_id": "HACK-01-1"
  },
  {
    "client_code": "C-001",
    "project_name": "XYZ Project",
    "project_code": "XYZ-2024",
    "project_state": "Active",
    "phase": "Implementation",
    "phase_id": "XYZ-P2",
    "task": "Backend Integration",
    "task_id": "XYZ-2024-5"
  }
]
```

You can modify it anytime — ChronoMind dynamically adapts the Gemini prompt to your defined schema.

**To use your own schema:** Modify the system prompt JSON format inside `app.py` and the `knowledge_base.json` file.

---

## ▶️ Run the Application

```bash
python app.py
```

Server starts at: **http://localhost:5000**

### From the UI:

1. Upload an audio file or enter text manually
2. Gemini will analyze and convert it into structured data
3. Export results as CSV

---

##  Example

### Input (voice/text):

> "On Monday, I worked on backend integration for 3 hours and fixed the S3 upload bug for the XYZ project. Then, I spent 2 hours on UI improvements for the ABC project."

### Output (CSV):

The system prompt considers **Monday to be in the current week**, so the date for the current week's Monday will be used in the `entry_date` column.

| entry_date | project_code | client_code | project_name    | task_name       | duration_minutes | comment                | billing_classification |
|------------|--------------|-------------|-----------------|-----------------|------------------|------------------------|------------------------|
| 2025-10-13 | XYZ          | CLIENT_A    | XYZ Project     | Backend Fix     | 180              | Fixed S3 upload bug    | Billable               |
| 2025-10-13 | ABC          | CLIENT_B    | ABC Project     | UI Enhancement  | 120              | UI improvements        | Billable               |

---

## Pros of ChronoMind

-  **Gemini-powered intelligence** for accurate transcription and contextual understanding
-  **Agentic workflow** with dynamic context retention
-  **Personalized & private** — run locally with your own schema
-  **Highly customizable** — adapt to journals, meeting notes, or project logs
-  **Secure** — no data sharing unless explicitly configured

---

## Tech Stack

- **Language:** Python
- **Framework:** Flask
- **AI Model:** Gemini API
- **Data Handling:** Pandas, CSV
- **Configuration:** `.env` for secrets
- **Optional Integrations:** AWS S3, GCP Storage (Scalability)

---

## License

This project is licensed under the [MIT License](LICENSE).

---
