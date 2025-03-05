import tkinter as tk
import time
from datetime import datetime
import os
import threading
from PIL import ImageGrab
import ctypes
from ctypes import wintypes
import win32con
import win32gui
import sys
import keyboard as kb
import queue

# Define WM_INPUT since it's not in win32con
WM_INPUT = 0x00FF

# Configuration flags
CAPTURE_SCREENSHOTS = False  # Toggle screenshot capturing
CAPTURE_RAW_MOUSE = True     # Toggle raw mouse input capture
CAPTURE_KEYBOARD = True      # Toggle keyboard input capture
SCREENSHOT_FREQUENCY = 60    # Screenshots per second

# Define folder for screenshots
screenshot_folder = "screenshots"
os.makedirs(screenshot_folder, exist_ok=True)

# Ensure logs folder exists
logs_folder = "logs"
os.makedirs(logs_folder, exist_ok=True)

# Generate a unique file name based on the current timestamp
timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
log_file = os.path.join(logs_folder, timestamp_str + '_log.txt')

# Try to create the log file directly in the current directory if permissions fail
try:
    with open(log_file, 'w') as f:
        f.write(f"--- Logging session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")
        f.write(f"--- Configuration: Screenshots={CAPTURE_SCREENSHOTS}, RawMouse={CAPTURE_RAW_MOUSE}, Keyboard={CAPTURE_KEYBOARD} ---\n")
except PermissionError:
    # If we can't write to the logs folder, use current directory
    log_file = timestamp_str + '_log.txt'
    with open(log_file, 'w') as f:
        f.write(f"--- Logging session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")
        f.write(f"--- Configuration: Screenshots={CAPTURE_SCREENSHOTS}, RawMouse={CAPTURE_RAW_MOUSE}, Keyboard={CAPTURE_KEYBOARD} ---\n")

# Global variables 
stop_program = False
taking_screenshots = True
esc_pressed = 0
last_esc_time = 0

# Simple direct logging function - This should work like in the old version
def write_log(message):
    try:
        with open(log_file, 'a') as f:
            f.write(message + '\n')
    except Exception as e:
        print(f"Error writing to log: {e}")

# Function to get a timestamp in Unix format with milliseconds
def get_timestamp():
    return f"{time.time():.3f}"

# Function to capture screenshots at high frequency
def capture_screenshots(frequency=60):
    global taking_screenshots
    if not CAPTURE_SCREENSHOTS:
        return
        
    interval = 1 / frequency  # Calculate the interval in seconds
    while taking_screenshots and not stop_program:
        try:
            # Generate the screenshot file name with milliseconds
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]  # Trim to milliseconds
            screenshot_path = os.path.join(screenshot_folder, f"screenshot_{timestamp}.png")
            
            # Capture the screen and save it
            ImageGrab.grab().save(screenshot_path, "PNG")
            time.sleep(interval)  # Wait for the next capture
        except Exception as e:
            write_log(f"{get_timestamp()} - Screenshot error: {str(e)}")
            time.sleep(1)  # Wait a bit before retrying

# Windows structures for raw input
class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]

class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]

class RAWMOUSE(ctypes.Structure):
    class _U1(ctypes.Union):
        class _S2(ctypes.Structure):
            _fields_ = [
                ("usButtonFlags", wintypes.USHORT),
                ("usButtonData", wintypes.USHORT),
            ]
        _fields_ = [
            ("ulButtons", wintypes.ULONG),
            ("_s2", _S2),
        ]
    
    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("_u1", _U1),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]

class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG),
    ]

class RAWHID(ctypes.Structure):
    _fields_ = [
        ("dwSizeHid", wintypes.DWORD),
        ("dwCount", wintypes.DWORD),
        ("bRawData", wintypes.BYTE * 1),
    ]

class RAWINPUT(ctypes.Structure):
    class _U1(ctypes.Union):
        _fields_ = [
            ("mouse", RAWMOUSE),
            ("keyboard", RAWKEYBOARD),
            ("hid", RAWHID),
        ]
    
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("_u1", _U1),
        ("data", wintypes.BYTE * 1),
    ]

# Constants for raw input
RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIM_TYPEHID = 2
RI_MOUSE_MOVE_RELATIVE = 0
RI_MOUSE_MOVE_ABSOLUTE = 1
RI_MOUSE_LEFT_BUTTON_DOWN = 1
RI_MOUSE_LEFT_BUTTON_UP = 2
RI_MOUSE_RIGHT_BUTTON_DOWN = 4
RI_MOUSE_RIGHT_BUTTON_UP = 8
RI_MOUSE_MIDDLE_BUTTON_DOWN = 16
RI_MOUSE_MIDDLE_BUTTON_UP = 32

