import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
from drive import download_file 
import matplotlib.font_manager as fm

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
    """Calculates a darker shade of a given hex color."""
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    darkened = tuple(int(max(min(c * factor, 255), 0)) for c in rgb)
    return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

# ---------------- THEME ---------------- #
BACKGROUND_COLOR = "#1e1e1e"
TEXT_COLOR = "#f0f0f0"

# ---------------- FUNCTIONS ---------------- #

def autopct_hours(values):
    """Custom autopct function to display hours and percentage (based on minutes)."""
    def my_autopct(pct):
        total_minutes = sum(values)
        minutes = pct * total_minutes / 100
        hours = minutes / 60
        
        # Only display if there's significant time (e.g., > 3 minutes)
        if hours < 0.05 and pct < 1:
            return '' 
            
        return f"{hours:.1f}h\n({pct:.0f}%)"
    return my_autopct

def style_dark(ax):
    """Applies dark theme styling to an Axes object."""
    ax.set_facecolor(BACKGROUND_COLOR)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.title.set_color(TEXT_COLOR)
    for text_obj in ax.texts:
        text_obj.set_color(TEXT_COLOR)

def load_and_process(day_range):
    """
    Loads, filters, and processes the time-tracking data, handling string errors 
    and ensuring compatibility with the 'Minutes Spent' column.
    """
    
    # Read CSV without strict dtype enforcement
    df = pd.read_csv(
        CSV_FILE,
        usecols=[0, 1, 2, 3], # Assuming the order is Timestamp, Minutes Spent, Subject, Type
        header=0
    )
    df.columns = ["Timestamp", "Minutes Spent", "Subject", "Type"]
    
    # Data Cleaning and Preparation
    df['Timestamp'] = pd.to_datetime(df["Timestamp"], dayfirst=True, errors='coerce')
    
    # FIX: Use pd.to_numeric with errors='coerce' to turn bad strings ('#REF!') into NaN.
    df['Minutes'] = pd.to_numeric(
        df['Minutes Spent'], 
        errors='coerce' 
    ).fillna(0).astype(float)
    
    # Drop rows where critical columns are missing
    df = df.dropna(subset=['Timestamp', 'Subject', 'Type'])
    
    # Filter by Date Range (Inclusive of today)
    today = pd.Timestamp.today().normalize().date()
    start_date = today - timedelta(days=day_range - 1)
    
    df['Date'] = df['Timestamp'].dt.date
    df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= today)].copy()
    
    # Filter out rows where minutes are 0 or less
    df_filtered = df_filtered[df_filtered['Minutes'] > 0]
    
    return df_filtered

# ---------------- INITIAL DOWNLOAD ---------------- #
download_file() 

# ---------------- PLOT SETUP ---------------- #

# FIX: Set DPI explicitly (e.g., 100) for consistent scaling across Windows/Pi. 
# A 16x9 figure at 100 DPI is 1600x900 pixels.
fig = plt.figure(figsize=(16, 9), facecolor=BACKGROUND_COLOR, dpi=100) 

# Apply font and color settings using standard rcParams
plt.rcParams['text.color'] = TEXT_COLOR
plt.rcParams['axes.labelcolor'] = TEXT_COLOR
plt.rcParams['xtick.color'] = TEXT_COLOR
plt.rcParams['ytick.color'] = TEXT_COLOR
plt.rcParams['figure.titlesize'] = 18 

plt.subplots_adjust(
    top=0.88,
    bottom=0.12,
    left=0.02,
    right=0.98,
    wspace=0.25,
    hspace=0.4
)

# GridSpec layout: 2 rows x 4 cols
gs = GridSpec(2, 4, figure=fig)
ax_subject = fig.add_subplot(gs[:, :2], facecolor=BACKGROUND_COLOR)
ax_maths = fig.add_subplot(gs[0, 2], facecolor=BACKGROUND_COLOR)
ax_cs = fig.add_subplot(gs[0, 3], facecolor=BACKGROUND_COLOR)
ax_physics = fig.add_subplot(gs[1, 2], facecolor=BACKGROUND_COLOR)
ax_overall = fig.add_subplot(gs[1, 3], facecolor=BACKGROUND_COLOR)

axes_right = {
    "Maths": ax_maths,
    "Computer Science": ax_cs,
    "Physics": ax_physics,
    "Overall": ax_overall 
}

