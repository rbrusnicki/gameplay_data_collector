import os
import re
import numpy as np
from collections import deque
from datetime import datetime

def parse_log_line(line):
    """Parse a log line and return timestamp and movement data if it's a mouse movement."""
    # Match timestamp and mouse movement data
    match = re.match(r'(\d+\.\d+) - MOUSE MOVED: (-?\d+), (-?\d+)', line)
    if match:
        timestamp = float(match.group(1))
        dx = int(match.group(2))
        dy = int(match.group(3))
        return timestamp, dx, dy
    return None

class MouseMovement:
    def __init__(self, timestamp, dx, dy, line, line_number):
        self.timestamp = timestamp
        self.dx = dx
        self.dy = dy
        self.line = line
        self.line_number = line_number
        self.cumulative_x = 0  # Will be set later
        self.cumulative_y = 0  # Will be set later

def find_center_returns(movements, window_size=20, time_threshold=0.05, position_threshold=2):
    """
    Find sequences of movements that return to a center point.
    
    Args:
        movements: List of MouseMovement objects
        window_size: Number of movements to look at in each window
        time_threshold: Maximum time (in seconds) for a sequence to be considered a game correction
        position_threshold: Maximum distance from original position to be considered a return to center
    """
    if len(movements) < 2:
        return set()

    # Calculate cumulative positions
    cum_x = 0
    cum_y = 0
    for m in movements:
        cum_x += m.dx
        cum_y += m.dy
        m.cumulative_x = cum_x
        m.cumulative_y = cum_y

    movements_to_remove = set()
    i = 0
    
    while i < len(movements) - 1:
        # Look for potential center returns in a sliding window
        window = movements[i:min(i + window_size, len(movements))]
        if len(window) < 2:
            break
            
        # Check if this window contains a return to center
        start_x = window[0].cumulative_x
        start_y = window[0].cumulative_y
        start_time = window[0].timestamp
        
        # Find any points in the window that return close to the starting position
        for j in range(1, len(window)):
            end_x = window[j].cumulative_x
            end_y = window[j].cumulative_y
            end_time = window[j].timestamp
            
            # Check if position is close to start position
            dist_from_start = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            time_diff = end_time - start_time
            
            if dist_from_start <= position_threshold and time_diff <= time_threshold:
                # This sequence returns to center quickly - mark all movements in between for removal
                for k in range(i + 1, i + j + 1):
                    movements_to_remove.add(k)
                i = i + j  # Skip the processed movements
                break
        i += 1
    
    return movements_to_remove

def clean_log_file(input_file):
    """Clean a log file by removing game-induced counter-movements."""
    # Create output filename in the same directory as input
    input_dir = os.path.dirname(input_file)
    base_name = os.path.basename(input_file)
    base, ext = os.path.splitext(base_name)
    output_file = os.path.join(input_dir, f"{base}_cleaned{ext}")
    
    # Read all lines
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Process lines and identify movements
    movements = []
    non_movement_lines = []
    
    for i, line in enumerate(lines):
        parsed = parse_log_line(line)
        if parsed:
            timestamp, dx, dy = parsed
            movements.append(MouseMovement(timestamp, dx, dy, line, i))
        else:
            non_movement_lines.append((i, line))
    
    # Find movements to remove
    indices_to_remove = find_center_returns(movements)
    
    # Write cleaned data
    with open(output_file, 'w') as f:
        current_movement = 0
        for i, line in enumerate(lines):
            if current_movement < len(movements) and i == movements[current_movement].line_number:
                if current_movement not in indices_to_remove:
                    f.write(line)
                current_movement += 1
            else:
                # Write non-movement lines
                f.write(line)
    
    return output_file

def main():
    # Look for logs in the logs directory
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        print(f"Logs directory '{logs_dir}' not found")
        return
    
    # Process all log files in the logs directory
    log_files = [f for f in os.listdir(logs_dir) 
                 if f.endswith('_log.txt') and not f.endswith('_cleaned_log.txt')]
    
    if not log_files:
        print("No log files found in logs directory")
        return
    
    for log_file in log_files:
        full_path = os.path.join(logs_dir, log_file)
        print(f"Processing {log_file}...")
        output_file = clean_log_file(full_path)
        print(f"Created cleaned file: {os.path.basename(output_file)}")

if __name__ == "__main__":
    main() 