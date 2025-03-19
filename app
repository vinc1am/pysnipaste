import sys
import threading
import keyboard  
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QRubberBand
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
        print("ScreenshotOverlay initialized")
    
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
        print("Mouse released; selection:", selection)
        self.hide() 
        QTimer.singleShot(100, lambda: self.captureScreen(selection))
        self.close()
    
    def captureScreen(self, geometry: QRect):
        global latest_pixmap
        screen = QApplication.screenAt(self.mapToGlobal(geometry.topLeft()))
        if not screen:
            screen = QApplication.primaryScreen()
        print("Capturing screenshot from screen:", screen.name())
        pixmap = screen.grabWindow(0,
                                   geometry.x(),
                                   geometry.y(),
                                   geometry.width(),
                                   geometry.height())
        pixmap.save("screenshot.png", "png")
        # print("Screenshot captured and saved as screenshot.png")
        QApplication.clipboard().setPixmap(pixmap)
        # print("Screenshot copied to clipboard.")
        latest_pixmap = pixmap

class FloatingScreenshotWindow(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.label = QLabel(self)
        self.label.setPixmap(pixmap)
        self.label.adjustSize()
        self.resize(self.label.size())
        self.offset = QPoint()
        self.original_pixmap = pixmap
        self.current_pixmap = pixmap
        print("FloatingScreenshotWindow created")
    
    def mousePressEvent(self, event):
        self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        self.move(event.globalPos() - self.offset)
    
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        scale_factor = 1.1 if delta > 0 else 0.9
        new_width = int(self.current_pixmap.width() * scale_factor)
        new_height = int(self.current_pixmap.height() * scale_factor)
        if new_width < 50 or new_height < 50:
            return
        self.current_pixmap = self.original_pixmap.scaled(new_width,
                                                          new_height,
                                                          Qt.KeepAspectRatio,
                                                          Qt.SmoothTransformation)
        self.label.setPixmap(self.current_pixmap)
        self.label.adjustSize()
        self.resize(self.label.size())
    
    def mouseDoubleClickEvent(self, event):
        self.close()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySnipaste")
        layout = QVBoxLayout()
        self.capture_button = QPushButton("Capture Screenshot (Alt+<)")
        self.floating_button = QPushButton("Show Floating Screenshot (Alt+>)")
        self.quit_button = QPushButton("Quit")
        layout.addWidget(self.capture_button)
        layout.addWidget(self.floating_button)
        layout.addWidget(self.quit_button)
        self.setLayout(layout)
        self.capture_button.clicked.connect(self.trigger_capture)
        self.floating_button.clicked.connect(self.trigger_floating)
        self.quit_button.clicked.connect(self.close_application)
        self.floating_windows = []  
        print("MainWindow initialized")
    
    def trigger_capture(self):
        print("Triggering screenshot capture")
        self.overlay = ScreenshotOverlay()
        self.overlay.showFullScreen()
    
    def trigger_floating(self):
        global latest_pixmap
        print("Triggering floating screenshot display")
        if latest_pixmap is None:
            print("No screenshot available")
            return
        # Create a new floating window for the latest screenshot.
        floating = FloatingScreenshotWindow(latest_pixmap)
        floating.show()
        self.floating_windows.append(floating)
    
    def close_application(self):
        print("Quitting application")
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
    print("Main window shown")
    
    # Start the hotkey listener in a separate thread.
    threading.Thread(target=hotkey_listener, args=(main_window,), daemon=True).start()
    
    sys.exit(app.exec_())

