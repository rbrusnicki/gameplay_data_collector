# Gameplay Data Collector

A Python-based tool for collecting and logging keyboard and mouse input data along with screen captures, specifically designed for behavioral cloning applications. This tool is ideal for gathering training data to teach AI models to mimic human gameplay patterns, user behavior studies, or input pattern recording.

## What is Behavioral Cloning?

Behavioral cloning is a technique where an AI model learns to perform tasks by imitating human demonstrations. This tool captures the necessary input data (keystrokes, mouse movements) and corresponding visual context (screenshots) that can be used to train machine learning models to replicate human behavior in games or other applications.

## Features

- Real-time keyboard input logging
- Optimized log file size (only logs key state changes, not continuous presses)
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

1. Run the main logger script:
```bash
python combined_logger.py
```

2. The program will create two directories:
   - `logs/` - Stores input event logs with timestamps
   - `screenshots/` - Stores captured screenshots (if enabled)

3. A GUI window will appear indicating that logging has started

4. To stop the program:
   - Press ESC key 5 times, or
   - Close the GUI window

### Additional Utilities

The repository also includes this utility script:

- `visualize_mouse_data.py` - Generate visualizations of collected mouse movement data

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

The logger is optimized to only record key state changes:
- A key press is logged only when the key is initially pressed down
- A key release is logged only when the key is released
- Holding a key down does not generate multiple log entries

This optimization ensures clean, efficient data for behavioral cloning models while maintaining all necessary information about input timing and sequence.

### Screenshots
Screenshots are saved in the `screenshots` directory with timestamp-based filenames:
```
screenshot_2024-03-21_14-30-45-123.png
```

These screenshots provide the visual context that can be paired with input actions for training behavioral cloning models.

## Important Notes

- The program creates a new log file for each session
- The logger efficiently tracks key states to minimize log file size
- Screenshots can consume significant disk space when enabled
- The tool must be run with appropriate permissions to capture keyboard/mouse input
- Consider adding `logs/` and `screenshots/` to your `.gitignore` file
- For behavioral cloning applications, ensure you collect sufficient data across various scenarios

## Data Processing for Behavioral Cloning

After collecting data with this tool, you can:
1. Synchronize input events with corresponding screenshots using timestamps
2. Preprocess the data into training examples (input state → action pairs)
3. Train a machine learning model (e.g., neural network) to predict actions based on visual input
4. Test the trained model by having it control the game/application

## Contributing

Feel free to fork this repository and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 