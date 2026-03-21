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
ACCENT_TEXT = "#ffffff"

# ================= HELPERS ================= #
def darker(hex_color, factor=0.7):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"#{int(r*factor):02x}{int(g*factor):02x}{int(b*factor):02x}"

def hours(minutes):
    return minutes / 60

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
plt.subplots_adjust(left=0.03, right=0.97, top=0.92, bottom=0.08, wspace=0.25, hspace=0.35)

# Main subject pie
gs = GridSpec(2, 4, figure=fig, width_ratios=[1.2,1.2,1,1], height_ratios=[1,1])
ax_subject = fig.add_subplot(gs[:, :2])

# Right-hand bars
ax_bars = fig.add_subplot(gs[:, 2:])
ax_bars.axis('off')

BAR_ORDER = ["Maths", "Computer Science", "Physics", "Overall"]

# ================= DRAW RIGHT-HAND BARS ================= #
def draw_bars(ax, df):
    ax.clear()
    ax.axis('off')

    n = len(BAR_ORDER)
    bar_height = 0.08
    spacing = 0.12
    total_height = n*bar_height + (n-1)*spacing
    y_start = (1 - total_height)/2  # vertical centering

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

        # Colors
        if subject=="Overall":
            c_work = TYPE_COLORS["Work"]
            c_rev = TYPE_COLORS["Revision"]
        else:
            base = SUBJECT_COLORS.get(subject, "#cccccc")
            c_work = base
            c_rev = darker(base)

        # Draw full rounded bar (background)
        corner_radius = bar_height / 2
        full_bar = FancyBboxPatch((0, y), 1, bar_height,
                                  boxstyle=f"round,pad=0,rounding_size={corner_radius}",
                                  linewidth=0, facecolor='#333333')
        ax.add_patch(full_bar)

        # Draw Work segment (no rounding to preserve full bar ends)
        if work > 0:
            frac = work / total
            ax.add_patch(plt.Rectangle((0, y), frac, bar_height, color=c_work))
            ax.text(frac/2, y + bar_height/2,
                    f"Work ({int(round(frac*100))}%) {hours(work):.1f}h",
                    ha='center', va='center', fontsize=10, color=TEXT_COLOR)

        # Draw Revision segment (no rounding)
        if revision > 0:
            frac = revision / total
            ax.add_patch(plt.Rectangle((work/total, y), frac, bar_height, color=c_rev))
            ax.text(work/total + frac/2, y + bar_height/2,
                    f"Revision ({int(round(frac*100))}%) {hours(revision):.1f}h",
                    ha='center', va='center', fontsize=10, color=TEXT_COLOR)

        # Subject label under bar
        ax.text(0, y - 0.02, subject, ha='left', va='top', fontsize=12, color=TEXT_COLOR)

    ax.set_xlim(0,1)
    ax.set_ylim(0,1)

# ================= DRAW ALL ================= #
def draw_charts(day_range):
    ax_subject.clear()
    ax_subject.axis('off')
    df = load_and_process(day_range)

    if df.empty:
        ax_subject.text(0.5,0.5,"No data", ha='center', va='center', fontsize=16, color=TEXT_COLOR)
        fig.canvas.draw_idle()
        return

    # ---- MAIN SUBJECT PIE ----
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

    # ---- RIGHT-HAND BARS ----
    draw_bars(ax_bars, df)

    # ---- TOP LEFT INFO ----
    fig.texts.clear()
    total_hours = df['Minutes'].sum()/60
    fig.text(0.03,0.94,f"{total_hours:.1f} h", fontsize=22, weight='bold', color=ACCENT_TEXT, ha='left')
    fig.text(0.03,0.905,f"{day_range} days", fontsize=16, color="#cfcfcf", ha='left')

    fig.canvas.draw_idle()

# ================= KEYBOARD ================= #
def on_key(event):
    global current_day_range
    if event.key=='r':
        download_file()
        draw_charts(current_day_range)
    elif event.key in map(str, range(1,7)):
        current_day_range = DAY_RANGES[int(event.key)-1]
        draw_charts(current_day_range)

fig.canvas.mpl_connect('key_press_event', on_key)

# ---------------- AUTO REFRESH ---------------- #
def auto_refresh():
    print("Auto-refreshing data...")
    download_file()
    draw_charts(current_day_range)

timer = fig.canvas.new_timer(interval=3600000) # 1 hour
timer.add_callback(auto_refresh)
timer.start()

# ================= FULLSCREEN ================= #
manager = plt.get_current_fig_manager()
manager.window.attributes("-fullscreen", True)

# ================= START ================= #
draw_charts(current_day_range)
plt.show(block=True)
