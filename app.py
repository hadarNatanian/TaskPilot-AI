from __future__ import annotations

import json
import html
import os
from dataclasses import dataclass, asdict
from datetime import datetime, date, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load a local .env file if present; never commit it.
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


st.set_page_config(page_title="TaskPilot AI", page_icon="🧭", layout="wide")


def israel_now() -> datetime:
    """Return the current Israel local time as a naive datetime for app calculations."""
    try:
        return datetime.now(ZoneInfo("Asia/Jerusalem")).replace(tzinfo=None)
    except Exception:
        # Fallback for systems without timezone database; uses the computer's local timezone.
        return datetime.now().astimezone().replace(tzinfo=None)


def israel_today() -> date:
    return israel_now().date()

st.markdown(
    """
    <style>
    :root { --tp-ink:#183153; --tp-muted:#64748b; --tp-line:#dbe3ee; --tp-soft:#f4f7fc; }
    html, body, [class*="css"] { direction: rtl; }
    [data-testid="stAppViewContainer"], [data-testid="stSidebar"], [data-testid="stMain"], .block-container { direction: rtl; }
    .block-container { max-width:1280px; padding-top:1.5rem; padding-bottom:3rem; }
    h1,h2,h3,h4,h5,h6,
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
    [data-testid="stCaptionContainer"], [data-testid="stAlert"],
    [data-testid="stExpander"] summary { text-align:right; }
    [data-testid="stMarkdownContainer"] { direction:rtl; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] { text-align:right; }
    [data-testid="stRadio"] > label { text-align:right; }
    [data-testid="stRadio"] [role="radiogroup"] { direction:rtl; }
    [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {
        border-radius:11px; font-weight:650; transition:transform .12s ease, box-shadow .12s ease;
    }
    [data-testid="stButton"] button:hover, [data-testid="stFormSubmitButton"] button:hover {
        transform:translateY(-1px); box-shadow:0 4px 14px rgba(36,87,167,.12);
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] { border-radius:10px; }
    [data-testid="stDateInput"] input { direction:ltr !important; text-align:right !important; unicode-bidi:isolate; }
    [data-testid="stTimeInput"] input, input[type="time"], input[type="datetime-local"] {
        direction:ltr !important; text-align:left !important; unicode-bidi:isolate !important;
    }
    .hero {
        padding:1.5rem 1.7rem; margin-bottom:1.4rem; border-radius:20px;
        background:linear-gradient(120deg,#edf4ff 0%,#fbfdff 72%);
        border:1px solid #d8e5fa; box-shadow:0 8px 26px rgba(31,65,114,.06);
        text-align:right; direction:rtl;
    }
    .hero h1 { margin:0 0 .55rem 0; color:var(--tp-ink); font-size:2.2rem; }
    .hero div { color:#334e70; line-height:1.65; }
    .hero .muted { color:var(--tp-muted); font-size:.94rem; margin-top:.35rem; }
    .section-heading { color:var(--tp-ink); font-size:1.35rem; font-weight:750; text-align:right; direction:rtl; margin:.5rem 0 1rem; }
    .taskpilot-time { direction:ltr; unicode-bidi:isolate; display:inline-block; white-space:nowrap; font-variant-numeric:tabular-nums; }
    .taskpilot-removed { direction:rtl; text-align:right; display:flex; flex-direction:row; justify-content:flex-start; align-items:flex-start; gap:.55rem; margin:.55rem 0; padding:.75rem .9rem; background:#fff8ed; border:1px solid #f4dfbd; border-radius:12px; }
    .taskpilot-removed-dot { flex:0 0 auto; color:#b7791f; }
    .taskpilot-trace-list { direction:rtl; display:flex; flex-direction:column; gap:.55rem; margin:.5rem 0; }
    .taskpilot-trace-row { direction:rtl; text-align:right; display:flex; align-items:flex-start; gap:.7rem; padding:.7rem .85rem; border:1px solid #e1e8f2; border-radius:11px; background:#fbfcff; line-height:1.7; }
    .taskpilot-trace-mark { flex:0 0 auto; width:1.65rem; height:1.65rem; display:flex; align-items:center; justify-content:center; border-radius:8px; background:#eaf1ff; color:#2457a7; font-weight:750; }
    .taskpilot-decision-card { direction:rtl; text-align:right; padding:1rem 1.05rem; border:1px solid #dce5f1; border-radius:14px; background:#fff; margin:.55rem 0; line-height:1.75; }
    .taskpilot-decision-card h4 { margin:0 0 .35rem 0; color:#183153; font-size:1rem; }
    .taskpilot-decision-card p { margin:0; color:#334e70; }
    .taskpilot-decision-card.info { background:#f3f7ff; border-color:#d8e5fa; }
    .taskpilot-decision-card.success { background:#effaf3; border-color:#ccebd7; }
    .taskpilot-decision-card.warning { background:#fff8ed; border-color:#f4dfbd; }
    .taskpilot-task-note { direction:rtl; text-align:right; padding:.9rem 1rem; border:1px solid #e1e8f2; border-radius:12px; background:#fbfcff; margin:.5rem 0; }
    .taskpilot-task-note strong { display:block; color:#183153; margin-bottom:.25rem; }
    [data-testid="stExpander"] { border-radius:13px; border:1px solid var(--tp-line); overflow:hidden; }
    [data-testid="stMetric"] { background:var(--tp-soft); border:1px solid #e2eaf5; padding:.85rem 1rem; border-radius:14px; text-align:right; }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { text-align:right; }
    ul,ol { direction:rtl; text-align:right; padding-right:1.5rem; padding-left:0; }
    li { text-align:right; }
    </style>
    """,
    unsafe_allow_html=True,
)