# Additional constants not always in win32con
RID_INPUT = 0x10000003

# Window handling
def create_window():
    global window
    window = tk.Tk()
    window.title("Raw Input Logger")
    window.geometry("400x300")

    # Set a larger font size
    font_size = 12

    # Create the configuration display
    config_frame = tk.Frame(window, padx=10, pady=10)
    config_frame.pack(fill='x')
    
    config_label = tk.Label(config_frame, text="Current Configuration:", font=("Arial", font_size, "bold"))
    config_label.pack(anchor='w')
    
    screenshots_label = tk.Label(config_frame, 
                                text=f"Screenshots: {'ON' if CAPTURE_SCREENSHOTS else 'OFF'}", 
                                font=("Arial", font_size))
    screenshots_label.pack(anchor='w')
    
    mouse_label = tk.Label(config_frame, 
                          text=f"Raw Mouse: {'ON' if CAPTURE_RAW_MOUSE else 'OFF'}", 
                          font=("Arial", font_size))
    mouse_label.pack(anchor='w')
    
    keyboard_label = tk.Label(config_frame, 
                             text=f"Keyboard: {'ON' if CAPTURE_KEYBOARD else 'OFF'}", 
                             font=("Arial", font_size))
    keyboard_label.pack(anchor='w')

    # Create a separator
    separator = tk.Frame(window, height=2, bg="gray")
    separator.pack(fill='x', padx=10, pady=10)

    # Create the status display
    status_frame = tk.Frame(window, padx=10, pady=5)
    status_frame.pack(fill='x')
    
    status_label = tk.Label(status_frame, text="Logging in progress...", font=("Arial", font_size))
    status_label.pack()
    
    # Instructions
    instructions_frame = tk.Frame(window, padx=10, pady=5)
    instructions_frame.pack(fill='x')
    
    instruction_label = tk.Label(instructions_frame, 
                                text="To stop: Press ESC 5 times or close this window", 
                                font=("Arial", font_size))
    instruction_label.pack()

    # Show log file path
    log_frame = tk.Frame(window, padx=10, pady=5)
    log_frame.pack(fill='x')
    
    log_label = tk.Label(log_frame, 
                        text=f"Log file: {os.path.basename(log_file)}", 
                        font=("Arial", font_size-2))
    log_label.pack()

    # Define action on window close
    def on_closing():
        global stop_program, taking_screenshots
        stop_program = True  # Set flag to stop listeners
        taking_screenshots = False  # Stop the screenshot thread
        write_log(f"{get_timestamp()} --- Logging session ended by window close ---")
        window.destroy()  # Close the window

    window.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Register for raw input
    setup_raw_input(window.winfo_id())
    
    # Set up a custom message handler
    def wnd_proc(hwnd, msg, wparam, lparam):
        try:
            if msg == WM_INPUT and (CAPTURE_RAW_MOUSE or CAPTURE_KEYBOARD):
                process_raw_input(lparam)
        except Exception as e:
            print(f"Error in window procedure: {e}")
        return win32gui.CallWindowProc(original_wnd_proc, hwnd, msg, wparam, lparam)
    
    hwnd = window.winfo_id()
    original_wnd_proc = win32gui.SetWindowLong(hwnd, win32con.GWL_WNDPROC, wnd_proc)
    
    # Handle keyboard for ESC press detection
    kb.hook(check_esc_pressed)
    
    # Process tkinter events
    def process_events():
        if not stop_program:
            window.update()
            window.after(10, process_events)
    
    window.after(10, process_events)
    
    return window

def check_esc_pressed(e):
    global esc_pressed, stop_program, last_esc_time, taking_screenshots
    
    if e.event_type == kb.KEY_DOWN and e.name == 'esc':
        current_time = time.time()
        # Reset counter if more than 2 seconds between presses
        if current_time - last_esc_time > 2:
            esc_pressed = 0
        
        last_esc_time = current_time
        esc_pressed += 1
        
        if CAPTURE_KEYBOARD:
            write_log(f"{get_timestamp()} - PRESSED : esc")
        
        if esc_pressed >= 5:
            write_log(f"{get_timestamp()} --- Logging session ended by pressing ESC 5 times ---")
            stop_program = True
            taking_screenshots = False
            if 'window' in globals():
                window.destroy()
    elif e.event_type == kb.KEY_DOWN and CAPTURE_KEYBOARD:
        write_log(f"{get_timestamp()} - PRESSED : {e.name}")
    elif e.event_type == kb.KEY_UP and CAPTURE_KEYBOARD:
        write_log(f"{get_timestamp()} - RELEASED : {e.name}")

