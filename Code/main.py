import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPixmap, QPainter, QTransform
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from pynput import mouse
import threading

# Tamaño de Sonic
sonicSize = 120

# 🔧 Función para acceder a recursos incluso dentro de .exe
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller lo define en ejecución
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MouseClickSignal(QObject):
    clicked_outside = pyqtSignal(QPoint)

class SonicWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.freezeMode = False
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.click_signal = MouseClickSignal()
        self.click_signal.clicked_outside.connect(self.handle_global_click)

        self.idle_timer = QTimer()
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self.anim_waiting)

        self.dragging = False
        self.offset = None

        self.sonic_speed = 10
        self.destination = None
        self.moving_timer = QTimer()
        self.moving_timer.timeout.connect(self.move_towards_destination)
        self.flip_horizontal = False

        self.frames = []
        self.current_frame = 0
        self.image = QPixmap()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.resize(1, 1)
        self.show()

        threading.Thread(target=self.start_mouse_listener, daemon=True).start()

    def start_mouse_listener(self):
        def on_click(x, y, button, pressed):
            if button == mouse.Button.left and pressed:
                pt = QPoint(x, y)
                if not self.geometry().contains(pt):
                    self.click_signal.clicked_outside.emit(pt)
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

    def handle_global_click(self, point):
        if self.freezeMode:
            return
        dest_x = point.x() - self.width() // 2
        dest_y = point.y() - self.height() // 2
        self.destination = (dest_x, dest_y)
        self.anim_run()
        self.moving_timer.start(16)

    def move_towards_destination(self):
        if not self.destination or self.freezeMode:
            return
        cx, cy = self.pos().x(), self.pos().y()
        dx = self.destination[0] - cx
        dy = self.destination[1] - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist <= self.sonic_speed:
            self.move(*self.destination)
            self.destination = None
            self.moving_timer.stop()
            self.anim_idle()
            return
        self.flip_horizontal = dx < 0
        nx = cx + int(dx / dist * self.sonic_speed)
        ny = cy + int(dy / dist * self.sonic_speed)
        self.move(nx, ny)

    def mousePressEvent(self, event):
        if self.image.rect().contains(event.pos()):
            if event.button() == Qt.LeftButton:
                self.dragging = True
                self.offset = event.pos()
                self.destination = None
                self.moving_timer.stop()
                self.anim_drag()
            elif event.button() == Qt.RightButton:
                self.freezeMode = not self.freezeMode
                print("Freeze Mode:", "Activado" if self.freezeMode else "Desactivado")
                if self.freezeMode:
                    self.anim_SONICO()
                else:
                    self.anim_idle()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.offset = None
            if self.freezeMode:
                self.anim_SONICO()
            else:
                self.anim_idle()

    def update_frame(self):
        if not self.frames:
            return
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        pixmap = self.frames[self.current_frame]
        if self.flip_horizontal:
            transform = QTransform().scale(-1, 1)
            pixmap = pixmap.transformed(transform)
        self.image = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.image.isNull():
            painter.drawPixmap(0, 0, self.image)

    def anim_idle(self):
        if self.freezeMode:
            self.anim_SONICO()
            return
        self.frames = [
            QPixmap(resource_path("assets/MiniSonicAnimations_1.png")).scaled(sonicSize, sonicSize, Qt.KeepAspectRatio, Qt.FastTransformation),
        ]
        self.current_frame = 0
        self.image = self.frames[0]
        self.resize(self.image.width(), self.image.height())
        self.timer.start(350)
        self.idle_timer.start(5000)

    def anim_waiting(self):
        self.frames = [
            QPixmap(resource_path("assets/MiniSonicAnimations_3.png")).scaled(sonicSize, sonicSize, Qt.KeepAspectRatio, Qt.FastTransformation),
            QPixmap(resource_path("assets/MiniSonicAnimations_4.png")).scaled(sonicSize, sonicSize, Qt.KeepAspectRatio, Qt.FastTransformation),
        ] * 5 + [
            QPixmap(resource_path("assets/MiniSonicAnimations_5.png")).scaled(sonicSize, sonicSize, Qt.KeepAspectRatio, Qt.FastTransformation),
        ] * 3
        self.current_frame = 0
        self.image = self.frames[0]
        self.resize(self.image.width(), self.image.height())
        self.timer.start(350)

    def anim_SONICO(self):
        self.frames = [
            QPixmap(resource_path("assets/MiniSonicAnimations_6.png")).scaled(sonicSize, sonicSize, Qt.KeepAspectRatio, Qt.FastTransformation),
            QPixmap(resource_path("assets/MiniSonicAnimations_7.png")).scaled(sonicSize, sonicSize, Qt.KeepAspectRatio, Qt.FastTransformation),
        ]
        self.current_frame = 0
        self.image = self.frames[0]
        self.resize(self.image.width(), self.image.height())
        self.timer.start(350)

    def anim_run(self):
        self.frames = [
            QPixmap(resource_path(f"assets/MiniSonicAnimations_{i}.png")).scaled(sonicSize, sonicSize, Qt.KeepAspectRatio, Qt.FastTransformation)
            for i in range(16, 24)
        ]
        self.current_frame = 0
        self.image = self.frames[0]
        self.resize(self.image.width(), self.image.height())
        self.timer.start(100)
        self.idle_timer.stop()

    def anim_drag(self):
        self.frames = [
            QPixmap(resource_path(f"assets/MiniSonicAnimations_{i}.png")).scaled(sonicSize, sonicSize, Qt.KeepAspectRatio, Qt.FastTransformation)
            for i in range(8, 16)
        ]
        self.current_frame = 0
        self.image = self.frames[0]
        self.resize(self.image.width(), self.image.height())
        self.timer.start(100)
        self.idle_timer.stop()

# Ejecutar
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SonicWindow()
    w.anim_idle()
    sys.exit(app.exec_())
