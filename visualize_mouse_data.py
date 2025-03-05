import os
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime

def parse_log_file(file_path):
    """Parse a log file and return timestamps and movements."""
    timestamps = []
    movements_x = []
    movements_y = []
    cumulative_x = 0
    cumulative_y = 0
    
    with open(file_path, 'r') as f:
        for line in f:
            # Match timestamp and mouse movement data
            match = re.match(r'(\d+\.\d+) - MOUSE MOVED: (-?\d+), (-?\d+)', line)
            if match:
                timestamp = float(match.group(1))
                dx = int(match.group(2))
                dy = int(match.group(3))
                
                # Accumulate movements to get position
                cumulative_x += dx
                cumulative_y += dy
                
                timestamps.append(timestamp)
                movements_x.append(cumulative_x)
                movements_y.append(cumulative_y)
    
    return np.array(timestamps), np.array(movements_x), np.array(movements_y)

def get_time_window(timestamps, total_duration):
    """Get start and end times from user input."""
    while True:
        print(f"\nTotal log duration: {total_duration:.2f} seconds")
        try:
            start = float(input(f"Enter start time (0 to {total_duration:.2f}): "))
            if not 0 <= start <= total_duration:
                print("Start time must be within the log duration")
                continue
                
            end = float(input(f"Enter end time ({start:.2f} to {total_duration:.2f}): "))
            if not start < end <= total_duration:
                print("End time must be greater than start time and within log duration")
                continue
                
            return start, end
        except ValueError:
            print("Please enter valid numbers")

def filter_data_by_time(t, x, y, start_time, end_time):
    """Filter data arrays to include only points within the time window."""
    mask = (t >= start_time) & (t <= end_time)
    return t[mask], x[mask], y[mask]

def plot_comparison(original_file):
    """Plot original vs cleaned mouse movements."""
    # Get the cleaned file path
    base, ext = os.path.splitext(original_file)
    cleaned_file = f"{base}_cleaned{ext}"
    
    if not os.path.exists(cleaned_file):
        print(f"Cleaned file not found: {cleaned_file}")
        return
    
    # Parse both files
    orig_t, orig_x, orig_y = parse_log_file(original_file)
    clean_t, clean_x, clean_y = parse_log_file(cleaned_file)
    
    # Get the time window from user
    total_duration = orig_t[-1] - orig_t[0]
    start_time, end_time = get_time_window(orig_t, total_duration)
    
    # Filter data to the selected time window
    orig_t, orig_x, orig_y = filter_data_by_time(orig_t - orig_t[0], orig_x, orig_y, start_time, end_time)
    clean_t, clean_x, clean_y = filter_data_by_time(clean_t - clean_t[0], clean_x, clean_y, start_time, end_time)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(15, 10))
    
    # Plot 1: Movement paths
    ax1 = plt.subplot(221)
    ax1.plot(orig_x, orig_y, 'b-', alpha=0.5, label='Original', linewidth=1)
    ax1.plot(clean_x, clean_y, 'r-', alpha=0.5, label='Cleaned', linewidth=1)
    ax1.set_title(f'Mouse Movement Paths\n(Time Window: {start_time:.2f}s - {end_time:.2f}s)')
    ax1.set_xlabel('X Movement')
    ax1.set_ylabel('Y Movement')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: X movement over time
    ax2 = plt.subplot(222)
    ax2.plot(orig_t, orig_x, 'b-', alpha=0.5, label='Original', linewidth=1)
    ax2.plot(clean_t, clean_x, 'r-', alpha=0.5, label='Cleaned', linewidth=1)
    ax2.set_title('X Movement Over Time')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('X Position')
    ax2.legend()
    ax2.grid(True)
    
    # Plot 3: Y movement over time
    ax3 = plt.subplot(223)
    ax3.plot(orig_t, orig_y, 'b-', alpha=0.5, label='Original', linewidth=1)
    ax3.plot(clean_t, clean_y, 'r-', alpha=0.5, label='Cleaned', linewidth=1)
    ax3.set_title('Y Movement Over Time')
    ax3.set_xlabel('Time (seconds)')
    ax3.set_ylabel('Y Position')
    ax3.legend()
    ax3.grid(True)
    
    # Plot 4: Statistics
    ax4 = plt.subplot(224)
    ax4.axis('off')
    
    # Calculate statistics for the selected window
    orig_movements = len(orig_t)
    clean_movements = len(clean_t)
    removed = orig_movements - clean_movements
    removal_percent = (removed / orig_movements) * 100 if orig_movements > 0 else 0
    
    orig_total_dist = np.sum(np.sqrt(np.diff(orig_x)**2 + np.diff(orig_y)**2))
    clean_total_dist = np.sum(np.sqrt(np.diff(clean_x)**2 + np.diff(clean_y)**2))
    
    stats_text = (
        f"Statistics (Time Window: {start_time:.2f}s - {end_time:.2f}s):\n\n"
        f"Original movements: {orig_movements}\n"
        f"Cleaned movements: {clean_movements}\n"
        f"Removed movements: {removed}\n"
        f"Removal percentage: {removal_percent:.1f}%\n\n"
        f"Original total distance: {orig_total_dist:.1f}\n"
        f"Cleaned total distance: {clean_total_dist:.1f}\n"
        f"Distance reduction: {((orig_total_dist - clean_total_dist) / orig_total_dist * 100):.1f}%"
    )
    
    ax4.text(0.1, 0.9, stats_text, fontsize=10, verticalalignment='top')
    
    # Adjust layout and display
    plt.tight_layout()
    
    # Save plot
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    plot_filename = f"mouse_movement_comparison_{timestamp}.png"
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as: {plot_filename}")
    
    # Show plot
    plt.show()
    
    # Ask if user wants to view another time window
    if input("\nWould you like to view another time window? (y/n): ").lower().startswith('y'):
        plot_comparison(original_file)

def main():
    # Look for logs in the logs directory
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        print(f"Logs directory '{logs_dir}' not found")
        return
    
    # Get list of original log files (excluding cleaned ones)
    log_files = [f for f in os.listdir(logs_dir) 
                 if f.endswith('_log.txt') and not f.endswith('_cleaned_log.txt')]
    
    if not log_files:
        print("No log files found in logs directory")
        return
    
    # Print available files
    print("\nAvailable log files:")
    for i, file in enumerate(log_files):
        print(f"{i+1}. {file}")
    
    # Get user selection
    while True:
        try:
            selection = int(input("\nSelect a file number to visualize (or 0 to exit): ")) - 1
            if selection == -1:
                return
            if 0 <= selection < len(log_files):
                break
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Plot the selected file
    selected_file = os.path.join(logs_dir, log_files[selection])
    plot_comparison(selected_file)

if __name__ == "__main__":
    main() 