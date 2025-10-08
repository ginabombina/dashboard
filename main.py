import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
from drive import download_file

# ---------------- CONFIG ---------------- #
CSV_FILE = "sheet.csv"
DAY_RANGES = [1, 2, 4, 7, 14, 28]
current_day_range = 7

# Subject colors
SUBJECT_COLORS = {
    "Maths": "#69b1db",
    "Physics": "#a078e0",
    "Computer Science": "#da8bda",
    "EPQ": "#e7de5f"
}

# Greys for overall
TYPE_COLORS = {
    "Revision": "#B3B3B3",
    "Work": "#6e6e6e",
}

# Slightly darker versions for per-subject pies
def darker(hex_color, factor=0.8):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    darkened = tuple(int(max(min(c * factor, 255), 0)) for c in rgb)
    return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

# ---------------- THEME ---------------- #
BACKGROUND_COLOR = "#1e1e1e"
TEXT_COLOR = "#f0f0f0"

# ---------------- FUNCTIONS ---------------- #
def delta_hours(row):
    try:
        start_str = str(row['Start Time'])[:5]
        end_str = str(row['End Time'])[:5]
        if start_str.lower() == 'nan' or end_str.lower() == 'nan':
            return 0.0
        start_time = datetime.strptime(start_str, "%H:%M")
        end_time = datetime.strptime(end_str, "%H:%M")
        return (end_time - start_time).seconds / 3600
    except:
        return 0.0

def style_dark(ax):
    ax.set_facecolor(BACKGROUND_COLOR)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.title.set_color(TEXT_COLOR)
    for t in ax.texts:
        t.set_color(TEXT_COLOR)

def autopct_hours(values):
    def my_autopct(pct):
        total = sum(values)
        hours = pct * total / 100
        return f"{hours:.1f}h\n({pct:.0f}%)"
    return my_autopct

def load_and_process(day_range):
    df = pd.read_csv(
        CSV_FILE,
        usecols=[0,1,2,3,4],
        dtype={"Start Time": str, "End Time": str, "Subject": str, "Type": str}
    )
    df.columns = ["Timestamp", "Start Time", "End Time", "Subject", "Type"]
    df['Timestamp'] = pd.to_datetime(df["Timestamp"], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Timestamp'])
    
    # Inclusive of today
    today = pd.Timestamp.today().normalize().date()
    start_date = today - timedelta(days=day_range - 1)
    
    df['Date'] = df['Timestamp'].dt.date
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= today)].copy()
    df_filtered = df_filtered.dropna(subset=['Start Time','End Time'])
    df_filtered['Hours'] = df_filtered.apply(delta_hours, axis=1)
    
    return df_filtered

# ---------------- INITIAL DOWNLOAD ---------------- #
download_file()  # Only download once at program start

# ---------------- PLOT SETUP ---------------- #
fig = plt.figure(figsize=(16, 9), facecolor=BACKGROUND_COLOR)
plt.subplots_adjust( # Adjust spacing manually
    top=0.88,    # move title down (0.98 → 0.88) for more space
    bottom=0.12, # leave space at bottom for buttons
    left=0.02,
    right=0.98,
    wspace=0.25,
    hspace=0.4
)
# Fullscreen
mng = plt.get_current_fig_manager()
try:
    mng.full_screen_toggle()
except:
    pass

# GridSpec layout: 2 rows x 4 cols
gs = GridSpec(2,4, figure=fig)
ax_subject = fig.add_subplot(gs[:, :2], facecolor=BACKGROUND_COLOR)
ax_maths = fig.add_subplot(gs[0,2], facecolor=BACKGROUND_COLOR)
ax_cs = fig.add_subplot(gs[0,3], facecolor=BACKGROUND_COLOR)
ax_physics = fig.add_subplot(gs[1,2], facecolor=BACKGROUND_COLOR)
ax_overall = fig.add_subplot(gs[1,3], facecolor=BACKGROUND_COLOR)
axes_right = {
    "Maths": ax_maths,
    "Computer Science": ax_cs,
    "Physics": ax_physics,
    "Overall": ax_overall
}

