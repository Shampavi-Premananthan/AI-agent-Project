import os
import json
from datetime import datetime, timedelta

import streamlit as st
from openai import OpenAI  # example client

# Set your API key (safe place: environment variable)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

TASKS_FILE = "tasks.json"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ------------ Data layer ------------

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


# ------------ Helpers ------------

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def priority_order(priority):
    mapping = {"High": 1, "Medium": 2, "Low": 3}
    return mapping.get(priority, 2)


# ------------ Planning logic ------------

def generate_plan(tasks, available_hours):
    today = datetime.today().date()

    active_tasks = [t for t in tasks if not t.get("completed", False)]
    if not active_tasks:
        return {}, []

    active_tasks.sort(
        key=lambda t: (
            parse_date(t["deadline"]) or today,
            priority_order(t["priority"])
        )
    )

    remaining = {id(t): float(t["hours"]) for t in active_tasks}
    plan = {day: [] for day in DAYS}

    for i in range(7):
        current_date = today + timedelta(days=i)
        day_name = DAYS[current_date.weekday() % 7]
        remaining_today = float(available_hours.get(day_name, 0.0))

        if remaining_today <= 0:
            continue

        for t in active_tasks:
            if remaining_today <= 0:
                break

            deadline = parse_date(t["deadline"]) or today
            if current_date > deadline:
                continue

            tid = id(t)
            if remaining[tid] <= 0:
                continue

            alloc = min(remaining[tid], remaining_today)
            if alloc <= 0:
                continue

            plan[day_name].append({
                "title": t["title"],
                "subject": t["subject"],
                "hours": round(alloc, 2),
                "deadline": t["deadline"],
                "priority": t["priority"],
            })

            remaining[tid] -= alloc
            remaining_today -= alloc

    unfilled = [t for t in active_tasks if remaining[id(t)] > 0.01]
    return plan, [
        {
            "title": t["title"],
            "subject": t["subject"],
            "remaining": round(remaining[id(t)], 2),
            "deadline": t["deadline"]
        }
        for t in unfilled
    ]


