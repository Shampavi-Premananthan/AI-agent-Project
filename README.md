# Study & Project Planner Agent

A Study & Project Planner Agent built with **Python** and **Streamlit** that helps students plan weekly study sessions and projects by managing tasks, generating a smart timetable, and tracking progress.

## Features

- 📝 Task management  
  - Add, edit, complete, and delete tasks.  
  - Each task has: title, subject, deadline, estimated hours, and priority (High/Medium/Low).

- 📆 Weekly study plan generation  
  - Set your available study hours for each day (Mon–Sun).  
  - The planner automatically distributes study sessions across the week before each deadline.  
  - Highlights overdue and due-soon tasks.

- 📊 Progress & analytics  
  - Shows total tasks, completed tasks, and completion percentage.  
  - Displays per-subject planned hours for the generated week.

- 🤖 Agent-style behavior (optional)  
  - Simple reschedule button (e.g., “I missed today’s plan”) to regenerate the plan.  
  - Optional “instruction agent” hook where an LLM or rule-based logic can adjust priorities and hours.

---

## Tech Stack

- Python 3.x  
- Streamlit  
- Git (for version control)  

---

## Getting Started

These steps let anyone clone and run the app locally.

### 1. Clone the repository

```
git clone https://github.com/Shampavi-Premananthan/AI-agent-Project.git
cd AI-agent-Project
```

### 2. Create a virtual environment (optional but recommended)

```
# Windows (PowerShell)
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

If you have a `requirements.txt`, run:

```
pip install -r requirements.txt
```

If not, minimal install (for this project):

```
pip install streamlit
```

---

## Running the App

From the project folder:

```
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`) in your browser.

---

## How to Use

1. **Add tasks**  
   - Go to the “Tasks” tab.  
   - Enter title, subject, deadline, hours, and priority, then click **“Add task”**.  

2. **Manage tasks**  
   - Use **Done**, **Edit**, and 🗑 buttons to update or remove tasks.  
   - Filter tasks by subject and check progress metrics at the top.

3. **Generate weekly plan**  
   - Go to the “Weekly Plan” tab.  
   - Set your available hours for each day.  
   - Click **“Generate weekly plan”** to see day-wise sessions.  
   - Use **“I missed today’s plan”** (if enabled) to reschedule.

---

## Optional: AI Instruction Agent (if configured)

If you connect an LLM API (e.g., Gemini or OpenAI) and enable the instruction agent in `app.py`, you can:

- Type natural language instructions like:  
  - “Focus more on AI project and keep Friday light.”  
  - “Reduce Java on weekdays, move it to weekend.”  
- The agent will slightly adjust subject priorities and day weights before generating the plan.

(For now this may be optional / experimental; contributors can extend this part.)

---

## Project Structure

```
AI-agent-Project/
├── app.py           # Main Streamlit app
├── tasks.json       # Local storage for tasks (can be regenerated)
├── README.md        # Project documentation
└── ...              # Any additional modules or assets
```


---

## Contributions

Issues and pull requests are welcome.  
If you want to extend the agent (better scheduling logic, real LLM integration, calendar export, etc.), feel free to fork the repo and submit a PR.


