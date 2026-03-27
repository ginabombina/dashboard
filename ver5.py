# ================= FORCE TK ================= #
import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")

# ================= IMPORTS ================= #
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from datetime import timedelta
from matplotlib.patches import FancyBboxPatch
from drive import download_file

# ================= CONFIG ================= #
CSV_FILE = "sheet.csv"
DAY_RANGE = 14

SUBJECT_COLORS = {
    "Maths":           "#56a5d3",
    "Further Maths":   "#2a5f8f",
    "Computer Science":"#c95dc9"
}

GOAL_HIT_COLOR     = "#6dd97a"
BAR_COLOR          = "#a078e0"
GOAL_COLOR         = BAR_COLOR

DAILY_GOAL_HOURS   = 4
WEEKLY_GOAL_HOURS  = 28

# ================= THEME ================= #
BACKGROUND_COLOR = "#1e1e1e"
TEXT_COLOR       = "#f0f0f0"
ACCENT_TEXT      = "#ffffff"
ACCENT_COLOR     = "#333333"

# ================= HELPERS ================= #
def hours(minutes):
    return minutes / 60


# ================= DATA ================= #
def load_raw():
    df = pd.read_csv(CSV_FILE, usecols=[0, 1, 2])
    df.columns = ["Timestamp", "Minutes Spent", "Subject"]

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
    df['Minutes']   = pd.to_numeric(df['Minutes Spent'], errors='coerce').fillna(0)

    df = df.dropna(subset=['Timestamp', 'Subject'])
    df['Date'] = df['Timestamp'].dt.date
    df = df[df['Minutes'] > 0]

    return df


def load_range(df, day_range):
    today = pd.Timestamp.today().normalize().date()
    start = today - timedelta(days=day_range - 1)
    return df[(df['Date'] >= start) & (df['Date'] <= today)]


# ================= METRICS ================= #
def compute_streak(df):
    """
    Count consecutive days (going back from yesterday) where the daily goal
    was met. Today is included in the streak only if the goal is already met,
    so the streak never resets to 0 at midnight if yesterday was a goal day.
    """
    today     = pd.Timestamp.today().date()
    yesterday = today - timedelta(days=1)

    streak = 0

    # Check today first — if goal already met, count it
    today_mins = df[df['Date'] == today]['Minutes'].sum()
    if today_mins >= DAILY_GOAL_HOURS * 60:
        streak += 1
        start_day = yesterday
    else:
        # Today not yet done; streak is built from yesterday backwards
        start_day = yesterday

    for i in range(365):
        d     = start_day - timedelta(days=i)
        mins  = df[df['Date'] == d]['Minutes'].sum()
        if mins >= DAILY_GOAL_HOURS * 60:
            streak += 1
        else:
            break

    return streak


def compute_momentum(df, day_range):
    """Return the difference in hours between the current period and the previous period."""
    today      = pd.Timestamp.today().date()
    cur_start  = today - timedelta(days=day_range - 1)
    prev_end   = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=day_range - 1)

    current  = df[(df['Date'] >= cur_start)  & (df['Date'] <= today)]['Minutes'].sum()
    previous = df[(df['Date'] >= prev_start) & (df['Date'] <= prev_end)]['Minutes'].sum()

    return hours(current) - hours(previous)


# ================= FIGURE ================= #
plt.rcParams['toolbar'] = 'None'

fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=BACKGROUND_COLOR)
plt.subplots_adjust(left=0.03, right=0.97, top=0.95, bottom=0.07, wspace=0.3)

# Layout: top row = goal circles (left ~35%) + day bars (right ~65%)
#         bottom row = subject bars (left 80%) + stats (right 20%)
gs = GridSpec(2, 10, figure=fig, height_ratios=[1.0, 1.0])

ax_daily_goal  = fig.add_subplot(gs[0, 0:2])  # top: daily ring
ax_weekly_goal = fig.add_subplot(gs[0, 2:4])  # top: weekly ring
ax_days        = fig.add_subplot(gs[0, 4:])   # top: 14-day bar chart
ax_subject     = fig.add_subplot(gs[1, :8])   # bottom-left: subject bars
ax_stats       = fig.add_subplot(gs[1, 8:])   # bottom-right: stats panel


# ================= SUBJECT BARS ================= #
def draw_subject(ax, df):
    ax.clear()
    ax.axis('off')

    mins = df.groupby('Subject')['Minutes'].sum()

    subject_order = ["Maths", "Further Maths", "Computer Science"]
    values = {s: mins.get(s, 0) for s in subject_order}

    max_val = max(values.values()) if values else 1
    max_val = max(max_val, 1)

    bar_height = 0.22
    spacing    = 0.10
    n          = len(subject_order)
    total_h    = n * bar_height + (n - 1) * spacing
    # Push bars up slightly to leave room for the "7 days" label at the bottom
    start_y    = (1 - total_h) / 2 + 0.06

    for i, name in enumerate(subject_order):
        val   = values[name]
        y     = start_y + (n - 1 - i) * (bar_height + spacing)
        width = val / max_val

        # background
        bg = FancyBboxPatch(
            (0, y), 1, bar_height,
            boxstyle="round,pad=0,rounding_size=0",
            linewidth=0,
            facecolor=ACCENT_COLOR
        )
        ax.add_patch(bg)

        # foreground
        if width > 0:
            fg = FancyBboxPatch(
                (0, y), width, bar_height,
                boxstyle="round,pad=0,rounding_size=0",
                linewidth=0,
                facecolor=SUBJECT_COLORS[name]
            )
            ax.add_patch(fg)

        padding = 0.015
        ax.text(padding, y + bar_height / 2, name,
                ha='left', va='center',
                color=TEXT_COLOR, fontsize=12)

        ax.text(1 - padding, y + bar_height / 2,
                f"{hours(val):.1f}h",
                ha='right', va='center',
                color=TEXT_COLOR, fontsize=12)

    # "7 days" label below the bottom bar
    ax.text(0.5, start_y - 0.08, "last 7 days",
            ha='center', va='center',
            color="#888888", fontsize=9)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)