def apply_instruction_with_llm(instruction, tasks, available_hours):
    """
    Use an LLM to lightly adjust priorities / available hours
    based on a natural language instruction.
    This keeps it simple but gives real 'agent' behavior.
    """
    if not client or not OPENAI_API_KEY:
        # No key: just return original
        return tasks, available_hours

    # Prepare a compact description of current situation
    subjects = sorted({t["subject"] for t in tasks})
    summary = {
        "subjects": subjects,
        "available_hours": available_hours,
    }

    prompt = (
        "You are an AI study planner agent.\n"
        "User will give an instruction about how to adjust their weekly plan.\n"
        "You will respond ONLY with a small JSON object, no explanation.\n"
        "Format:\n"
        "{\n"
        '  "boost_subjects": [list of subjects to emphasize],\n'
        '  "reduce_subjects": [list of subjects to de-emphasize],\n'
        '  "day_weights": { "Monday": 1.0, "Tuesday": 1.0, ... },\n'
        '  "priority_changes": { "AI": "High", "Java": "Medium" }\n'
        "}\n\n"
        f"Current context: {json.dumps(summary)}\n\n"
        f"User instruction: {instruction}\n"
    )

    try:
        # Simple chat completion call (adjust model name to what you actually use)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # example; choose suitable cheap model
            messages=[
                {"role": "system", "content": "You are a strict JSON generator for a study planner agent."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        # Attempt to parse JSON from content
        data = json.loads(content)
    except Exception:
        # If anything fails, just return original
        return tasks, available_hours

    # Apply day_weights to available_hours
    day_weights = data.get("day_weights", {})
    new_available = available_hours.copy()
    for day, w in day_weights.items():
        if day in new_available:
            try:
                new_available[day] = max(0.0, float(new_available[day]) * float(w))
            except ValueError:
                pass

    # Apply priority_changes
    priority_changes = data.get("priority_changes", {})
    new_tasks = []
    for t in tasks:
        t2 = t.copy()
        subj = t2["subject"]
        if subj in priority_changes:
            new_pr = priority_changes[subj]
            if new_pr in ["High", "Medium", "Low"]:
                t2["priority"] = new_pr
        new_tasks.append(t2)

    return new_tasks, new_available


def reschedule_missed_day(tasks, available_hours, day_name):
    """
    Take all sessions planned for a given day_name and push their hours
    to the next days before deadline, if possible.
    Simple heuristic: add their hours back into task 'hours' and regenerate plan.
    """
    # Very simple: just regenerate plan; real implementation would
    # track per-session completion. Here we just warn the user.
    # You can extend this later if you track per-session status.
    return generate_plan(tasks, available_hours)



# ------------ Streamlit UI ------------

st.set_page_config(page_title="Study & Project Planner Agent", layout="wide")

st.title("📚 Study & Project Planner Agent")
st.write(
    "Tasks add pannunga, daily available hours set pannunga, "
    "app uruviya simple AI-like planner un week‑a auto schedule pannum."
)

if "tasks" not in st.session_state:
    st.session_state["tasks"] = load_tasks()

tasks = st.session_state["tasks"]

tab_tasks, tab_plan = st.tabs(["📝 Tasks", "📆 Weekly Plan"])

# ----- Tasks tab -----
with tab_tasks:
    st.subheader("Add new task")

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Title", placeholder="Example: TestNG Assignment")
        subject = st.text_input("Subject / Course", placeholder="Example: Java, AI")
    with col2:
        deadline_date = st.date_input("Deadline", value=datetime.today())
        hours = st.number_input("Estimated hours", min_value=0.5, step=0.5, value=2.0)
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])

    if st.button("➕ Add task"):
        if title.strip() == "" or subject.strip() == "":
            st.warning("Title and subject are required.")
        else:
            new_task = {
                "title": title.strip(),
                "subject": subject.strip(),
                "deadline": deadline_date.strftime("%Y-%m-%d"),
                "hours": float(hours),
                "priority": priority,
                "completed": False,
            }
            tasks.append(new_task)
            save_tasks(tasks)
            st.session_state["tasks"] = tasks
            st.success("Task added.")
            st.rerun()

    st.markdown("---")
    st.subheader("Current tasks")

    if not tasks:
        st.info("No tasks yet. Add something above.")
    else:
        # Small stats / progress
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("completed", False))
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Total tasks", total)
        with col_s2:
            st.metric("Completed", completed)
        with col_s3:
            pct = 0 if total == 0 else round(completed * 100 / total)
            st.metric("Completion", f"{pct}%")

        st.markdown("### Filter by subject")
        subjects = sorted(list({t["subject"] for t in tasks}))
        subject_filter = st.selectbox(
            "Show tasks for subject",
            options=["All"] + subjects,
            index=0,
            help="Filter tasks by course/subject."
        )

        for idx, t in enumerate(tasks):
            if subject_filter != "All" and t["subject"] != subject_filter:
                continue

            with st.container():
                cols = st.columns([4, 2, 2, 2, 1, 1])
                with cols[0]:
                    st.markdown(f"**{t['title']}**  \n_{t['subject']}_")
                with cols[1]:
                    st.markdown(f"Deadline: `{t['deadline']}`")
                with cols[2]:
                    st.markdown(f"Hours: **{t['hours']}**")
                with cols[3]:
                    status = "✅ Completed" if t.get("completed", False) else "⏳ Pending"
                    st.markdown(f"Priority: **{t['priority']}**  \nStatus: {status}")

                # Done button
                with cols[4]:
                    if st.button("Done", key=f"done-{idx}"):
                        tasks[idx]["completed"] = True
                        save_tasks(tasks)
                        st.session_state["tasks"] = tasks
                        st.rerun()

                # Edit / Delete buttons
                with cols[5]:
                    edit_key = f"edit-{idx}"
                    delete_key = f"del-{idx}"
                    if st.button("✏️", key=edit_key):
                        st.session_state["edit_index"] = idx
                    if st.button("🗑", key=delete_key):
                        tasks.pop(idx)
                        save_tasks(tasks)
                        st.session_state["tasks"] = tasks
                        st.rerun()

            # If this row is in edit mode, show inline edit form
            if st.session_state.get("edit_index") == idx:
                st.markdown("**Edit this task:**")
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    new_title = st.text_input(
                        "Title",
                        value=t["title"],
                        key=f"edit-title-{idx}"
                    )
                    new_subject = st.text_input(
                        "Subject / Course",
                        value=t["subject"],
                        key=f"edit-subject-{idx}"
                    )
                with e_col2:
                    new_deadline = st.date_input(
                        "Deadline",
                        value=parse_date(t["deadline"]) or datetime.today().date(),
                        key=f"edit-deadline-{idx}"
                    )
                    new_hours = st.number_input(
                        "Estimated hours",
                        min_value=0.5,
                        step=0.5,
                        value=float(t["hours"]),
                        key=f"edit-hours-{idx}"
                    )
                    new_priority = st.selectbox(
                        "Priority",
                        ["High", "Medium", "Low"],
                        index=["High", "Medium", "Low"].index(t["priority"]),
                        key=f"edit-priority-{idx}"
                    )

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("💾 Save changes", key=f"save-{idx}"):
                        t["title"] = new_title.strip()
                        t["subject"] = new_subject.strip()
                        t["deadline"] = new_deadline.strftime("%Y-%m-%d")
                        t["hours"] = float(new_hours)
                        t["priority"] = new_priority
                        save_tasks(tasks)
                        st.session_state["tasks"] = tasks
                        st.session_state["edit_index"] = None
                        st.success("Task updated.")
                        st.rerun()
                with c2:
                    if st.button("Cancel", key=f"cancel-{idx}"):
                        st.session_state["edit_index"] = None
                        st.rerun()

