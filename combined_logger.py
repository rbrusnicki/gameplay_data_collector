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
from pynput import mouse, keyboard

# Define WM_INPUT since it's not in win32con
WM_INPUT = 0x00FF

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

# Generate a unique file name based on the current timestamp
log_file = os.path.join(logs_folder, datetime.now().strftime('%Y-%m-%d %H-%M-%S') + '_log.txt')

# Open the file in append mode to log data
with open(log_file, 'a') as f:
    f.write(f"--- Logging session started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---\n")

# Global variables
stop_program = False
esc_pressed = 0
window = None
keyboard_listener = None
mouse_listener = None
original_wnd_proc = None

# Dictionary to track the state of each key (pressed or released)
key_states = {}

# Function to write to log file
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

# Add RIDEV_INPUTSINK flag
RIDEV_INPUTSINK = 0x00000100

# Additional constants not always in win32con
RID_INPUT = 0x10000003

# Define how to handle key presses
def on_press(key):
    global key_states
    
    # Convert key to string representation for dictionary key
    key_str = str(key)
    
    # Only log if the key wasn't already pressed
    if key_str not in key_states or key_states[key_str] == 'released':
        try:
            write_log(f"{get_timestamp()} - PRESSED : {key.char}")
        except AttributeError:
            write_log(f"{get_timestamp()} - PRESSED : {key}")
        
        # Update key state
        key_states[key_str] = 'pressed'

# Define how to handle key releases
def on_release(key):
    global stop_program, keyboard_listener, mouse_listener, key_states
    
    # Convert key to string representation for dictionary key
    key_str = str(key)
    
    # Only log if the key was previously pressed
    if key_str not in key_states or key_states[key_str] == 'pressed':
        try:
            write_log(f"{get_timestamp()} - RELEASED: {key.char}")
        except AttributeError:
            write_log(f"{get_timestamp()} - RELEASED: {key}")
        
        # Update key state
        key_states[key_str] = 'released'

    # Keep the 'Esc' key logging but terminate on five 'Esc' presses
    if key == keyboard.Key.esc:
        global esc_pressed
        esc_pressed += 1
        if esc_pressed == 5:
            write_log(f"{get_timestamp()} --- Logging session ended by pressing ESC 5 times ---")
            stop_program = True
            # Stop both listeners when Esc is pressed five times
            if keyboard_listener:
                keyboard_listener.stop()
            if mouse_listener:
                mouse_listener.stop()
            if window:
                window.destroy()  # Close the tkinter window
            return False  # Stop the keyboard listener
    else:
        esc_pressed = 0

# Define how to handle mouse clicks (using pynput)
def on_click(x, y, button, pressed):
    if stop_program:
        return False
    if pressed:
        write_log(f"{get_timestamp()} - MOUSE PRESSED : {button}")
    else:
        write_log(f"{get_timestamp()} - MOUSE RELEASED: {button}")

# Define how to handle mouse scroll (using pynput)
def on_scroll(x, y, dx, dy):
    write_log(f"{get_timestamp()} - MOUSE SCROLLED: {dx}, {dy}")

# Function to setup raw input for mouse
def setup_raw_input(hwnd):
    # Register for raw input - mouse only
    raw_mouse = RAWINPUTDEVICE(
        usUsagePage=0x01,      # HID_USAGE_PAGE_GENERIC
        usUsage=0x02,          # HID_USAGE_GENERIC_MOUSE
        dwFlags=RIDEV_INPUTSINK,  # Use RIDEV_INPUTSINK to receive input in background
        hwndTarget=hwnd        # Target window to receive input
    )
    
    # Register mouse device
    devices = (RAWINPUTDEVICE * 1)(raw_mouse)
    
    result = ctypes.windll.user32.RegisterRawInputDevices(devices, 1, ctypes.sizeof(RAWINPUTDEVICE))
    if result == 0:  # 0 means failure
        error_code = ctypes.GetLastError()
        write_log(f"{get_timestamp()} - Error registering raw input devices. Code: {error_code}")
        print(f"Error registering raw input devices. Code: {error_code}")
    else:
        write_log(f"{get_timestamp()} - Successfully registered raw input devices")
        print("Successfully registered raw input devices")

# Function to process raw input data - ONLY for mouse movement
def process_raw_input(lparam):
    try:
        buffer_size = wintypes.UINT()
        
        # Get the size of the input data
        result = ctypes.windll.user32.GetRawInputData(
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
        
        # Process mouse input - ONLY for movement
        if raw_input.header.dwType == RIM_TYPEMOUSE:
            mouse = raw_input._u1.mouse
            
            # Log relative movements (this is what we want - hardware movements)
            if mouse.lLastX != 0 or mouse.lLastY != 0:
                write_log(f"{get_timestamp()} - MOUSE MOVED: {mouse.lLastX}, {mouse.lLastY}")
                print(f"Mouse moved: {mouse.lLastX}, {mouse.lLastY}")  # Debug print
    except Exception as e:
        print(f"Error processing raw input: {e}")
        write_log(f"{get_timestamp()} - Error processing raw input: {str(e)}")

# Function to create a tkinter window
def create_window():
    global window, original_wnd_proc
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
        write_log(f"{get_timestamp()} --- Logging session ended by window close ---")
        # Stop both listeners
        if keyboard_listener:
            keyboard_listener.stop()
        if mouse_listener:
            mouse_listener.stop()
        window.destroy()  # Close the window

    window.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Get the window handle after it's created and visible
    window.update()
    hwnd = window.winfo_id()
    
    # Register for raw input
    setup_raw_input(hwnd)
    
    # Set up a custom message handler
    def wnd_proc(hwnd, msg, wparam, lparam):
        try:
            if msg == WM_INPUT:
                process_raw_input(lparam)
        except Exception as e:
            print(f"Error in window procedure: {e}")
        return win32gui.CallWindowProc(original_wnd_proc, hwnd, msg, wparam, lparam)
    
    # Set the window procedure
    original_wnd_proc = win32gui.SetWindowLong(hwnd, win32con.GWL_WNDPROC, wnd_proc)
    
    return window

def main():
    global keyboard_listener, mouse_listener, window
    
    # Start the screenshot thread if enabled
    if ENABLE_SCREENSHOTS:
        screenshot_thread = threading.Thread(target=capture_screenshots, args=(SCREENSHOT_FREQUENCY,), daemon=True)
        screenshot_thread.start()
    
    try:
        # Create the tkinter window first
        window = create_window()
        
        # Set up listeners for both keyboard and mouse
        keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        mouse_listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
        
        # Start the listeners
        keyboard_listener.start()
        mouse_listener.start()
        
        # Run the tkinter main loop
        window.mainloop()
        
    except Exception as e:
        print(f"Error in main function: {e}")
        write_log(f"{get_timestamp()} - Error in main function: {str(e)}")
    finally:
        # Clean up
        global stop_program, taking_screenshots
        stop_program = True
        taking_screenshots = False
        
        # Stop listeners if they exist
        if keyboard_listener:
            keyboard_listener.stop()
        if mouse_listener:
            mouse_listener.stop()
            
        write_log(f"{get_timestamp()} --- Logging session ended ---")

if __name__ == "__main__":
    main() 