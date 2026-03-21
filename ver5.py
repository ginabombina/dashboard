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
DAY_RANGES = [1,2,4,7,14,28]
current_day_range = 7

SUBJECT_COLORS = {
    "Maths": "#69b1db",
    "Computer Science": "#da8bda"
}

GOAL_COLOR = "#e7de5f"
BAR_COLOR = "#a078e0"

DAILY_GOAL_HOURS = 4
WEEKLY_GOAL_HOURS = 28

# ================= THEME ================= #
BACKGROUND_COLOR = "#1e1e1e"
TEXT_COLOR = "#f0f0f0"
ACCENT_TEXT = "#ffffff"
ACCENT_COLOR="#333333"

# ================= HELPERS ================= #
def hours(minutes):
    return minutes / 60

# ================= DATA ================= #
def load_raw():
    df = pd.read_csv(CSV_FILE, usecols=[0,1,2])
    df.columns = ["Timestamp","Minutes Spent","Subject"]

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], dayfirst=True, errors='coerce')
    df['Minutes'] = pd.to_numeric(df['Minutes Spent'], errors='coerce').fillna(0)

    df = df.dropna(subset=['Timestamp','Subject'])
    df['Date'] = df['Timestamp'].dt.date
    df = df[df['Minutes']>0]

    return df


def load_range(df,day_range):
    today = pd.Timestamp.today().normalize().date()
    start = today - timedelta(days=day_range-1)
    return df[(df['Date']>=start) & (df['Date']<=today)]


# ================= METRICS ================= #
def compute_streak(df):
    today = pd.Timestamp.today().date()
    streak = 0

    for i in range(365):
        d = today - timedelta(days=i)
        minutes = df[df['Date']==d]['Minutes'].sum()

        if minutes >= 240:
            streak += 1
        else:
            break

    return streak


def compute_momentum(df,day_range):
    today = pd.Timestamp.today().date()

    current_start = today - timedelta(days=day_range-1)
    prev_start = current_start - timedelta(days=day_range)
    prev_end = current_start - timedelta(days=1)

    current = df[(df['Date']>=current_start)&(df['Date']<=today)]['Minutes'].sum()
    prev = df[(df['Date']>=prev_start)&(df['Date']<=prev_end)]['Minutes'].sum()

    return hours(current), hours(prev)


# ================= FIGURE ================= #
plt.rcParams['toolbar'] = 'None'

fig = plt.figure(figsize=(16,9), dpi=100, facecolor=BACKGROUND_COLOR)
plt.subplots_adjust(left=0.03,right=0.97,top=0.90,bottom=0.07,wspace=0.25)

gs = GridSpec(2,4,figure=fig,height_ratios=[1.2,1])

ax_subject = fig.add_subplot(gs[0,:])
ax_daily_goal = fig.add_subplot(gs[1,0])
ax_weekly_goal = fig.add_subplot(gs[1,1])
ax_days = fig.add_subplot(gs[1,2:])


# ================= SUBJECT BARS ================= #
def draw_subject(ax,df):

    ax.clear()
    ax.axis('off')

    mins = df.groupby('Subject')['Minutes'].sum()

    maths = mins.get("Maths",0)
    cs = mins.get("Computer Science",0)

    max_val = max(maths,cs,1)

    subjects = [
        ("Maths",maths),
        ("Computer Science",cs)
    ]

    bar_height = 0.25
    spacing = 0.18

    for i,(name,val) in enumerate(subjects):

        y = 0.50 - i*(bar_height+spacing)
        width = val/max_val

        rounding_bg, rounding_fg = 0,0

        # background
        bg = FancyBboxPatch(
            (0,y),1,bar_height,
            boxstyle=f"round,pad=0,rounding_size={rounding_bg}",
            linewidth=0,
            facecolor=ACCENT_COLOR
        )
        ax.add_patch(bg)

        # foreground (proper rounded)
        fg = FancyBboxPatch(
            (0,y),width,bar_height,
            boxstyle=f"round,pad=0,rounding_size={rounding_fg}",
            linewidth=0,
            facecolor=SUBJECT_COLORS[name]
        )
        ax.add_patch(fg)

        # labels
        padding = 0.02
        
        ax.text(padding, y + bar_height / 2, name,
            ha='left', va='center',
            color=TEXT_COLOR, fontsize=13)

        ax.text(1 - padding, y + bar_height / 2,
            f"{hours(val):.1f}h",
            ha='right', va='center',
            color=TEXT_COLOR, fontsize=13)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)


