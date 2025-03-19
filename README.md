# PySnipaste

## Pure-Python Lightweight Snipaste Alternative

# Work In Progress

### Overview
PySnipaste is a lightweight, pure-Python alternative to Snipaste, designed for users who require a secure, offline screenshot tool. This tool replicates the core functionalities of Snipaste, allowing users to capture screenshots and interact with floating images effortlessly.

### Features
- **Screenshot Capture:** Take screenshots with a simple hotkey.
- **Floating Image Window:** Display captured images as draggable, resizable floating windows.
- **Resize with Scroll:** Adjust the image size using the scroll wheel.
- **Remove with Double-Click:** Double-click on an image to remove it from the screen (without deleting the file).
- **Offline & Secure:** No network connection required, ensuring security and privacy.

### Usage
1. **Run the script:**
   ```sh
   python app.py
   ```
2. **Use the hotkeys:**
   - `ALT + <` → Take a screenshot (existing function, unchanged)
   - `ALT + >` → Display the last removed floating image
   - **Scroll Wheel** → Resize floating image
   - **Double-Click** → Remove floating image