# ---------------- DRAW CHARTS ---------------- #
def draw_charts(day_range):
    """Draws all the charts based on the current day range."""
    for ax in [ax_subject, ax_maths, ax_cs, ax_physics, ax_overall]:
        ax.clear()
        ax.set_visible(True)

    df_filtered = load_and_process(day_range)

    if df_filtered.empty or df_filtered['Minutes'].sum() == 0:
        ax_subject.text(0.5, 0.5, "No data", ha='center', va='center', color=TEXT_COLOR, fontsize=16)
        for ax in axes_right.values():
            ax.set_visible(False)
        
        fig.suptitle(f"Total hours: 0.0h over {day_range} day{'s' if day_range != 1 else ''}",
                     fontsize=18, color=TEXT_COLOR)
        plt.draw()
        return

    # Subject breakdown (left)
    subject_minutes = df_filtered.groupby('Subject')['Minutes'].sum()
    subject_minutes = subject_minutes[subject_minutes > 0] 
    
    colors = [SUBJECT_COLORS.get(label, "#cccccc") for label in subject_minutes.index]
    
    # 1. Main Pie Chart: Labels removed, but autopct (hours/percent) remains inside.
    wedges, texts, autotexts = ax_subject.pie(
        subject_minutes.values,
        labels=None, # FIX: Labels removed
        autopct=autopct_hours(subject_minutes.values),
        startangle=90,
        colors=colors,
        textprops={'color': TEXT_COLOR} 
    )
    
    # --- START OF ERROR-PRONE CODE REMOVAL ---
    # The following block caused the TypeError and is unnecessary since you prefer 
    # the subject labels to be removed and rely on the colors/legend.
    # The subject labels were incorrectly calculated and are now removed entirely.

    # --- END OF ERROR-PRONE CODE REMOVAL ---

    ax_subject.set_title("Time by Subject", fontsize=16)
    ax_subject.axis('equal')
    style_dark(ax_subject)

    # Work vs Revision (right)
    visible_axes = []
    for subj, ax in axes_right.items():
        ax.clear() 
        
        # Titles
        if subj == "Overall":
            df_sub = df_filtered
            ax.set_title("Overall", fontsize=16) 
        else:
            df_sub = df_filtered[df_filtered['Subject'] == subj]
            ax.set_title(f"{subj}", fontsize=16) 

        type_minutes = df_sub.groupby('Type')['Minutes'].sum()
        type_minutes = type_minutes[type_minutes > 0] 
        
        if type_minutes.empty:
            ax.text(0.5, 0.5, f"No data for {subj}", ha='center', va='center', fontsize=11, color=TEXT_COLOR)
            ax.axis('off')
            visible_axes.append(ax)
            continue

        if subj == "Overall":
            colors = [TYPE_COLORS.get(t, "#cccccc") for t in type_minutes.index]
        else:
            base = SUBJECT_COLORS.get(subj, "#cccccc")
            color_map = {
                'Work': base,
                'Revision': darker(base, 0.7)
            }
            colors = [color_map.get(t, "#cccccc") for t in type_minutes.index]


        ax.pie(
            type_minutes.values,
            labels=type_minutes.index,
            autopct=autopct_hours(type_minutes.values),
            startangle=90,
            colors=colors,
            labeldistance=0.6, 
            pctdistance=0.3, 
            textprops={'color': TEXT_COLOR}
        )
        style_dark(ax)
        ax.axis('equal')
        visible_axes.append(ax)

    # Total hours
    total_minutes = df_filtered['Minutes'].sum()
    total_hours = total_minutes / 60
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
    ax = plt.axes([0.1 + i*0.12, 0.02, 0.1, 0.04], facecolor=BACKGROUND_COLOR)
    b = Button(ax, f"{dr} days [{i+1}]")
    b.label.set_color(TEXT_COLOR)
    b.on_clicked(lambda event, dr=dr: update_day_range(dr))
    button_axes.append(ax)
    buttons.append(b)

ax_refresh = plt.axes([0.85, 0.02, 0.1, 0.04], facecolor=BACKGROUND_COLOR)
b_refresh = Button(ax_refresh, "Refresh [R]")
b_refresh.label.set_color(TEXT_COLOR)
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
def auto_refresh():
    print("Auto-refreshing data...")
    download_file()
    draw_charts(current_day_range)

timer = fig.canvas.new_timer(interval=3600000) # 1 hour
timer.add_callback(auto_refresh)
timer.start()

# Maximize the plt window
manager = plt.get_current_fig_manager()
manager.resize(*manager.window.maxsize())

plt.show()