# ================= DAILY BARS ================= #
def draw_days(ax,df,day_range):

    ax.clear()
    ax.axis('off')

    today = pd.Timestamp.today().date()

    values = []
    labels = []

    for i in range(day_range):
        d = today - timedelta(days=(day_range-1-i))
        mins = df[df['Date']==d]['Minutes'].sum()

        values.append(hours(mins))
        labels.append(d.strftime("%a"))

    for i,val in enumerate(values):

        height = min(val/DAILY_GOAL_HOURS,1)

        ax.add_patch(plt.Rectangle((i,0),0.8,height,color=BAR_COLOR))

        ax.text(i+0.4,height-0.05,f"{val:.1f}h" if val>0 else "",
                ha='center',va='top',color=TEXT_COLOR,fontsize=9)

        ax.text(i+0.4,-0.08,labels[i],
                ha='center',color=TEXT_COLOR,fontsize=10)

    ax.set_xlim(0,day_range)
    ax.set_ylim(0,1)


# ================= GOAL RINGS ================= #
def draw_goal(ax,current,goal,title):

    ax.clear()
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

    progress = min(current/goal,1)

    ax.pie([1],radius=1,colors=[ACCENT_COLOR],startangle=90)

    ax.pie([progress,1-progress],
           radius=1,startangle=90,
           counterclock=False,
           colors=[GOAL_COLOR,"#00000000"])

    centre = plt.Circle((0,0),0.7,color=BACKGROUND_COLOR)
    ax.add_artist(centre)

    ax.text(0,0.1,f"{current:.1f}h",
            ha='center',color=TEXT_COLOR,
            fontsize=16,weight='bold')

    ax.text(0,-0.15,f"/ {goal}h",
            ha='center',color="#cccccc")

    ax.text(0,-1.2,title,
            ha='center',color=TEXT_COLOR,
            fontsize=12)


# ================= DRAW ================= #
def draw_charts(day_range):

    raw = load_raw()
    df = load_range(raw,day_range)

    today = pd.Timestamp.today().date()

    daily = hours(raw[raw['Date']==today]['Minutes'].sum())

    week_start = today - timedelta(days=6)
    weekly = hours(raw[(raw['Date']>=week_start)&(raw['Date']<=today)]['Minutes'].sum())

    streak = compute_streak(raw)

    study_days = df.groupby('Date')['Minutes'].sum()
    study_days = (study_days>0).sum()

    cur,prev = compute_momentum(raw,day_range)
    change = cur-prev

    fig.texts.clear()

    total = hours(df['Minutes'].sum())

    fig.text(0.12,0.90,f"{total:.1f}h total",fontsize=22,weight='bold',color=ACCENT_TEXT)
    fig.text(0.35,0.90,f"{streak} day streak",fontsize=16,color=TEXT_COLOR)
    fig.text(0.58,0.90,f"{study_days}/{day_range} study days",fontsize=16,color=TEXT_COLOR)
    fig.text(0.81,0.90,f"Momentum {change:+.1f}h",fontsize=16,color=TEXT_COLOR)

    # Horizontal bar underneath
    from matplotlib.lines import Line2D
    line = Line2D([0.05, 0.95], [0.87, 0.87], transform=fig.transFigure, color=ACCENT_COLOR, linewidth=2)
    fig.add_artist(line)

    draw_subject(ax_subject,df)
    draw_goal(ax_daily_goal,daily,DAILY_GOAL_HOURS,"Daily Goal")
    draw_goal(ax_weekly_goal,weekly,WEEKLY_GOAL_HOURS,"Weekly Goal")
    draw_days(ax_days,df,day_range)

    fig.canvas.draw_idle()


# ================= CONTROLS ================= #
def on_key(event):
    global current_day_range

    if event.key=='r':
        download_file()
        draw_charts(current_day_range)

    elif event.key in map(str,range(1,7)):
        current_day_range = DAY_RANGES[int(event.key)-1]
        draw_charts(current_day_range)

fig.canvas.mpl_connect('key_press_event', on_key)


# ================= AUTO REFRESH ================= #
def auto_refresh():
    download_file()
    draw_charts(current_day_range)

timer = fig.canvas.new_timer(interval=3600000)
timer.add_callback(auto_refresh)
timer.start()


# ================= START ================= #
download_file()

manager = plt.get_current_fig_manager()
manager.window.attributes("-fullscreen", True)

draw_charts(current_day_range)
plt.show(block=True)