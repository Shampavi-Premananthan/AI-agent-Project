import json
import os
from datetime import datetime, timedelta

TASKS_FILE = "tasks.json"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ------------ Data layer ------------

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


# ------------ Helper functions ------------

def parse_date(date_str):
    """
    Parse date in format YYYY-MM-DD.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def print_tasks(tasks):
    if not tasks:
        print("\nNo tasks yet.\n")
        return
    print("\nCurrent tasks:\n")
    for idx, t in enumerate(tasks, start=1):
        status = "✅" if t.get("completed", False) else "⏳"
        print(f"{idx}. {status} {t['title']} "
              f"[{t['subject']}] "
              f"Deadline: {t['deadline']} "
              f"Hours: {t['hours']} "
              f"Priority: {t['priority']}")
    print()


# ------------ Core agent actions ------------

def add_task(tasks):
    print("\n--- Add Task ---")
    title = input("Title (e.g., 'TestNG Assignment'): ").strip()
    subject = input("Subject/Course (e.g., 'Java', 'AI'): ").strip()

    while True:
        deadline_str = input("Deadline (YYYY-MM-DD): ").strip()
        deadline = parse_date(deadline_str)
        if deadline:
            break
        print("Invalid date format. Please use YYYY-MM-DD.")

    while True:
        try:
            hours = float(input("Estimated hours needed (e.g., 4): ").strip())
            if hours <= 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a positive number for hours.")

    priority = input("Priority (High/Medium/Low): ").strip().capitalize()
    if priority not in ["High", "Medium", "Low"]:
        priority = "Medium"

    task = {
        "title": title,
        "subject": subject,
        "deadline": deadline_str,
        "hours": hours,
        "priority": priority,
        "completed": False
    }
    tasks.append(task)
    save_tasks(tasks)
    print("\nTask added successfully!\n")


def mark_task_completed(tasks):
    print_tasks(tasks)
    if not tasks:
        return
    try:
        num = int(input("Enter task number to mark as completed: ").strip())
        if 1 <= num <= len(tasks):
            tasks[num - 1]["completed"] = True
            save_tasks(tasks)
            print("Task marked as completed.\n")
        else:
            print("Invalid task number.\n")
    except ValueError:
        print("Please enter a valid number.\n")


def delete_task(tasks):
    print_tasks(tasks)
    if not tasks:
        return
    try:
        num = int(input("Enter task number to delete: ").strip())
        if 1 <= num <= len(tasks):
            removed = tasks.pop(num - 1)
            save_tasks(tasks)
            print(f"Deleted task: {removed['title']}\n")
        else:
            print("Invalid task number.\n")
    except ValueError:
        print("Please enter a valid number.\n")


def get_available_hours():
    print("\n--- Set Available Study Hours ---")
    available = {}
    for day in DAYS:
        while True:
            try:
                val = float(input(f"{day} (hours available, e.g., 2, 0): ").strip())
                if val < 0:
                    raise ValueError
                available[day] = val
                break
            except ValueError:
                print("Please enter a non-negative number.")
    return available


def generate_plan(tasks, available_hours):
    """
    Very simple planner:
    - Only considers tasks not completed.
    - Sorts by (deadline, priority).
    - Iterates day by day from today, assigns hours until each task is filled.
    """
    today = datetime.today().date()

    # Filter active tasks
    active_tasks = [
        t for t in tasks
        if not t.get("completed", False)
    ]

    if not active_tasks:
        print("\nNo pending tasks to plan.\n")
        return

    # Map priority to numeric (High first)
    priority_order = {"High": 1, "Medium": 2, "Low": 3}

    # Sort tasks by deadline then priority
    active_tasks.sort(
        key=lambda t: (
            parse_date(t["deadline"]) or today,
            priority_order.get(t["priority"], 2)
        )
    )

    # Remaining hours per task
    remaining = {id(t): t["hours"] for t in active_tasks}

    # Initialize plan
    plan = {day: [] for day in DAYS}

    # Plan for next 7 days (this week-like)
    for i in range(7):
        current_date = today + timedelta(days=i)
        day_name = DAYS[current_date.weekday() % 7]
        remaining_hours_today = available_hours.get(day_name, 0.0)

        if remaining_hours_today <= 0:
            continue

        for t in active_tasks:
            if remaining_hours_today <= 0:
                break

            d = parse_date(t["deadline"]) or today
            # Do not schedule after deadline
            if current_date > d:
                continue

            task_id = id(t)
            if remaining[task_id] <= 0:
                continue

            # Allocate min(remaining task hours, remaining today)
            alloc = min(remaining[task_id], remaining_hours_today)
            if alloc <= 0:
                continue

            plan[day_name].append({
                "title": t["title"],
                "subject": t["subject"],
                "hours": round(alloc, 2),
                "deadline": t["deadline"],
                "priority": t["priority"]
            })

            remaining[task_id] -= alloc
            remaining_hours_today -= alloc

    # Print plan
    print("\n--- Weekly Study Plan (Simple Agent) ---\n")
    for day in DAYS:
        print(f"{day}:")
        if not plan[day]:
            print("  No planned study sessions.")
        else:
            for session in plan[day]:
                print(
                    f"  - {session['title']} ({session['subject']}) | "
                    f"{session['hours']}h | "
                    f"Deadline: {session['deadline']} | "
                    f"Priority: {session['priority']}"
                )
        print()

    # Warn about any tasks that still have remaining hours
    unfilled = [t for t in active_tasks if remaining[id(t)] > 0.01]
    if unfilled:
        print("⚠ Warning: Not enough available hours to fully cover these tasks:")
        for t in unfilled:
            print(
                f"  - {t['title']} ({t['subject']}) "
                f"needs ~{round(remaining[id(t)], 2)} more hour(s) before {t['deadline']}"
            )
        print()


# ------------ Main loop (Agent interface) ------------

def main():
    tasks = load_tasks()

    while True:
        print("===== Study & Project Planner Agent (CLI) =====")
        print("1. View tasks")
        print("2. Add task")
        print("3. Mark task as completed")
        print("4. Delete task")
        print("5. Generate weekly plan")
        print("6. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            print_tasks(tasks)
        elif choice == "2":
            add_task(tasks)
        elif choice == "3":
            mark_task_completed(tasks)
        elif choice == "4":
            delete_task(tasks)
        elif choice == "5":
            available = get_available_hours()
            generate_plan(tasks, available)
        elif choice == "6":
            print("Goodbye! Stay consistent with your plan :)")
            break
        else:
            print("Invalid choice. Please try again.\n")


if __name__ == "__main__":
    main()
