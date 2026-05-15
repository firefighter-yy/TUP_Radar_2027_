# qt_display.py
import sys
import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

# 全局 QApplication 单例
_app = None

def _get_app():
    """获取或创建 QApplication 实例"""
    global _app
    if _app is None:
        _app = QtWidgets.QApplication.instance()
        if _app is None:
            _app = QtWidgets.QApplication(sys.argv)
    return _app

# 全局窗口字典
_windows = {}

class QtWindow(QtWidgets.QMainWindow):
    key_pressed = QtCore.pyqtSignal(int)
    mouse_event = QtCore.pyqtSignal(int, int, int)

    def __init__(self, title="Window", size=(1280, 720)):
        # 确保 QApplication 已存在
        self.app = _get_app()
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(*size)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.image_label)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.image_label.setMouseTracking(True)
        self._last_key = -1
        self.show()

    def imshow(self, img_bgr):
        if img_bgr is None:
            return
        # BGR -> RGB
        if len(img_bgr.shape) == 3:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = img_bgr
        h, w = img_rgb.shape[:2]
        if len(img_rgb.shape) == 3:
            ch = img_rgb.shape[2]
            bytes_per_line = ch * w
            qt_img = QtGui.QImage(img_rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        else:
            qt_img = QtGui.QImage(img_rgb.data, w, h, QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap.fromImage(qt_img)
        scaled_pixmap = pixmap.scaled(self.image_label.size(), QtCore.Qt.KeepAspectRatio,
                                      QtCore.Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def keyPressEvent(self, event):
        key = event.key()
        # 转换为 ASCII 码
        if QtCore.Qt.Key_A <= key <= QtCore.Qt.Key_Z:
            key = ord(chr(key).lower())
        elif QtCore.Qt.Key_0 <= key <= QtCore.Qt.Key_9:
            key = ord(chr(key))
        elif key == QtCore.Qt.Key_Space:
            key = ord(' ')
        elif key == QtCore.Qt.Key_Escape:
            key = 27
        elif key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            key = 13
        else:
            key = -1
        self._last_key = key
        self.key_pressed.emit(key)
        if key == 27:
            self.close()

    def waitKey(self, delay=1):
        app = _get_app()
        app.processEvents()
        key = self._last_key
        self._last_key = -1
        if delay > 0:
            loop = QtCore.QEventLoop()
            QtCore.QTimer.singleShot(delay, loop.quit)
            loop.exec_()
        return key

    def mousePressEvent(self, event):
        x, y = self._map_to_image_coords(event.pos())
        self.mouse_event.emit(0, x, y)

    def mouseMoveEvent(self, event):
        x, y = self._map_to_image_coords(event.pos())
        self.mouse_event.emit(1, x, y)

    def mouseReleaseEvent(self, event):
        x, y = self._map_to_image_coords(event.pos())
        self.mouse_event.emit(2, x, y)

    def _map_to_image_coords(self, qt_pos):
        if self.image_label.pixmap() is None:
            return -1, -1
        label_rect = self.image_label.rect()
        pix_rect = self.image_label.pixmap().rect()
        scale_x = pix_rect.width() / max(label_rect.width(), 1)
        scale_y = pix_rect.height() / max(label_rect.height(), 1)
        x_offset = (label_rect.width() - pix_rect.width()) // 2
        y_offset = (label_rect.height() - pix_rect.height()) // 2
        img_x = int((qt_pos.x() - x_offset) / scale_x) if scale_x != 0 else -1
        img_y = int((qt_pos.y() - y_offset) / scale_y) if scale_y != 0 else -1
        return img_x, img_y

def imshow(winname, img):
    if winname not in _windows:
        _windows[winname] = QtWindow(title=winname)
    _windows[winname].imshow(img)

def waitKey(delay=1):
    # 确保至少有一个窗口存在，否则无法等待
    if not _windows:
        return -1
    app = _get_app()
    # 处理所有窗口的事件，收集第一个按键
    key = -1
    for win in _windows.values():
        k = win.waitKey(0)  # 内部会调用 processEvents 和循环
        if k != -1:
            key = k
    app.processEvents()
    return key

def setMouseCallback(winname, callback, param=None):
    if winname not in _windows:
        _windows[winname] = QtWindow(title=winname)
    def handler(event, x, y):
        callback(event, x, y, 0, param)  # flags 固定为 0
    _windows[winname].mouse_event.connect(handler)

def destroyAllWindows():
    for win in _windows.values():
        win.close()
    _windows.clear()

def namedWindow(winname, flags=0):
    pass