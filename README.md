# Gameplay Data Collector

A Python-based tool for collecting and logging keyboard and mouse input data along with screen captures, ideal for gameplay analysis, user behavior studies, or input pattern recording.

## Features

- Real-time keyboard input logging
- Mouse movement, click, and scroll tracking
- High-frequency screenshot capture (configurable)
- Millisecond-precision timestamps
- User-friendly GUI interface
- Safe exit mechanism (5 ESC presses or window close)
- Organized data storage structure

## Requirements

- Python 3.6+
- Required packages:
  - `pynput`
  - `Pillow` (PIL)
  - `tkinter` (usually comes with Python)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/gameplay_data_collector.git
cd gameplay_data_collector
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the script:
```bash
python keyboard_mouse_logger.py
```

2. The program will create two directories:
   - `logs/` - Stores input event logs with timestamps
   - `screenshots/` - Stores captured screenshots (if enabled)

3. A GUI window will appear indicating that logging has started

4. To stop the program:
   - Press ESC key 5 times, or
   - Close the GUI window

## Configuration

You can modify these settings in the script:

```python
ENABLE_SCREENSHOTS = True  # Set to False to disable screenshot capture
SCREENSHOT_FREQUENCY = 60  # Screenshots per second
```

## Output Format

### Log Files
Log files are stored in the `logs` directory with timestamps and contain entries like:
```
1234567890.123 - PRESSED : 'a'
1234567890.234 - RELEASED: 'a'
1234567890.345 - MOUSE MOVED: 10, -5
1234567890.456 - MOUSE PRESSED : Button.left
```

### Screenshots
Screenshots are saved in the `screenshots` directory with timestamp-based filenames:
```
screenshot_2024-03-21_14-30-45-123.png
```

## Important Notes

- The program creates a new log file for each session
- Screenshots can consume significant disk space when enabled
- The tool must be run with appropriate permissions to capture keyboard/mouse input
- Consider adding `logs/` and `screenshots/` to your `.gitignore` file

## Contributing

Feel free to fork this repository and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 