def setup_raw_input(hwnd):
    # Register for raw input
    raw_mouse = RAWINPUTDEVICE(
        usUsagePage=0x01,      # HID_USAGE_PAGE_GENERIC
        usUsage=0x02,          # HID_USAGE_GENERIC_MOUSE
        dwFlags=0,             # No flags
        hwndTarget=hwnd        # Target window to receive input
    )
    
    raw_keyboard = RAWINPUTDEVICE(
        usUsagePage=0x01,      # HID_USAGE_PAGE_GENERIC
        usUsage=0x06,          # HID_USAGE_GENERIC_KEYBOARD
        dwFlags=0,             # No flags
        hwndTarget=hwnd        # Target window to receive input
    )
    
    # Register both devices if needed
    devices = (RAWINPUTDEVICE * 2)(raw_mouse, raw_keyboard)
    
    if ctypes.windll.user32.RegisterRawInputDevices(devices, 2, ctypes.sizeof(RAWINPUTDEVICE)) == False:
        error_code = ctypes.GetLastError()
        write_log(f"{get_timestamp()} - Error registering raw input devices. Code: {error_code}")

def process_raw_input(lparam):
    buffer_size = wintypes.UINT()
    
    # Get the size of the input data
    ctypes.windll.user32.GetRawInputData(
        lparam, 
        RID_INPUT,
        None, 
        ctypes.byref(buffer_size), 
        ctypes.sizeof(RAWINPUTHEADER)
    )
    
    if buffer_size.value <= 0:
        return
        
    # Create a buffer to receive the input data
    raw_buffer = (ctypes.c_byte * buffer_size.value)()
    
    # Get the raw input data
    size = ctypes.windll.user32.GetRawInputData(
        lparam, 
        RID_INPUT, 
        raw_buffer, 
        ctypes.byref(buffer_size), 
        ctypes.sizeof(RAWINPUTHEADER)
    )
    
    if size != buffer_size.value:
        return
        
    # Cast the raw buffer to a RAWINPUT structure
    raw_input = ctypes.cast(raw_buffer, ctypes.POINTER(RAWINPUT)).contents
    
    # Process mouse input
    if raw_input.header.dwType == RIM_TYPEMOUSE and CAPTURE_RAW_MOUSE:
        mouse = raw_input._u1.mouse
        
        # Log relative movements (this is what we want - hardware movements)
        if mouse.lLastX != 0 or mouse.lLastY != 0:
            write_log(f"{get_timestamp()} - RAW MOUSE MOVE: {mouse.lLastX}, {mouse.lLastY}")
        
        # Check mouse buttons
        button_flags = mouse._u1._s2.usButtonFlags
        
        if button_flags & RI_MOUSE_LEFT_BUTTON_DOWN:
            write_log(f"{get_timestamp()} - RAW MOUSE LEFT DOWN")
        
        if button_flags & RI_MOUSE_LEFT_BUTTON_UP:
            write_log(f"{get_timestamp()} - RAW MOUSE LEFT UP")
        
        if button_flags & RI_MOUSE_RIGHT_BUTTON_DOWN:
            write_log(f"{get_timestamp()} - RAW MOUSE RIGHT DOWN")
        
        if button_flags & RI_MOUSE_RIGHT_BUTTON_UP:
            write_log(f"{get_timestamp()} - RAW MOUSE RIGHT UP")
        
        if button_flags & RI_MOUSE_MIDDLE_BUTTON_DOWN:
            write_log(f"{get_timestamp()} - RAW MOUSE MIDDLE DOWN")
        
        if button_flags & RI_MOUSE_MIDDLE_BUTTON_UP:
            write_log(f"{get_timestamp()} - RAW MOUSE MIDDLE UP")
    
# Main function
def main():
    # Start screenshot thread if enabled
    if CAPTURE_SCREENSHOTS:
        screenshot_thread = threading.Thread(target=capture_screenshots, args=(SCREENSHOT_FREQUENCY,), daemon=True)
        screenshot_thread.start()
    
    # Create and show the main window
    main_window = create_window()
    
    try:
        # Run the Tkinter main loop
        main_window.mainloop()
    except Exception as e:
        write_log(f"{get_timestamp()} - Error in main loop: {str(e)}")
    finally:
        # Clean up
        global stop_program, taking_screenshots
        stop_program = True
        taking_screenshots = False
        kb.unhook_all()
        write_log(f"{get_timestamp()} --- Logging session ended ---")

if __name__ == "__main__":
    main()