# ================= STATS PANEL ================= #
def draw_stats(ax, streak, momentum_3d, momentum_7d):
    ax.clear()
    ax.axis('off')
    ax.set_facecolor(BACKGROUND_COLOR)

    def fmt_momentum(val):
        return f"{val:+.1f}h"

    stats = [
        ("Streak",           f"{streak}d"),
        ("3-day momentum",   fmt_momentum(momentum_3d)),
        ("7-day momentum",   fmt_momentum(momentum_7d)),
    ]

    n      = len(stats)
    slot_h = 1.0 / n

    for i, (label, value) in enumerate(stats):
        centre_y = 1.0 - (i + 0.5) * slot_h

        ax.text(0.5, centre_y + 0.10, label,
                ha='center', va='center',
                color=TEXT_COLOR, fontsize=10)
        ax.text(0.5, centre_y - 0.10, value,
                ha='center', va='center',
                color=ACCENT_TEXT, fontsize=22, weight='bold')

        if i < n - 1:
            sep_y = 1.0 - (i + 1) * slot_h
            ax.axhline(sep_y, color=ACCENT_COLOR, linewidth=1, xmin=0.05, xmax=0.95)

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)


# ================= GOAL RINGS ================= #
def draw_goal(ax, current, goal, title):
    ax.clear()
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

    progress   = min(current / goal, 1)
    goal_hit   = current >= goal
    fill_color = GOAL_HIT_COLOR if goal_hit else GOAL_COLOR
    pct_text = f"{int(current / goal * 100)}%"

    ax.pie([1], radius=1, colors=[ACCENT_COLOR], startangle=90)
    ax.pie([progress, 1 - progress],
           radius=1, startangle=90,
           counterclock=False,
           colors=[fill_color, "#00000000"])

    centre = plt.Circle((0, 0), 0.70, color=BACKGROUND_COLOR)
    ax.add_artist(centre)

    ax.text(0, 0.12, pct_text,
            ha='center', color=TEXT_COLOR,
            fontsize=15, weight='bold')

    ax.text(0, -0.15, f"{current:.1f} / {goal}h",
            ha='center', color="#cccccc", fontsize=9)

    ax.text(0, -1.25, title,
            ha='center', color=TEXT_COLOR, fontsize=11)


# ================= DAILY BAR CHART ================= #
def draw_days(ax, df, day_range):
    ax.clear()
    ax.axis('off')

    today  = pd.Timestamp.today().date()
    values = []
    labels = []

    for i in range(day_range):
        d    = today - timedelta(days=(day_range - 1 - i))
        mins = df[df['Date'] == d]['Minutes'].sum()
        values.append(hours(mins))
        labels.append(d.strftime("%a"))

    max_val = max(values) if any(v > 0 for v in values) else 1

    bar_w = 0.7

    for i, val in enumerate(values):
        height = val / max_val if max_val > 0 else 0
        color  = GOAL_HIT_COLOR if val >= DAILY_GOAL_HOURS else BAR_COLOR

        ax.add_patch(plt.Rectangle((i, 0), bar_w, height, color=color))

        if val > 0:
            ax.text(i + bar_w / 2, height + 0.02,
                    f"{val:.1f}h",
                    ha='center', va='bottom',
                    color=TEXT_COLOR, fontsize=7.5)

        ax.text(i + bar_w / 2, -0.06, labels[i],
                ha='center', va='top',
                color=TEXT_COLOR, fontsize=8.5)

    ax.set_xlim(-0.2, day_range)
    ax.set_ylim(0, 1.2)


# ================= DRAW ALL ================= #
def draw_charts():
    raw = load_raw()
    df  = load_range(raw, DAY_RANGE)

    today      = pd.Timestamp.today().date()
    week_start = today - timedelta(days=6)

    daily  = hours(raw[raw['Date'] == today]['Minutes'].sum())
    weekly = hours(raw[(raw['Date'] >= week_start) & (raw['Date'] <= today)]['Minutes'].sum())

    streak      = compute_streak(raw)
    momentum_3d = compute_momentum(raw, 3)
    momentum_7d = compute_momentum(raw, 7)

    fig.texts.clear()

    draw_subject(ax_subject, df)
    draw_stats(ax_stats, streak, momentum_3d, momentum_7d)
    draw_goal(ax_daily_goal,  daily,  DAILY_GOAL_HOURS,  "Daily Goal")
    draw_goal(ax_weekly_goal, weekly, WEEKLY_GOAL_HOURS, "Weekly Goal")
    draw_days(ax_days, raw, DAY_RANGE)

    fig.canvas.draw_idle()


# ================= CONTROLS ================= #
def on_key(event):
    if event.key == 'r':
        download_file()
        draw_charts()

fig.canvas.mpl_connect('key_press_event', on_key)


# ================= AUTO REFRESH ================= #
def auto_refresh():
    download_file()
    draw_charts()

timer = fig.canvas.new_timer(interval=600000)  # every 10 mins
timer.add_callback(auto_refresh)
timer.start()


# ================= START ================= #
download_file()

manager = plt.get_current_fig_manager()
manager.window.attributes("-fullscreen", True)

draw_charts()
plt.show(block=True)