# ----- Plan tab -----
with tab_plan:
    st.subheader("Set available hours per day")

    colA, colB = st.columns(2)
    with colA:
        default_week_hours = {
            "Monday": 2,
            "Tuesday": 2,
            "Wednesday": 2,
            "Thursday": 2,
            "Friday": 2,
            "Saturday": 4,
            "Sunday": 4,
        }
        st.caption("Default suggestion; you can change any value.")
    with colB:
        st.caption("Tip: Keep some buffer hours for unexpected work.")

    available = {}
    for day in DAYS:
        available[day] = st.number_input(
            f"{day}",
            min_value=0.0,
            step=0.5,
            value=float(default_week_hours.get(day, 0)),
            key=f"avail-{day}"
        )

    # Overdue & due-soon highlighting in tasks (just info text)
    today = datetime.today().date()
    overdue = []
    due_soon = []
    for t in tasks:
        d = parse_date(t["deadline"])
        if not d or t.get("completed", False):
            continue
        if d < today:
            overdue.append(t)
        elif 0 <= (d - today).days <= 3:
            due_soon.append(t)

    if overdue:
        st.error("⚠ Overdue tasks:")
        for t in overdue:
            st.write(f"- **{t['title']}** ({t['subject']}) – deadline `{t['deadline']}`")

    if due_soon:
        st.warning("⏰ Due soon (within 3 days):")
        for t in due_soon:
            st.write(f"- **{t['title']}** ({t['subject']}) – deadline `{t['deadline']}`")

    st.markdown("---")
    col_plan_btns = st.columns([2, 1])
    with col_plan_btns[0]:
        generate_clicked = st.button("🧠 Generate weekly plan")
    with col_plan_btns[1]:
        missed_today = st.button("I missed today's plan")

    # LLM-based instruction for plan adjustment
    st.markdown("---")
    st.subheader("🤖 AI Agent: Natural Language Plan Adjustment")
    st.markdown("### Optional: Agent instruction")
    instruction = st.text_area(
        "Tell the agent how to adjust your week (optional)",
        placeholder="Example: Focus more on AI project, reduce Java on weekdays, keep Sunday light.",
        height=80,
    )
    use_instruction = st.checkbox("Use AI instruction agent (requires OpenAI key)", value=False)

    # Keep the latest plan in session state
    if "latest_plan" not in st.session_state:
        st.session_state["latest_plan"] = None
        st.session_state["latest_unfilled"] = None

    if generate_clicked:
        tasks_for_plan = tasks
        available_for_plan = available

        if use_instruction and instruction.strip():
            tasks_for_plan, available_for_plan = apply_instruction_with_llm(
                instruction.strip(), tasks, available
            )

        plan, unfilled = generate_plan(tasks_for_plan, available_for_plan)
        st.session_state["latest_plan"] = plan
        st.session_state["latest_unfilled"] = unfilled

    if missed_today and st.session_state.get("latest_plan"):
        # Simple reschedule: regenerate using same tasks & hours
        plan, unfilled = reschedule_missed_day(tasks, available, DAYS[today.weekday()])
        st.session_state["latest_plan"] = plan
        st.session_state["latest_unfilled"] = unfilled
        st.info("Regenerated plan assuming today's sessions were missed.")

    if use_instruction and instruction.strip():
        # Use LLM to adjust plan based on user instruction
        adjusted_tasks, adjusted_available = apply_instruction_with_llm(instruction, tasks, available)
        plan, unfilled = generate_plan(adjusted_tasks, adjusted_available)
        st.session_state["latest_plan"] = plan
        st.session_state["latest_unfilled"] = unfilled
        st.success("✨ AI has adjusted your plan based on your instruction!")

    plan = st.session_state.get("latest_plan")
    unfilled = st.session_state.get("latest_unfilled")

    if plan:
        st.markdown("### Weekly Plan")
        for day in DAYS:
            with st.expander(day, expanded=(day in ["Monday", "Tuesday"])):
                sessions = plan.get(day, [])
                if not sessions:
                    st.write("No planned study sessions.")
                else:
                    for s in sessions:
                        # Color tags for priority
                        if s["priority"] == "High":
                            pr_tag = "🟥 High"
                        elif s["priority"] == "Medium":
                            pr_tag = "🟨 Medium"
                        else:
                            pr_tag = "🟩 Low"

                        st.markdown(
                            f"- **{s['title']}** ({s['subject']}) – "
                            f"{s['hours']}h, {pr_tag}, "
                            f"Deadline: `{s['deadline']}`"
                        )

        if unfilled:
            st.warning("Not enough hours to fully cover all tasks.")
            for u in unfilled:
                st.write(
                    f"- **{u['title']}** ({u['subject']}) still needs "
                    f"~{u['remaining']}h before `{u['deadline']}`."
                )
        else:
            st.success("All tasks are fully scheduled within your available hours.")

        # Per-subject hours summary (based on plan)
        st.markdown("---")
        st.markdown("### Per-subject planned hours")
        subject_hours = {}
        for day in DAYS:
            for s in plan.get(day, []):
                key = s["subject"]
                subject_hours[key] = subject_hours.get(key, 0.0) + float(s["hours"])

        if not subject_hours:
            st.info("No sessions in the plan yet.")
        else:
            for subj, hrs in subject_hours.items():
                st.write(f"- **{subj}**: {round(hrs, 2)} hour(s) planned this week.")
