# ================= FORCE TK (PI REQUIRED) ================= #
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
DAY_RANGES = [1, 2, 4, 7, 14, 28]
current_day_range = 7

SUBJECT_COLORS = {
    "Maths": "#69b1db",
    "Computer Science": "#da8bda",
    "EPQ": "#e7de5f"
}

TYPE_COLORS = {
    "Revision": "#B3B3B3",
    "Work": "#6e6e6e",
}

# ================= GOALS ================= #
DAILY_REVISION_GOAL_HOURS = 4
WEEKLY_REVISION_GOAL_HOURS = 28
GOAL_COLOR = "#a078e0"  # Physics purple

# ================= THEME ================= #
BACKGROUND_COLOR = "#1e1e1e"
TEXT_COLOR = "#f0f0f0"
ACCENT_TEXT = "#ffffff"

# ================= HELPERS ================= #
def darker(hex_color, factor=0.7):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"

def hours(minutes):
    return minutes / 60

# ================= DATA ================= #
def load_raw():
    df = pd.read_csv(CSV_FILE, usecols=[0,1,2,3])
    df.columns = ["Timestamp", "Minutes Spent", "Subject", "Type"]

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
    df['Minutes'] = pd.to_numeric(df['Minutes Spent'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Timestamp', 'Subject', 'Type'])
    df['Date'] = df['Timestamp'].dt.date
    df = df[df['Minutes'] > 0]
    return df

def load_and_process(day_range):
    df = load_raw()
    today = pd.Timestamp.today().normalize().date()
    start = today - timedelta(days=day_range - 1)
    return df[(df['Date'] >= start) & (df['Date'] <= today)]

# ================= INITIAL DOWNLOAD ================= #
download_file()

# ================= FIGURE ================= #
plt.rcParams['toolbar'] = 'None'
fig = plt.figure(figsize=(16, 9), dpi=100, facecolor=BACKGROUND_COLOR)
plt.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.08, wspace=0.25, hspace=0.15)

gs = GridSpec(2, 4, figure=fig,
              width_ratios=[1.2,1.2,1,1],
              height_ratios=[1,1])

# Main subject pie
ax_subject = fig.add_subplot(gs[:, :2])

# Goal circles (top right)
ax_daily_goal = fig.add_subplot(gs[0, 2])
ax_weekly_goal = fig.add_subplot(gs[0, 3])

# Bars now take FULL bottom row
ax_bars = fig.add_subplot(gs[1, 2:])

BAR_ORDER = ["Maths", "Computer Science", "Overall"]

# ================= DRAW BARS ================= #
def draw_bars(ax, df):
    ax.clear()
    ax.axis('off')

    n = len(BAR_ORDER)
    bar_height = 0.18
    spacing = 0.18
    total_height = n*bar_height + (n-1)*spacing
    y_start = (1 - total_height)/2

    for i, subject in enumerate(BAR_ORDER):
        y = y_start + (n-1-i)*(bar_height + spacing)

        df_sub = df if subject=="Overall" else df[df['Subject']==subject]
        mins = df_sub.groupby('Type')['Minutes'].sum()

        work = mins.get("Work",0)
        revision = mins.get("Revision",0)
        total = work + revision

        if total == 0:
            ax.text(0.5, y + bar_height/2, "No data", ha='center', va='center', color=TEXT_COLOR)
            continue

        if subject=="Overall":
            c_work = TYPE_COLORS["Work"]
            c_rev = TYPE_COLORS["Revision"]
        else:
            base = SUBJECT_COLORS.get(subject, "#cccccc")
            c_work = base
            c_rev = darker(base)

        corner_radius = bar_height / 2
        full_bar = FancyBboxPatch((0, y), 1, bar_height,
                                  boxstyle=f"round,pad=0,rounding_size={corner_radius}",
                                  linewidth=0, facecolor='#333333')
        ax.add_patch(full_bar)

        if work > 0:
            frac_work = work / total
            ax.add_patch(plt.Rectangle((0, y), frac_work, bar_height, color=c_work))

            ax.text(frac_work/2,
                    y + bar_height/2,
                    f"Work ({int(round(frac_work*100))}%) {hours(work):.1f}h",
                    ha='center',
                    va='center',
                    fontsize=11,
                    color=TEXT_COLOR)

        if revision > 0:
            frac_rev = revision / total
            start_x = work / total

            ax.add_patch(plt.Rectangle((start_x, y), frac_rev, bar_height, color=c_rev))

            ax.text(start_x + frac_rev/2,
                    y + bar_height/2,
                    f"Revision ({int(round(frac_rev*100))}%) {hours(revision):.1f}h",
                    ha='center',
                    va='center',
                    fontsize=11,
                    color=TEXT_COLOR)
            
        ax.text(0, y - 0.03, subject, ha='left', va='top', fontsize=13, color=TEXT_COLOR)

    ax.set_xlim(0,1)
    ax.set_ylim(0,1)

# ================= GOAL CIRCLES ================= #
def draw_goal_circle(ax, current_hours, goal_hours, title):
    ax.clear()
    ax.axis('equal')
    ax.axis('off')

    progress = min(current_hours / goal_hours, 1)

    ax.pie([1], radius=1, colors=["#333333"], startangle=90)

    ax.pie([progress, 1-progress],
           radius=1,
           startangle=90,
           counterclock=False,
           colors=[GOAL_COLOR, "#00000000"])

    centre_circle = plt.Circle((0,0), 0.7, color=BACKGROUND_COLOR)
    ax.add_artist(centre_circle)

    ax.text(0, 0.1,
            f"{current_hours:.1f}h",
            ha='center', va='center',
            fontsize=17, weight='bold', color=TEXT_COLOR)

    ax.text(0, -0.15,
            f"/ {goal_hours}h",
            ha='center', va='center',
            fontsize=11, color="#cfcfcf")

    # Label UNDER circle
    ax.text(0, -1.25,
            title,
            ha='center',
            va='top',
            fontsize=13,
            color=TEXT_COLOR)
    
# ================= DRAW ALL ================= #
def draw_charts(day_range):
    ax_subject.clear()
    ax_subject.axis('off')

    raw_df = load_raw()
    df = load_and_process(day_range)

    if df.empty:
        ax_subject.text(0.5,0.5,"No data", ha='center', va='center', fontsize=16, color=TEXT_COLOR)
        fig.canvas.draw_idle()
        return

    today = pd.Timestamp.today().date()

    # DAILY (all work + revision today)
    daily_hours = raw_df[
        raw_df['Date'] == today
    ]['Minutes'].sum() / 60

    # WEEKLY (last 7 days, all work + revision)
    week_start = today - timedelta(days=6)
    weekly_hours = raw_df[
        (raw_df['Date'] >= week_start) &
        (raw_df['Date'] <= today)
    ]['Minutes'].sum() / 60

    # PIE
    subject_minutes = df.groupby('Subject')['Minutes'].sum()
    colors = [SUBJECT_COLORS.get(s,"#cccccc") for s in subject_minutes.index]

    def pie_autopct(p):
        total = subject_minutes.sum()
        minutes = p*total/100
        hrs = minutes/60
        if hrs<0.05: return ""
        return f"{hrs:.1f}h\n({p:.0f}%)"

    ax_subject.pie(subject_minutes.values,
                   colors=colors,
                   startangle=90,
                   radius=1.12,
                   autopct=pie_autopct,
                   textprops={'fontsize':11,'color':TEXT_COLOR})
    ax_subject.axis('equal')

    draw_bars(ax_bars, df)

    draw_goal_circle(ax_daily_goal,
                     daily_hours,
                     DAILY_REVISION_GOAL_HOURS,
                     "Daily Goal")

    draw_goal_circle(ax_weekly_goal,
                     weekly_hours,
                     WEEKLY_REVISION_GOAL_HOURS,
                     "Weekly Goal")

    fig.texts.clear()
    total_hours = df['Minutes'].sum()/60
    fig.text(0.03,0.94,f"{total_hours:.1f} h", fontsize=22, weight='bold', color=ACCENT_TEXT, ha='left')
    fig.text(0.03,0.905,f"{day_range} days", fontsize=16, color="#cfcfcf", ha='left')

    fig.canvas.draw_idle()

# ================= CONTROLS ================= #
def on_key(event):
    global current_day_range
    if event.key=='r':
        download_file()
        draw_charts(current_day_range)
    elif event.key in map(str, range(1,7)):
        current_day_range = DAY_RANGES[int(event.key)-1]
        draw_charts(current_day_range)

fig.canvas.mpl_connect('key_press_event', on_key)

def auto_refresh():
    download_file()
    draw_charts(current_day_range)

timer = fig.canvas.new_timer(interval=3600000)
timer.add_callback(auto_refresh)
timer.start()

manager = plt.get_current_fig_manager()
manager.window.attributes("-fullscreen", True)

draw_charts(current_day_range)
plt.show(block=True)