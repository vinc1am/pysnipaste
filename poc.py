import sys
import threading
import keyboard  
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QLabel, QRubberBand, QStyle
from PyQt5.QtCore import QRect, QPoint, Qt, QSize, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon

latest_pixmap = None

class ScreenshotOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Select Area')
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        # print("ScreenshotOverlay initialized")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 51))
    
    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()
        # print("Mouse pressed at:", event.pos())
    
    def mouseMoveEvent(self, event):
        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        # print("Mouse moved to:", event.pos())
    
    def mouseReleaseEvent(self, event):
        selection = self.rubberBand.geometry()
        self.rubberBand.hide()
        # print("Mouse released; selection:", selection)
        self.hide() 
        QTimer.singleShot(100, lambda: self.captureScreen(selection))
        self.close()
    
    def captureScreen(self, geometry: QRect):
        global latest_pixmap
        screen = QApplication.screenAt(self.mapToGlobal(geometry.topLeft()))
        if not screen:
            screen = QApplication.primaryScreen()
        # print("Capturing screenshot from screen:", screen.name())
        pixmap = screen.grabWindow(0,
                                   geometry.x(),
                                   geometry.y(),
                                   geometry.width(),
                                   geometry.height())
        # pixmap.save("screenshot.png", "png")
        # print("Screenshot captured and saved as screenshot.png")
        QApplication.clipboard().setPixmap(pixmap)
        # print("Screenshot copied to clipboard.")
        latest_pixmap = pixmap

class FloatingScreenshotWindow(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_StaticContents)
        self.label = QLabel(self)

        self.original_pixmap = pixmap
        self.current_pixmap = pixmap.copy()
        self.drawing_pixmap = QPixmap(self.current_pixmap.size())
        self.drawing_pixmap.fill(Qt.transparent)

        self.label.setPixmap(self.get_combined_pixmap())
        self.label.adjustSize()
        self.resize(self.label.size())

        self.offset = QPoint()
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        # print("FloatingScreenshotWindow with box highlighting created")

    def get_combined_pixmap(self):
        combined = QPixmap(self.current_pixmap.size())
        combined.fill(Qt.transparent)
        painter = QPainter(combined)
        painter.drawPixmap(0, 0, self.current_pixmap)
        painter.drawPixmap(0, 0, self.drawing_pixmap)
        painter.end()
        return combined

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            # print("Started box highlight at", event.pos())
        elif event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.drawing and (event.buttons() & Qt.RightButton):
            self.end_point = event.pos()
            # Temporary preview by copying pixmap
            preview_pixmap = self.drawing_pixmap.copy()
            painter = QPainter(preview_pixmap)
            brush_color = QColor(255, 255, 0, 100)  # semi-transparent yellow
            painter.fillRect(QRect(self.start_point, self.end_point).normalized(), brush_color)
            painter.end()
            combined = QPixmap(self.current_pixmap.size())
            painter = QPainter(combined)
            painter.drawPixmap(0, 0, self.current_pixmap)
            painter.drawPixmap(0, 0, preview_pixmap)
            painter.end()
            self.label.setPixmap(combined)
            self.label.adjustSize()
        elif event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton and self.drawing:
            self.drawing = False
            self.end_point = event.pos()
            painter = QPainter(self.drawing_pixmap)
            brush_color = QColor(255, 255, 0, 100)  # semi-transparent yellow
            painter.fillRect(QRect(self.start_point, self.end_point).normalized(), brush_color)
            painter.end()
            combined = self.get_combined_pixmap()
            self.label.setPixmap(combined)
            self.label.adjustSize()
            QApplication.clipboard().setPixmap(combined)
            # print("Finished box highlight and updated clipboard at", event.pos())

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        scale_factor = 1.1 if delta > 0 else 0.9
        new_width = int(self.current_pixmap.width() * scale_factor)
        new_height = int(self.current_pixmap.height() * scale_factor)
        if new_width < 50 or new_height < 50:
            return
        
        self.current_pixmap = self.original_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.drawing_pixmap = QPixmap(self.current_pixmap.size())
        self.drawing_pixmap.fill(Qt.transparent)
        
        self.label.setPixmap(self.get_combined_pixmap())
        self.label.adjustSize()
        self.resize(self.label.size())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.close()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySnipaste")
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.capture_button = QPushButton("Capture")
        self.capture_button.setToolTip("Alt + <")
        self.capture_button.setMinimumWidth(80)
        self.capture_button.setStyleSheet(self.button_style())

        self.floating_button = QPushButton("Preview")
        self.floating_button.setToolTip("Alt + >")
        self.floating_button.setMinimumWidth(80)
        self.floating_button.setStyleSheet(self.button_style())

        layout.addWidget(self.capture_button)
        layout.addWidget(self.floating_button)

        self.setLayout(layout)
        self.resize(250, 45)
        self.setWindowFlags(self.windowFlags() | Qt.MSWindowsFixedSizeDialogHint)

        self.capture_button.clicked.connect(self.trigger_capture)
        self.floating_button.clicked.connect(self.trigger_floating)
        self.floating_windows = []
        # print("MainWindow initialized")


    def button_style(self):
        return """
            QPushButton {
                background-color: #007ACC;
                color: white;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #005F9E;
            }
            QPushButton:pressed {
                background-color: #003F6B;
            }
        """
    
    def trigger_capture(self):
        # print("Triggering screenshot capture")
        self.overlay = ScreenshotOverlay()
        self.overlay.showFullScreen()
    
    def trigger_floating(self):
        global latest_pixmap
        print("Triggering floating screenshot display")
        if latest_pixmap is None:
            # print("No screenshot available")
            return
        # Create a new floating window for the latest screenshot.
        floating = FloatingScreenshotWindow(latest_pixmap)
        floating.show()
        self.floating_windows.append(floating)
    
    def close_application(self):
        # print("Quitting application")
        self.close()

def hotkey_listener(main_window):
    # Register global hotkeys for Alt+< and Alt+>
    # Use QTimer.singleShot to safely invoke Qt functions from the thread.
    keyboard.add_hotkey('alt+<', lambda: QTimer.singleShot(0, main_window.trigger_capture))
    keyboard.add_hotkey('alt+>', lambda: QTimer.singleShot(0, main_window.trigger_floating))
    # This call will block this thread, but it's running as a daemon.
    keyboard.wait()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("pysnipaste.ico"))
    main_window = MainWindow()
    main_window.show()
    # print("Main window shown")
      
    # Start the hotkey listener in a separate thread.
    threading.Thread(target=hotkey_listener, args=(main_window,), daemon=True).start()
    
    sys.exit(app.exec_())


## pyinstaller --onefile --windowed --icon=pysnipaste.ico --add-data "pysnipaste.ico;." app.py
## PyQt5
## keyboard