# ---------------- DRAW CHARTS ---------------- #
def draw_charts(day_range):
    for ax in [ax_subject, *axes_right.values()]:
        ax.clear()
        ax.set_visible(True)

    df_filtered = load_and_process(day_range)

    if df_filtered.empty:
        ax_subject.text(0.5, 0.5, "No data", ha='center', va='center', color=TEXT_COLOR)
        for ax in axes_right.values():
            ax.set_visible(False)
        fig.suptitle("")
        plt.draw()
        return

    # Subject breakdown (left)
    subject_hours = df_filtered.groupby('Subject')['Hours'].sum()
    colors = [SUBJECT_COLORS.get(label, "#cccccc") for label in subject_hours.index]
    ax_subject.pie(
        subject_hours.values,
        labels=None,
        autopct=autopct_hours(subject_hours.values),
        startangle=90,
        colors=colors
    )
    ax_subject.set_title(None)
    ax_subject.axis('equal')
    style_dark(ax_subject)

    # Work vs Revision (right)
    visible_axes = []
    for subj, ax in axes_right.items():
        if subj == "Overall":
            df_sub = df_filtered
        else:
            df_sub = df_filtered[df_filtered['Subject'] == subj]

        type_hours = df_sub.groupby('Type')['Hours'].sum()
        if type_hours.empty:
            ax.clear()
            ax.text(0.5, 0.5, f"No data for {subj}", ha='center', va='center', fontsize=11, color=TEXT_COLOR)
            ax.axis('off')
            visible_axes.append(ax)
            continue

        if subj == "Overall":
            colors = [TYPE_COLORS.get(t, "#cccccc") for t in type_hours.index]
        else:
            base = SUBJECT_COLORS.get(subj, "#cccccc")
            colors = [base, darker(base, 0.7)]

        ax.pie(
            type_hours.values,
            labels=type_hours.index,
            autopct=autopct_hours(type_hours.values),
            startangle=90,
            colors=colors,
            labeldistance=0.6,
            pctdistance=0.3
        )
        style_dark(ax)
        ax.set_title(subj)
        ax.axis('equal')
        visible_axes.append(ax)

    # Hide unused axes
    for subj, ax in axes_right.items():
        if ax not in visible_axes and subj != "Overall":
            ax.set_visible(False)

    # Total hours
    total_hours = df_filtered['Hours'].sum()
    fig.suptitle(f"Total hours: {total_hours:.1f}h over {day_range} day{'s' if day_range != 1 else ''}",
                 fontsize=18, color=TEXT_COLOR)

    plt.draw()

draw_charts(current_day_range)

# ---------------- BUTTONS ---------------- #
button_axes = []
buttons = []

def update_day_range(dr):
    global current_day_range
    current_day_range = dr
    draw_charts(current_day_range)

for i, dr in enumerate(DAY_RANGES):
    ax = plt.axes([0.1 + i*0.1, 0.02, 0.08, 0.04])  # lower and slightly shorter
    b = Button(ax, f"{dr}d [{i+1}]")
    b.on_clicked(lambda event, dr=dr: update_day_range(dr))
    button_axes.append(ax)
    buttons.append(b)

ax_refresh = plt.axes([0.85, 0.02, 0.1, 0.04])  # lower and shorter
b_refresh = Button(ax_refresh, "Refresh [R]")
b_refresh.on_clicked(lambda event: (download_file(), draw_charts(current_day_range)))
# ---------------- KEYBOARD CONTROLS ---------------- #
def on_key(event):
    global current_day_range
    key = event.key.lower()
    if key == 'r':
        download_file()
        draw_charts(current_day_range)
    elif key in ['1','2','3','4','5','6']:
        index = int(key) - 1
        if index < len(DAY_RANGES):
            current_day_range = DAY_RANGES[index]
            draw_charts(current_day_range)

fig.canvas.mpl_connect('key_press_event', on_key)

# ---------------- AUTO REFRESH ---------------- #
timer = fig.canvas.new_timer(interval=3600000)  # 1 hour
timer.add_callback(lambda: draw_charts(current_day_range))
timer.start()

plt.show()