PRIORITY_SCORE = {"נמוכה": 1, "בינונית": 2, "גבוהה": 3, "קריטית": 4}
IMPORTANCE_SCORE = {"נמוכה": 1, "בינונית": 2, "גבוהה": 3, "קריטית": 4}


@dataclass
class Task:
    title: str
    minutes: int
    urgency: str
    importance: str
    deadline: datetime
    depends_on: list[str]


def get_api_key() -> str | None:
    """Read the key from Streamlit secrets first, then from an environment variable."""
    try:
        key = st.secrets.get("OPENAI_API_KEY", None)
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "").strip() or None


def validate_int(value: Any, label: str, low: int = 1, high: int = 10080) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: יש להזין מספר שלם.") from exc
    if not low <= number <= high:
        raise ValueError(f"{label}: הערך חייב להיות בין {low} ל־{high}.")
    return number


def serialize_task(task: Task) -> dict:
    return {
        "title": task.title,
        "minutes": task.minutes,
        "urgency": task.urgency,
        "importance": task.importance,
        "deadline": task.deadline.isoformat(timespec="minutes"),
        "depends_on": task.depends_on,
    }


def ai_analyze_tasks(tasks: list[Task], goal: str, budget_minutes: int) -> tuple[dict, str]:
    """
    Ask OpenAI to interpret task text and suggest a rationale.
    The model does not perform final scheduling arithmetic; Python validates feasibility.
    """
    key = get_api_key()
    if not key:
        raise RuntimeError("לא נמצא מפתח OPENAI_API_KEY.")
    if OpenAI is None:
        raise RuntimeError("ספריית openai אינה מותקנת. התקיני לפי requirements.txt.")
    client = OpenAI(api_key=key, timeout=30.0, max_retries=1)
    payload = {
        "goal": goal,
        "available_minutes": budget_minutes,
        "tasks": [serialize_task(task) for task in tasks],
    }
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        instructions=(
            "אתה מנתח משימות עבור TaskPilot. החזר JSON תקין בלבד עם המפתחות: "
            "summary (מחרוזת בעברית), dependency_notes (מחרוזת בעברית), "
            "task_notes (מערך אובייקטים עם title, rationale בעברית, suggested_split בוליאני). "
            "השתמש רק בנתונים שסופקו. אל תשנה דדליינים או משכי זמן ואל תמציא מידע. "
            "אל תטען שתוכנית אפשרית; קוד Python בודק זאת. אם אין מידע מספיק, ציין זאת ב-summary."
        ),
        input=(
            "Return valid json only as one JSON object with keys summary, dependency_notes, task_notes. "
            "Do not add Markdown fences.\n"
            + json.dumps(payload, ensure_ascii=False)
        ),
        temperature=0.2,
    )
    content = response.output_text
    if not content:
        raise RuntimeError("המודל החזיר תשובה ריקה.")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("המודל החזיר פלט שאינו JSON תקין.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("task_notes", []), list):
        raise RuntimeError("מבנה התשובה מהמודל אינו תקין.")
    data["source"] = "openai"
    return data, response.model


def deadline_bonus(task: Task, now: datetime) -> int:
    """Give a modest preference to tasks with nearer deadlines.

    Deadlines remain hard constraints; this bonus only helps choose between
    otherwise competing tasks. The reference point is the selected planning
    start time, not the computer clock.
    """
    minutes_left = int((task.deadline - now).total_seconds() // 60)
    if minutes_left <= 30:
        return 8
    if minutes_left <= 60:
        return 6
    if minutes_left <= 120:
        return 4
    if minutes_left <= 240:
        return 2
    return 0


def priority_value(task: Task, now: datetime) -> tuple:
    """Higher urgency/importance first, then nearer deadline, then duration."""
    urgency = PRIORITY_SCORE[task.urgency]
    importance = IMPORTANCE_SCORE[task.importance]
    minutes_to_deadline = int((task.deadline - now).total_seconds() // 60)
    score = urgency * 4 + importance * 3 + deadline_bonus(task, now)
    return (
        score,
        urgency,
        importance,
        -minutes_to_deadline,
        -task.minutes,
        task.title.casefold(),
    )


def plan_with_loop(tasks: list[Task], available_minutes: int, now: datetime) -> dict:
    """Find the highest-value feasible subset and schedule it without violating
    deadlines, dependencies, or the time budget.

    For up to 18 tasks, subset dynamic programming explores all feasible task
    combinations and dependency-valid orderings. This avoids the old failure
    mode where repeatedly removing one task could miss a better combination.
    For larger task lists, a priority-ordered greedy fallback keeps runtime
    bounded. In either mode, deadlines are hard constraints and task value is
    optimized before the number of tasks or minutes used.
    """
    trace: list[str] = []
    removed: list[dict] = []
    removed_titles: set[str] = set()

    title_map = {task.title: task for task in tasks}
    if len(title_map) != len(tasks):
        raise ValueError("קיימות משימות עם שמות כפולים.")

    known_titles = set(title_map)
    for task in tasks:
        missing = [name for name in task.depends_on if name not in known_titles]
        if missing:
            raise ValueError(
                f"במשימה '{task.title}' קיימת תלות במשימה לא מוכרת: "
                f"{', '.join(missing)}"
            )
        if task.title in task.depends_on:
            raise ValueError(f"המשימה '{task.title}' אינה יכולה להיות תלויה בעצמה.")
    
    # בדיקת תלות מעגלית בין משימות
    dependency_graph = {
        task.title: task.depends_on
        for task in tasks
    }

    visiting = set()
    visited = set()

    def detect_cycle(title):
        if title in visiting:
            return True
        if title in visited:
            return False

        visiting.add(title)

        for dependency in dependency_graph[title]:
            if detect_cycle(dependency):
                return True

        visiting.remove(title)
        visited.add(title)
        return False

    for task in tasks:
        if detect_cycle(task.title):
            raise ValueError(
                "זוהתה תלות מעגלית בין משימות. "
                "יש לשנות את התלויות לפני התכנון."
            )

    def record_removed(task: Task, reason: str) -> None:
        if task.title in removed_titles:
            return
        removed_titles.add(task.title)
        removed.append({"task": task, "reason": reason})
        trace.append(f"התאמה: הוסרה '{task.title}'. {reason}")

    def explain_removed_task(
        task: Task, selected_tasks: list[Task], available_minutes: int, now: datetime
    ) -> str:
        """Explain why a task was excluded using only constraints checked by the planner."""
        selected_titles = {item.title for item in selected_tasks}
        missing_deps = [dep for dep in task.depends_on if dep not in selected_titles]
        if missing_deps:
            return (
                "לא נכללה כי משימת הקדם הנדרשת אינה נמצאת בתוכנית: "
                + ", ".join(missing_deps)
                + "."
            )

        constraints = []
        if task.minutes > available_minutes:
            constraints.append(
                f"המשימה דורשת {task.minutes} דקות, אך תקציב הזמן הכולל הוא {available_minutes} דקות"
            )

        minutes_until_deadline = max(
            0, int((task.deadline - now).total_seconds() // 60)
        )
        if task.minutes > minutes_until_deadline:
            constraints.append(
                f"המשימה דורשת {task.minutes} דקות, אך נותרו {minutes_until_deadline} דקות עד הדדליין"
            )

        if constraints:
            return "לא ניתן לשבץ את המשימה: " + "; בנוסף, ".join(constraints) + "."

        selected_minutes = sum(item.minutes for item in selected_tasks)
        if selected_minutes + task.minutes > available_minutes:
            shortage = selected_minutes + task.minutes - available_minutes
            return (
                f"לא ניתן להוסיף אותה לצד כל המשימות שנבחרו: יחד הן דורשות "
                f"{selected_minutes + task.minutes} דקות, לעומת תקציב של {available_minutes} דקות "
                f"(חריגה של {shortage} דקות). החלפת משימה אחרת עשויה לשנות את השילוב."
            )

        return (
            "המשימה אפשרית בפני עצמה, אך לא נבחרה בשילוב הסופי. "
            "המתכנן בחר שילוב בעל ניקוד עדיפות כולל גבוה יותר, תוך שמירה על תקציב הזמן, הדדליינים והתלויות."
        )

    def task_value(task: Task) -> int:
        # Priority value comes first; deadline proximity breaks meaningful ties.
        return (
            PRIORITY_SCORE[task.urgency] * 4
            + IMPORTANCE_SCORE[task.importance] * 3
            + deadline_bonus(task, now)
        )

    def build_rows(order: list[Task]) -> list[dict]:
        cursor = now
        rows: list[dict] = []
        for task in order:
            end_time = cursor + timedelta(minutes=task.minutes)
            rows.append({
                "title": task.title,
                "minutes": task.minutes,
                "urgency": task.urgency,
                "importance": task.importance,
                "deadline": task.deadline,
                "start": cursor,
                "end": end_time,
                "depends_on": list(task.depends_on),
                "broken_dependencies": [],
            })
            cursor = end_time
        return rows

    def schedule_utility(order: list[Task]) -> tuple:
        # Do not reward unused time over higher-value tasks. Minutes are only
        # the final tie-breaker after priority, task count, and deadline urgency.
        return (
            sum(task_value(task) for task in order),
            len(order),
            sum(deadline_bonus(task, now) for task in order),
            sum(task.minutes for task in order),
        )

    if not tasks:
        trace.append("תנאי עצירה: לא הוזנו משימות.")
        return {
            "feasible": True, "schedule": [], "removed": [], "trace": trace,
            "total_minutes": 0, "iterations": 0, "active_count": 0,
        }

    # A reachable mask means at least one valid ordering of that exact subset
    # exists. Every ordering of the same subset has the same elapsed duration,
    # so one valid path per mask is enough for testing all possible extensions.
    if len(tasks) <= 18:
        count = len(tasks)
        full_mask = (1 << count) - 1
        index_by_title = {task.title: i for i, task in enumerate(tasks)}
        dependency_masks = []
        for task in tasks:
            mask = 0
            for dep in task.depends_on:
                mask |= 1 << index_by_title[dep]
            dependency_masks.append(mask)

        durations = [task.minutes for task in tasks]
        elapsed = [0] * (1 << count)
        reachable: dict[int, tuple[int, ...]] = {0: ()}
        best_mask = 0
        best_order: tuple[int, ...] = ()
        best_utility = schedule_utility([])
        trace.append(f"בדיקת שילובים: נבדקות תוכניות אפשריות עבור {count} משימות.")

        for mask in range(1 << count):
            order = reachable.get(mask)
            if order is None:
                continue
            current_utility = schedule_utility([tasks[i] for i in order])
            if current_utility > best_utility:
                best_utility = current_utility
                best_mask = mask
                best_order = order

            if mask == full_mask:
                continue
            for i, task in enumerate(tasks):
                bit = 1 << i
                if mask & bit:
                    continue
                if dependency_masks[i] & mask != dependency_masks[i]:
                    continue
                finish_minutes = elapsed[mask] + task.minutes
                if finish_minutes > available_minutes:
                    continue
                finish_time = now + timedelta(minutes=finish_minutes)
                if finish_time > task.deadline:
                    continue
                next_mask = mask | bit
                if next_mask not in reachable:
                    reachable[next_mask] = order + (i,)
                    elapsed[next_mask] = finish_minutes

        best_tasks = [tasks[i] for i in best_order]
        best_schedule = build_rows(best_tasks)
        feasible = best_mask == full_mask
        trace.append(
            "החלטה: נבחר השילוב בעל ניקוד העדיפות הגבוה ביותר שעומד בתקציב, "
            "בדדליינים ובתלויות; ניצול הזמן משמש שיקול משני בלבד."
        )
        trace.append(
            f"בדיקת תוצאה: {sum(t.minutes for t in best_tasks)} דקות מתוכננות "
            f"מתוך {available_minutes} דקות פנויות."
        )
        if feasible:
            trace.append("תנאי עצירה: נמצאה תוכנית מלאה אפשרית.")
        else:
            trace.append("תנאי עצירה: לא כל המשימות יכולות להיכנס; מוצג השילוב התקין בעל העדיפות הגבוהה ביותר.")

        scheduled_titles = {task.title for task in best_tasks}
        for task in tasks:
            if task.title not in scheduled_titles:
                reason = explain_removed_task(task, best_tasks, available_minutes, now)
                record_removed(task, reason)

        return {
            "feasible": feasible,
            "schedule": best_schedule,
            "removed": removed,
            "trace": trace,
            "total_minutes": sum(row["minutes"] for row in best_schedule),
            "iterations": 1,
            "active_count": len(best_schedule),
        }

    # Bounded fallback for unusually large task lists.
    trace.append("מספר המשימות גדול; נעשה שימוש בסדר עדיפויות מהיר במקום בבדיקת כל השילובים.")
    remaining = list(tasks)
    completed: set[str] = set()
    order: list[Task] = []
    cursor = now
    while remaining:
        ready = [t for t in remaining if all(dep in completed for dep in t.depends_on)]
        if not ready:
            break
        ready.sort(key=lambda t: priority_value(t, now), reverse=True)
        chosen = None
        for task in ready:
            finish = cursor + timedelta(minutes=task.minutes)
            if sum(t.minutes for t in order) + task.minutes <= available_minutes and finish <= task.deadline:
                chosen = task
                break
        if chosen is None:
            break
        order.append(chosen)
        completed.add(chosen.title)
        remaining.remove(chosen)
        cursor += timedelta(minutes=chosen.minutes)

    best_schedule = build_rows(order)
    feasible = len(order) == len(tasks)
    trace.append("בדיקת תוצאה: התקציב, הדדליינים והתלויות נבדקו בסדר שנבחר.")
    for task in tasks:
        if task.title not in completed:
            reason = explain_removed_task(task, order, available_minutes, now)
            record_removed(task, reason)
    return {
        "feasible": feasible, "schedule": best_schedule, "removed": removed,
        "trace": trace, "total_minutes": sum(row["minutes"] for row in best_schedule),
        "iterations": 1, "active_count": len(best_schedule),
    }

def render_trace_lines(lines: list[str]) -> None:
    """Render each agent decision separately so the trace is readable in Hebrew."""
    for index, line in enumerate(lines, 1):
        safe_line = html.escape(str(line))
        st.markdown(
            f'<div class="taskpilot-trace-row" dir="rtl">'
            f'<span class="taskpilot-trace-mark">{index}</span>'
            f'<span>{safe_line}</span></div>',
            unsafe_allow_html=True,
        )


def render_decision_card(title: str, body: str, kind: str = "info") -> None:
    safe_title = html.escape(str(title))
    safe_body = html.escape(str(body))
    st.markdown(
        f'<div class="taskpilot-decision-card {kind}" dir="rtl">'
        f'<h4>{safe_title}</h4><p>{safe_body}</p></div>',
        unsafe_allow_html=True,
    )


def fmt_dt(value: datetime) -> str:
    # Plain date/time text; direction is isolated only in rendered HTML.
    return value.strftime("%d/%m/%Y %H:%M")

def add_demo_tasks() -> None:
    now = israel_now()
    st.session_state.tasks = [
        Task("לסיים עבודה להגשה", 100, "קריטית", "קריטית", now + timedelta(hours=2), []),
        Task("ללמוד למבחן", 90, "גבוהה", "גבוהה", now + timedelta(hours=4), []),
        Task("להכין מצגת", 45, "בינונית", "גבוהה", now + timedelta(hours=8), ["לסיים עבודה להגשה"]),
        Task("לסדר את החדר", 30, "נמוכה", "נמוכה", now + timedelta(days=1), []),
    ]
    st.session_state.last_result = None
    st.session_state.analysis = None


if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "analysis_model" not in st.session_state:
    st.session_state.analysis_model = None

st.markdown(
    """
    <div class="hero">
      <h1>🧭 TaskPilot AI</h1>
      <div>אג'נט לתכנון משימות בעברית — קורא נתונים, מקבל החלטות, בודק היתכנות ומחשב מחדש.</div>
      <div class="muted">ניתוח המשימות מתבצע באמצעות OpenAI API; חישובי הזמן ובדיקות ההיתכנות מתבצעים ב-Python.</div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("⚙️ הגדרות")
    page = st.radio("ניווט", ["תכנון משימות", "מרכז ההחלטות"], index=0)
    st.divider()

    budget = st.number_input(
        "זמן פנוי (דקות)",
        min_value=1,
        max_value=10080,
        value=180,
        step=15,
    )

    goal = st.text_area(
        "המטרה שלך",
        value="להשלים את המשימות החשובות ביותר בזמן שיש לי.",
        height=90,
    )

    # השעה הנוכחית בישראל
    current_time = israel_now()
    st.caption(
        f"השעה הנוכחית בישראל: {current_time.strftime('%H:%M')}"
    )

    # אתחול שעת ההתחלה לפי השעון, פעם אחת בכל הפעלה
    if "planning_start_date" not in st.session_state:
        st.session_state.planning_start_date = current_time.date()
        st.session_state.planning_start_hour = current_time.hour
        st.session_state.planning_start_minute = current_time.minute

    if st.button("עדכון לשעה הנוכחית", use_container_width=True):
        refreshed = israel_now()
        st.session_state.planning_start_date = refreshed.date()
        st.session_state.planning_start_hour = refreshed.hour
        st.session_state.planning_start_minute = refreshed.minute
        st.rerun()

    st.markdown("**שעת התחלה לתכנון**")

    start_date = st.date_input(
        "תאריך התחלה",
        key="planning_start_date",
    )

    start_hour = st.selectbox(
        "שעת התחלה",
        options=list(range(24)),
        format_func=lambda x: f"{x:02d}",
        key="planning_start_hour",
    )

    start_minute = st.selectbox(
        "דקות התחלה",
        options=list(range(60)),
        format_func=lambda x: f"{x:02d}",
        key="planning_start_minute",
    )

    planning_start = datetime.combine(
        start_date,
        time(start_hour, start_minute),
    )

    st.divider()
    st.markdown("**דדליין כללי**")

    global_date = st.date_input(
        "תאריך יעד",
        value=israel_today(),
        key="global_deadline_date",
    )

    global_hour = st.selectbox(
        "שעת יעד",
        options=list(range(24)),
        index=23,
        format_func=lambda x: f"{x:02d}",
        key="global_hour",
    )

    global_minute = st.selectbox(
        "דקות יעד",
        options=list(range(60)),
        index=59,
        format_func=lambda x: f"{x:02d}",
        key="global_minute",
    )

    global_deadline = datetime.combine(
        global_date,
        time(global_hour, global_minute),
    )

    if st.button("הוספת משימות לדוגמה", use_container_width=True):
        add_demo_tasks()
        st.rerun()

if page == "תכנון משימות":
    st.markdown('<div class="section-heading">1. הוספת משימות</div>', unsafe_allow_html=True)
    st.caption("הזיני משימות בנפרד. אפשר לבחור משימה קודמת כתלות — היא תתוכנן לפניה.")
    existing_titles = [task.title for task in st.session_state.tasks]

    with st.form("task_form", clear_on_submit=True):
        title = st.text_input("שם המשימה", placeholder="לדוגמה: לכתוב את העבודה")
        c1, c2, c3 = st.columns(3)
        with c1:
            duration = st.number_input("משך משוער (דקות)", min_value=1, max_value=10080, value=30, step=5)
            urgency = st.selectbox("דחיפות", ["נמוכה", "בינונית", "גבוהה", "קריטית"], index=2)
        with c2:
            importance = st.selectbox("חשיבות", ["נמוכה", "בינונית", "גבוהה", "קריטית"], index=2)
            due_date = st.date_input("דדליין — תאריך", value=israel_today(), key="task_due_date")
        with c3:
            task_time_col1, task_time_col2 = st.columns(2)
            # Swap the visual sides of hour and minute controls in the RTL form.
            with task_time_col1:
                due_minute = st.selectbox(
                    "דקות",
                    options=list(range(60)),
                    index=59,
                    format_func=lambda value: f"{value:02d}",
                    key="task_due_minute",
                )
            with task_time_col2:
                due_hour = st.selectbox(
                    "שעה",
                    options=list(range(24)),
                    index=23,
                    format_func=lambda value: f"{value:02d}",
                    key="task_due_hour",
                )
            dependency = st.selectbox("תלויה במשימה (אופציונלי)", ["אין"] + existing_titles)
        submitted = st.form_submit_button("➕ הוספת משימה", use_container_width=True)

    if submitted:
        try:
            clean_title = title.strip()
            if not clean_title:
                raise ValueError("צריך להזין שם משימה.")
            if any(t.title.casefold() == clean_title.casefold() for t in st.session_state.tasks):
                raise ValueError("כבר קיימת משימה בשם הזה. בחרי שם ייחודי כדי למנוע בלבול בתלויות.")
            mins = validate_int(duration, "משך המשימה")
            due_time = time(due_hour, due_minute)
            due = datetime.combine(due_date, due_time)
            if due <= planning_start:
                raise ValueError("הדדליין חייב להיות אחרי שעת ההתחלה שנבחרה לתכנון.")
            deps = [] if dependency == "אין" else [dependency]
            st.session_state.tasks.append(Task(clean_title, mins, urgency, importance, due, deps))
            st.session_state.last_result = None
            st.session_state.analysis = None
            st.success(f"המשימה '{clean_title}' נוספה.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

    if st.session_state.tasks:
        st.markdown("#### המשימות שלך")
        for idx, task in enumerate(st.session_state.tasks):
            with st.container(border=True):
                a, b, c, d = st.columns([4, 1, 1, 1])
                a.markdown(
                    f'<div dir="rtl" style="text-align:right;font-weight:750;color:#183153;">{html.escape(task.title)}</div>',
                    unsafe_allow_html=True,
                )
                a.markdown(
                    f'<div dir="rtl" style="text-align:right;color:#64748b;font-size:.88rem;margin-top:.3rem;">'
                    f'דדליין: <span class="taskpilot-time">{html.escape(fmt_dt(task.deadline))}</span></div>',
                    unsafe_allow_html=True,
                )
                b.write(f"{task.minutes} דק׳")
                c.write(f"דחיפות: {task.urgency}")
                c.caption(f"חשיבות: {task.importance}")
                if task.depends_on:
                    a.caption("תלויה ב: " + ", ".join(task.depends_on))
                if d.button("הסרה", key=f"del_{idx}"):
                    dependent_tasks = [
                        other.title
                        for other in st.session_state.tasks
                        if task.title in other.depends_on
                    ]
                    if dependent_tasks:
                        st.warning(
                            f"לא ניתן למחוק את '{task.title}' כי המשימות הבאות תלויות בה: "
                            f"{', '.join(dependent_tasks)}. עדכני קודם את התלויות שלהן."
                        )
                    else:
                        st.session_state.tasks.pop(idx)
                        st.session_state.last_result = None
                        st.session_state.analysis = None
                        st.rerun()
        if st.button("🗑️ ניקוי כל המשימות"):
            st.session_state.tasks = []
            st.session_state.last_result = None
            st.session_state.analysis = None
            st.rerun()
    else:
        st.info("הוסיפי משימות או השתמשי בכפתור 'הוספת משימות לדוגמה' שבסרגל הצד.")

    st.divider()
    st.subheader("2. הפעלת האג'נט")
    if st.button("🚀 ניתוח ותכנון משימות", type="primary", use_container_width=True):
        try:
            if not st.session_state.tasks:
                raise ValueError("אין משימות לתכנון.")
            now = planning_start
            if global_deadline <= now:
                raise ValueError("הדדליין הכללי חייב להיות בעתיד.")
            effective_budget = min(
                validate_int(budget, "זמן פנוי"),
                int((global_deadline - now).total_seconds() // 60),
            )
            if effective_budget <= 0:
                raise ValueError("אין זמן זמין עד הדדליין הכללי.")

            # AI is mandatory: do not silently fall back to local analysis.
            if not get_api_key():
                raise RuntimeError(
                    "לא נמצא מפתח API. הגדירי OPENAI_API_KEY בקובץ .env או ב-.streamlit/secrets.toml ואז הפעילי מחדש את Streamlit."
                )

            analysis, model_name = ai_analyze_tasks(st.session_state.tasks, goal, effective_budget)
            st.session_state.analysis = analysis
            st.session_state.analysis_model = model_name

            # Python remains responsible for deterministic schedule arithmetic and feasibility checks.
            result = plan_with_loop(st.session_state.tasks, effective_budget, now)
            result["effective_budget"] = effective_budget
            result["goal"] = goal
            result["analysis"] = analysis
            result["analysis_model"] = model_name
            st.session_state.last_result = result
            st.success("הניתוח הושלם.")
        except (ValueError, TypeError) as exc:
            st.session_state.last_result = None
            st.session_state.analysis = None
            st.error(f"שגיאת קלט: {exc}")
        except Exception as exc:
            st.session_state.last_result = None
            st.session_state.analysis = None
            st.error(f"פעולת ה-AI נכשלה ולכן לא נבנתה תוכנית: {exc}")

    result = st.session_state.last_result
    if result:
        st.divider()
        st.markdown('<div class="section-heading">3. התוכנית שהתקבלה</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("זמן בתוכנית", f"{result['total_minutes']} דקות")
        m2.metric("תקציב זמן", f"{result['effective_budget']} דקות")
        m3.metric("איטרציות", str(result["iterations"]))

        if result["feasible"]:
            st.success("נמצאה תוכנית אפשרית למשימות שנשארו בתוכנית.")
            for i, row in enumerate(result["schedule"], 1):
                with st.container(border=True):
                    safe_title = html.escape(str(row["title"]))
                    st.markdown(
                        f'<div dir="rtl" style="text-align:right;font-weight:700;">'
                        f'<span dir="ltr" style="unicode-bidi:isolate;">{i}.</span> '
                        f'{safe_title}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div dir="rtl" style="text-align:right;color:#334e70;margin:.45rem 0;">'
                        f'<span class="taskpilot-time">{html.escape(fmt_dt(row["start"]))}</span>'
                        f' <span>—</span> '
                        f'<span class="taskpilot-time">{html.escape(fmt_dt(row["end"]))}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div dir="rtl" style="text-align:right;color:#64748b;font-size:.88rem;line-height:1.8;">'
                        f'משך: {row["minutes"]} דקות · דחיפות: {html.escape(row["urgency"])} · '
                        f'חשיבות: {html.escape(row["importance"])} · דדליין: '
                        f'<span class="taskpilot-time">{html.escape(fmt_dt(row["deadline"]))}</span></div>',
                        unsafe_allow_html=True,
                    )
                    if row["depends_on"]:
                        st.caption("תלויות: " + ", ".join(row["depends_on"]))
        else:
            st.warning("לא נמצאה תוכנית אפשרית מלאה. ייתכן שצריך יותר זמן, לשנות דדליינים או לפצל משימות.")

        if result["removed"]:
            st.markdown("#### משימות שהוצאו מהתוכנית")
            for entry in result["removed"]:
                task = entry["task"]
                safe_title = html.escape(str(task.title))
                safe_reason = html.escape(str(entry["reason"]))
                st.markdown(
                    f'<div class="taskpilot-removed" dir="rtl">'
                    f'<span class="taskpilot-removed-dot" aria-hidden="true">●</span>'
                    f'<span><strong>{safe_title}</strong> — {safe_reason}</span></div>',
                    unsafe_allow_html=True,
                )

        with st.expander("🧠 פירוט תהליך קבלת ההחלטות (Trace)", expanded=False):
            st.caption("כל שורה מתארת החלטה או בדיקה שביצע האג'נט. פתחי את האזור רק אם תרצי לראות את הפרטים.")
            render_trace_lines(result["trace"])

elif page == "מרכז ההחלטות":
    st.markdown('<div class="section-heading">🧠 מרכז ההחלטות</div>', unsafe_allow_html=True)
    st.caption("כאן אפשר להבין מה ה-AI הסיק, מה Python בדק, ולמה התוכנית נראית כך.")
    result = st.session_state.last_result
    analysis = st.session_state.analysis

    if not result:
        st.info("עדיין אין תוצאה. עברי לתכנון משימות והפעילי את האג'נט כדי לראות כאן את הניתוח וההחלטות.")
    else:
        metric_a, metric_b, metric_c = st.columns(3)
        metric_a.metric("משימות בתוכנית", len(result.get("schedule", [])))
        metric_b.metric("זמן מתוכנן", f"{result.get('total_minutes', 0)} דקות")
        metric_c.metric("איטרציות", result.get("iterations", 0))

        st.markdown("#### 🎯 מטרת התכנון")
        render_decision_card("המטרה שהוגדרה", result.get("goal", "לא הוגדרה מטרה."), "info")

        st.markdown("#### 🤖 מה ה-AI הבין מהמשימות?")
        if analysis:
            render_decision_card("סיכום הניתוח", analysis.get("summary", "לא התקבל סיכום."), "info")
            if analysis.get("dependency_notes"):
                render_decision_card("תלויות בין משימות", analysis["dependency_notes"], "info")
            meta_cols = st.columns(2)
            with meta_cols[0]:
                st.caption("מקור הניתוח: OpenAI API" if analysis.get("source") == "openai" else "מקור הניתוח: לא ידוע")
            with meta_cols[1]:
                if result.get("analysis_model"):
                    st.caption("מודל: " + str(result["analysis_model"]))

            notes = analysis.get("task_notes", [])
            if notes:
                st.markdown("#### 💡 הסבר לפי משימה")
                for note in notes:
                    safe_title = html.escape(str(note.get("title", "משימה")))
                    safe_rationale = html.escape(str(note.get("rationale", "אין הסבר זמין.")))
                    st.markdown(
                        f'<div class="taskpilot-task-note" dir="rtl">'
                        f'<strong>{safe_title}</strong><div>{safe_rationale}</div></div>',
                        unsafe_allow_html=True,
                    )
        else:
            render_decision_card("ניתוח AI", "לא נמצא ניתוח שמור. הפעילי מחדש את האג'נט כדי לייצר ניתוח.", "warning")

        st.markdown("#### 🧮 מה Python בדק?")
        if result.get("feasible"):
            render_decision_card(
                "התוכנית אפשרית",
                f"המשימות שנשארו דורשות {result.get('total_minutes', 0)} דקות מתוך תקציב של "
                f"{result.get('effective_budget', 0)} דקות, והבדיקה מצאה שהן עומדות בדדליינים.",
                "success",
            )
        else:
            render_decision_card(
                "לא נמצאה תוכנית מלאה",
                "הזמן או הדדליינים אינם מאפשרים לשבץ את כל המשימות. כדאי להגדיל את הזמן, לשנות דדליין או לבדוק את סדר העדיפויות.",
                "warning",
            )

        if result.get("removed"):
            st.markdown("#### 📤 משימות שהוצאו מהתוכנית")
            st.caption("המשימות הבאות לא נכללו בתוכנית הסופית. לכל אחת מוצגת הסיבה שהחזיר מנגנון התכנון.")
            for entry in result["removed"]:
                task = entry["task"]
                render_decision_card(task.title, entry.get("reason", "לא צוינה סיבה."), "warning")

        with st.expander("🧠 Trace מלא — שלבי ההחלטה והחישוב", expanded=False):
            st.caption("יומן טכני של הלולאה: תכנון סדר, חישוב זמן, בדיקת היתכנות והתאמות.")
            render_trace_lines(result.get("trace", []))

else:
    st.subheader("🔌 הגדרות AI")
    st.write("TaskPilot פועל עם OpenAI API בלבד. ללא מפתח תקין, ניתוח ותכנון לא יופעלו.")
    key = get_api_key()
    if key:
        st.success("נמצא מפתח API. הערך עצמו לא מוצג.")
    else:
        st.error("לא נמצא מפתח API. יש להגדיר אותו ולהפעיל מחדש את Streamlit.")
    st.markdown("#### הגדרת מפתח בצורה בטוחה")
    st.markdown(
        """
        **אפשרות א׳ — קובץ .env (מתאים להרצה מקומית)**

        צרי קובץ בשם `.env` באותה תיקייה שבה נמצא `app.py`:
        ```dotenv
        OPENAI_API_KEY=המפתח_שלך
        ```
        אין להוסיף רווחים מסביב ל-`=`. הוסיפי `.env` ל-`.gitignore`.

        **אפשרות ב׳ — משתנה סביבה**

        Windows PowerShell (לחלון הנוכחי בלבד):
        ```powershell
        $env:OPENAI_API_KEY="המפתח_שלך"
        streamlit run app.py
        ```

        macOS / Linux:
        ```bash
        export OPENAI_API_KEY="המפתח_שלך"
        streamlit run app.py
        ```

        **אפשרות ב׳ — Streamlit secrets**

        צרי תיקייה בשם `.streamlit` ובתוכה קובץ `secrets.toml`:
        ```toml
        OPENAI_API_KEY = "המפתח_שלך"
        ```

        אין להעלות את `secrets.toml` או מפתח API ל-GitHub. הוסיפי את `.streamlit/secrets.toml` לקובץ `.gitignore`.
        """
    )
    st.markdown("#### בחירת מודל")
    st.write("ברירת המחדל בקוד היא `gpt-4o-mini`. אפשר לשנות באמצעות משתנה הסביבה `OPENAI_MODEL` אם יש לך גישה למודל אחר.")
    st.markdown("#### פרטיות")
    st.write("כשמפעילים ניתוח AI, שמות המשימות, משכן, הדדליינים, התלויות והמטרה נשלחים ל-API כדי לנתח אותם. אל תזיני מידע אישי רגיש.")

st.divider()
st.caption("TaskPilot AI — אבטיפוס לימודי. המלצות AI הן הצעות; חישובי זמן והיתכנות נבדקים בקוד המקומי.")

