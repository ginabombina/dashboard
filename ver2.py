# ================= FORCE TK (PI REQUIRED) ================= #
import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")

# ================= IMPORTS ================= #
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from datetime import timedelta
from drive import download_file

# ================= CONFIG ================= #
CSV_FILE = "sheet.csv"
DAY_RANGES = [1, 2, 4, 7, 14, 28]
current_day_range = 7

SUBJECT_COLORS = {
    "Maths": "#69b1db",
    "Physics": "#a078e0",
    "Computer Science": "#da8bda",
    "EPQ": "#e7de5f"
}

TYPE_COLORS = {
    "Revision": "#B3B3B3",
    "Work": "#6e6e6e",
}

# ================= THEME ================= #
BACKGROUND_COLOR = "#1e1e1e"
TEXT_COLOR = "#f0f0f0"
MUTED_TEXT = "#666666"
ACCENT_TEXT = "#ffffff"

# ================= HELPERS ================= #
def darker(hex_color, factor=0.8):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    darkened = tuple(int(c * factor) for c in rgb)
    return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

def autopct_hours(values):
    def inner(pct):
        total = sum(values)
        minutes = pct * total / 100
        hours = minutes / 60
        if hours < 0.05:
            return ""
        return f"{hours:.1f}h\n({pct:.0f}%)"
    return inner

# ================= DATA ================= #
def load_and_process(day_range):
    df = pd.read_csv(CSV_FILE, usecols=[0,1,2,3])
    df.columns = ["Timestamp", "Minutes Spent", "Subject", "Type"]

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
    df['Minutes'] = pd.to_numeric(df['Minutes Spent'], errors='coerce').fillna(0)

    df = df.dropna(subset=['Timestamp', 'Subject', 'Type'])

    today = pd.Timestamp.today().normalize().date()
    start = today - timedelta(days=day_range - 1)

    df['Date'] = df['Timestamp'].dt.date
    df = df[(df['Date'] >= start) & (df['Date'] <= today)]
    df = df[df['Minutes'] > 0]

    return df

# ================= INITIAL DOWNLOAD ================= #
download_file()

# ================= FIGURE ================= #
plt.rcParams['toolbar'] = 'None'
fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=BACKGROUND_COLOR)
fig.patch.set_facecolor(BACKGROUND_COLOR)

plt.subplots_adjust(
    left=0.03,
    right=0.97,
    top=0.92,
    bottom=0.03,
    wspace=0.25,
    hspace=0.28
)

# Slight vertical compression for right-hand charts
gs = GridSpec(
    2, 4,
    figure=fig,
    width_ratios=[1.15, 1.15, 1, 1],
    height_ratios=[0.95, 0.95]
)

ax_subject = fig.add_subplot(gs[:, :2])
ax_maths = fig.add_subplot(gs[0, 2])
ax_cs = fig.add_subplot(gs[0, 3])
ax_physics = fig.add_subplot(gs[1, 2])
ax_overall = fig.add_subplot(gs[1, 3])

axes_right = {
    "Maths": ax_maths,
    "Computer Science": ax_cs,
    "Physics": ax_physics,
    "Overall": ax_overall
}

# ================= DRAW ================= #
def draw_charts(day_range):
    for ax in [ax_subject, ax_maths, ax_cs, ax_physics, ax_overall]:
        ax.clear()
        ax.axis('off')

    df = load_and_process(day_range)

    if df.empty:
        ax_subject.text(
            0.5, 0.5, "No data",
            ha='center', va='center',
            fontsize=16, color=TEXT_COLOR
        )
        fig.canvas.draw_idle()
        return

    # ---- MAIN SUBJECT PIE (SLIGHTLY BIGGER) ----
    subject_minutes = df.groupby('Subject')['Minutes'].sum()
    colors = [SUBJECT_COLORS.get(s, "#cccccc") for s in subject_minutes.index]

    ax_subject.pie(
        subject_minutes.values,
        colors=colors,
        startangle=90,
        radius=1.12,
        autopct=autopct_hours(subject_minutes.values),
        textprops={'fontsize': 11, 'color': TEXT_COLOR}
    )
    ax_subject.axis('equal')

    # ---- RIGHT SIDE PIES ----
    for subj, ax in axes_right.items():
        ax.axis('off')
        ax.set_title(subj, fontsize=15, color=TEXT_COLOR, pad=6)

        df_sub = df if subj == "Overall" else df[df['Subject'] == subj]
        mins = df_sub.groupby('Type')['Minutes'].sum()
        mins = mins[mins > 0]

        if mins.empty:
            ax.text(
                0.5, 0.5, "No data",
                ha='center', va='center',
                fontsize=11, color=TEXT_COLOR
            )
            continue

        if subj == "Overall":
            colors = [TYPE_COLORS.get(t, "#cccccc") for t in mins.index]
        else:
            base = SUBJECT_COLORS.get(subj, "#cccccc")
            colors = [base if t == "Work" else darker(base, 0.7) for t in mins.index]

        ax.pie(
            mins.values,
            labels=mins.index,
            colors=colors,
            startangle=90,
            autopct=autopct_hours(mins.values),
            labeldistance=0.6,
            pctdistance=0.35,
            textprops={'fontsize': 9, 'color': TEXT_COLOR}
        )
        ax.axis('equal')

    # ---- TOP LEFT INFO (TIME FIRST, DAYS SECOND) ----
    fig.texts.clear()
    total_hours = df['Minutes'].sum() / 60

    fig.text(
        0.03, 0.94,
        f"{total_hours:.1f} h",
        fontsize=18,
        weight='bold',
        color=ACCENT_TEXT,
        ha='left'
    )

    fig.text(
        0.03, 0.905,
        f"{day_range} days",
        fontsize=13,
        color="#cfcfcf",
        ha='left'
    )

    fig.canvas.draw_idle()

# ================= KEYBOARD ================= #
def on_key(event):
    global current_day_range
    if event.key == 'r':
        download_file()
        draw_charts(current_day_range)
    elif event.key in map(str, range(1, 7)):
        current_day_range = DAY_RANGES[int(event.key) - 1]
        draw_charts(current_day_range)

fig.canvas.mpl_connect('key_press_event', on_key)

# ================= FULLSCREEN ================= #
manager = plt.get_current_fig_manager()
manager.window.attributes("-fullscreen", True)

# ================= START ================= #
draw_charts(current_day_range)
plt.show(block=True)
