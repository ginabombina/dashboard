import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from datetime import datetime, timedelta
from drive import download_file

# ---------------- CONFIG ---------------- #
CSV_FILE = "sheet.csv"
DAY_RANGES = [1, 2, 4, 7, 14, 28]
current_day_range = 7

# Fixed colors for subjects and types (hex codes)
SUBJECT_COLORS = {
    "Maths": "#8ec3e2",
    "Physics": "#b392e7",
    "Computer Science": "#dda8dd",
    "EPQ": "#f7ef8a"
}

TYPE_COLORS = {
    "Revision": "#B3B3B3",
    "Work": "#6e6e6e",
}
# ---------------------------------------- #

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
    
def autopct_hours(values):
    def my_autopct(pct):
        total = sum(values)
        hours = pct*total/100
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
    today = pd.Timestamp.today().normalize().date()
    start_date = today - timedelta(days=day_range)
    df['Date'] = df['Timestamp'].dt.date
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= today)].copy()
    df_filtered = df_filtered.dropna(subset=['Start Time','End Time'])
    df_filtered['Hours'] = df_filtered.apply(delta_hours, axis=1)
    subject_hours = df_filtered.groupby('Subject')['Hours'].sum()
    type_hours = df_filtered.groupby('Type')['Hours'].sum()
    return subject_hours, type_hours

# ---------------- PLOT ------------------ #
fig, axes = plt.subplots(1, 2, figsize=(12,6))
plt.subplots_adjust(bottom=0.2)

def draw_charts(day_range):
    axes[0].clear()
    axes[1].clear()
    subject_hours, type_hours = load_and_process(day_range)

    if subject_hours.empty or type_hours.empty:
        axes[0].text(0.5,0.5,"No data", ha='center')
        axes[1].text(0.5,0.5,"No data", ha='center')
        fig.suptitle("")
    else:
        # Subjects pie chart
        colors = [SUBJECT_COLORS.get(label,"#cccccc") for label in subject_hours.index]
        axes[0].pie(
            subject_hours.values,
            labels=None,
            autopct=autopct_hours(subject_hours.values),
            startangle=90,
            colors=colors
        )
        axes[0].set_title(f"Subject")
        axes[0].axis('equal')

        # Type pie chart
        colors = [TYPE_COLORS.get(label,"#cccccc") for label in type_hours.index]
        axes[1].pie(
            type_hours.values,
            labels=type_hours.index,
            autopct=autopct_hours(type_hours.values),
            startangle=90,
            colors=colors
        )
        axes[1].set_title(f"Type of Work")
        axes[1].axis('equal')

        # Add total hours at the bottom
        total_hours = subject_hours.sum()
        fig.suptitle(f"Total hours: {total_hours:.1f}h over {day_range} days", fontsize=18)

    plt.draw()

draw_charts(current_day_range)

# ---------------- BUTTONS ---------------- #
# Small buttons (discrete)
button_axes = []
buttons = []
for i, dr in enumerate(DAY_RANGES):
    ax = plt.axes([0.1 + i*0.1, 0.05, 0.08, 0.05])
    b = Button(ax, f"{dr}d")
    b.on_clicked(lambda event, dr=dr: update_day_range(dr))
    button_axes.append(ax)
    buttons.append(b)

ax_refresh = plt.axes([0.85, 0.05, 0.1, 0.05])
b_refresh = Button(ax_refresh, "Refresh")
b_refresh.on_clicked(lambda event: draw_charts(current_day_range))

# ---------------- KEYBOARD CONTROLS ---------------- #
def on_key(event):
    global current_day_range
    key = event.key.lower()
    if key == 'r':
        download_file()
        draw_charts(current_day_range)
    elif key in ['1','2','3','4','5','6']:
        index = int(key)-1
        if index < len(DAY_RANGES):
            current_day_range = DAY_RANGES[index]
            draw_charts(current_day_range)

fig.canvas.mpl_connect('key_press_event', on_key)

def update_day_range(dr):
    global current_day_range
    current_day_range = dr
    draw_charts(current_day_range)

# ---------------- AUTO REFRESH ---------------- #
timer = fig.canvas.new_timer(interval=3600000)  # 1 hour = 3600000 ms
timer.add_callback(lambda: draw_charts(current_day_range))
timer.start()

plt.show()
