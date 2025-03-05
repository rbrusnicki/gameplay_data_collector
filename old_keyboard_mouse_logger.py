import tkinter as tk
from pynput import mouse, keyboard
import time
from datetime import datetime
import os
import threading
from PIL import ImageGrab

# Configuration options
ENABLE_SCREENSHOTS = True  # Set to False to disable screenshot capture
SCREENSHOT_FREQUENCY = 60  # Screenshots per second

# Define folders for data storage
screenshot_folder = "screenshots"
logs_folder = "logs"

# Create directories if they don't exist
os.makedirs(screenshot_folder, exist_ok=True)
os.makedirs(logs_folder, exist_ok=True)

# Variable to control screenshot thread
taking_screenshots = ENABLE_SCREENSHOTS

# Function to capture screenshots at high frequency
def capture_screenshots(frequency=60):
    global taking_screenshots
    interval = 1 / frequency  # Calculate the interval in seconds
    while taking_screenshots:
        # Generate the screenshot file name with milliseconds
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]  # Trim to milliseconds
        screenshot_path = os.path.join(screenshot_folder, f"screenshot_{timestamp}.png")
        
        # Capture the screen and save it
        ImageGrab.grab().save(screenshot_path, "PNG")
        time.sleep(interval)  # Wait for the next capture

# Start the screenshot thread if enabled
if ENABLE_SCREENSHOTS:
    screenshot_thread = threading.Thread(target=capture_screenshots, args=(SCREENSHOT_FREQUENCY,), daemon=True)
    screenshot_thread.start()

# Generate a unique file name based on the current timestamp
log_file = os.path.join(logs_folder, datetime.now().strftime('%Y-%m-%d %H-%M-%S') + '_log.txt')

# Open the file in append mode to log data
with open(log_file, 'a') as f:
    f.write(f"--- Logging session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")

# Global variable to stop both listeners
stop_program = False

# Function to get a timestamp in Unix format with milliseconds
def get_timestamp():
    return f"{time.time():.3f}"

# Define how to handle key presses
def on_press(key):
    with open(log_file, 'a') as f:
        try:
            f.write(f"{get_timestamp()} - PRESSED : {key.char}\n")
        except AttributeError:
            f.write(f"{get_timestamp()} - PRESSED : {key}\n")

# Define how to handle key releases
def on_release(key):
    global stop_program, mouse_listener, keyboard_listener
    with open(log_file, 'a') as f:
        try:
            f.write(f"{get_timestamp()} - RELEASED: {key.char}\n")
        except AttributeError:
            f.write(f"{get_timestamp()} - RELEASED: {key}\n")

    # Keep the 'Esc' key logging but terminate on five 'Esc' presses
    if key == keyboard.Key.esc:
        global esc_pressed
        esc_pressed += 1
        if esc_pressed == 5:
            with open(log_file, 'a') as f:
                f.write(f"{get_timestamp()} --- Logging session ended by pressing ESC 5 times ---\n")
            stop_program = True
            # Stop both listeners when Esc is pressed five times
            mouse_listener.stop()
            keyboard_listener.stop()
            window.destroy()  # Close the tkinter window
            return False  # Stop the keyboard listener
    else:
        esc_pressed = 0

# Variables to store the previous mouse position
prev_x, prev_y = None, None

# Define how to handle mouse movements
def on_move(x, y):
    global prev_x, prev_y
    if prev_x is not None and prev_y is not None:
        dx = x - prev_x
        dy = y - prev_y
        with open(log_file, 'a') as f:
            f.write(f"{get_timestamp()} - MOUSE MOVED: {dx}, {dy}\n")
    prev_x, prev_y = x, y

# Define how to handle mouse clicks
def on_click(x, y, button, pressed):
    if stop_program:
        return False
    with open(log_file, 'a') as f:
        if pressed:
            f.write(f"{get_timestamp()} - MOUSE PRESSED : {button}\n")
        else:
            f.write(f"{get_timestamp()} - MOUSE RELEASED: {button}\n")

# Define how to handle mouse scroll
def on_scroll(x, y, dx, dy):
    with open(log_file, 'a') as f:
        f.write(f"{get_timestamp()} - MOUSE SCROLLED: {dx}, {dy}\n")

# Initialize variable to track how many times 'Esc' is pressed
esc_pressed = 0

# Function to create a tkinter window
def create_window():
    global window
    window = tk.Tk()
    window.title("Input Logger")
    window.geometry("300x180")

    # Set a larger font size
    font_size = 12

    # Create the zeroth label with instructions
    label0 = tk.Label(window, text=" ", padx=20, pady=5, font=("Arial", font_size))
    label0.pack()

    # Create the first label
    label1 = tk.Label(window, text="Logging keyboard and mouse...", padx=20, pady=5, font=("Arial", font_size))
    label1.pack()

    # Create the second label with instructions
    label2 = tk.Label(window, text=" ", padx=20, pady=5, font=("Arial", font_size))
    label2.pack()

    # Create the third label with instructions
    label3 = tk.Label(window, text="To stop:", padx=20, pady=5, font=("Arial", font_size))
    label3.pack()

    # Create the fourth label with instructions
    label4 = tk.Label(window, text="Press ESC (x5) / Close this window", padx=20, pady=5, font=("Arial", font_size))
    label4.pack()


    # Define action on window close
    def on_closing():
        global stop_program, taking_screenshots
        stop_program = True  # Set flag to stop listeners
        taking_screenshots = False  # Stop the screenshot thread
        with open(log_file, 'a') as f:
            f.write(f"{get_timestamp()} --- Logging session ended by window close ---\n")
        # Stop both listeners
        mouse_listener.stop()
        keyboard_listener.stop()
        window.destroy()  # Close the window

    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.mainloop()

# Set up listeners for both keyboard and mouse
with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as mouse_listener, \
     keyboard.Listener(on_press=on_press, on_release=on_release) as keyboard_listener:

    # Create the tkinter window
    create_window()

    # Keep running until stop_program is set to True
    while not stop_program:
        pass
