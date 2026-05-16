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

    def __init__(self, title="Window", size=(1280, 720), auto_resize=True):
        """Qt 窗口封装，用于替代 OpenCV 的窗口接口。

        参数:
        - title: 窗口标题
        - size: 初始尺寸（宽, 高），仅作初始值，后续会根据图片自适应
        - auto_resize: 是否在每次 imshow 后将窗口调整为图像大小并锁定

        实现：初始化一个中央的 `QLabel` 用作图像承载控件，默认将其尺寸策略设为固定，
        以便在 `imshow` 中用 `setFixedSize` 精确控制显示像素尺寸。
        """
        # 确保 QApplication 已存在
        self.app = _get_app()
        super().__init__()
        self.setWindowTitle(title)
        # 使用 resize 而不是 setFixedSize，以便后续可以自适应调整窗口大小
        self.resize(*size)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        # 允许 QLabel 根据内容固定大小（当 auto_resize 启用时会设置）
        self.image_label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.layout.addWidget(self.image_label)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.image_label.setMouseTracking(True)
        self._last_key = -1
        self.auto_resize = auto_resize
        self.show()

    def imshow(self, img_bgr):
        """在窗口中显示一张 BGR 图像。

        步骤：
        1. 将 OpenCV 的 BGR 数据转换为 Qt 可用的 QImage(RGB 或灰度)。
        2. 将 QImage 转为 QPixmap(用于 QLabel 显示)。
        3. 限定显示最大尺寸不超过屏幕可用区域，超出则等比缩放。
        4. 根据 `auto_resize` 决定：
           - True:将 `QLabel` 精确设置为图像像素尺寸，`adjustSize()` 使主窗口贴合内容，
             然后用 `setFixedSize()` 锁定窗口，防止用户拖动改变大小。
           - False:按当前 `QLabel` 尺寸缩放显示（兼容旧行为）。
        """
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
            # QImage 需要每行的字节数（channels * width）
            bytes_per_line = ch * w
            qt_img = QtGui.QImage(img_rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        else:
            qt_img = QtGui.QImage(img_rgb.data, w, h, QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap.fromImage(qt_img)

        # 限制最大显示尺寸为屏幕可用区域，避免窗口超出屏幕
        try:
            screen_geom = self.app.primaryScreen().availableGeometry()
            max_w = max(100, screen_geom.width() - 100)
            max_h = max(100, screen_geom.height() - 100)
        except Exception:
            max_w, max_h = 1920, 1080

        display_pixmap = pixmap
        if pixmap.width() > max_w or pixmap.height() > max_h:
            display_pixmap = pixmap.scaled(max_w, max_h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

        if getattr(self, 'auto_resize', True):
            # 让 QLabel 固定为图像尺寸，然后调整窗口以贴合内容
            self.image_label.setFixedSize(display_pixmap.size())
            self.image_label.setPixmap(display_pixmap)
            # 调整主窗口尺寸以适应内容（包含布局边距）
            self.adjustSize()
            # 固定窗口大小，禁止用户手动拖动改变窗口尺寸
            self.setFixedSize(self.size())
        else:
            # 保持之前逻辑：将图像缩放到标签大小
            scaled_pixmap = display_pixmap.scaled(self.image_label.size(), QtCore.Qt.KeepAspectRatio,
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
        """将 QLabel 中的 Qt 坐标映射回图片像素坐标。

        说明：当 QLabel 中的 pixmap 比 label 小（由于保持纵横比居中显示），
        需要计算偏移量和缩放因子后将窗口坐标映射为图像像素坐标。
        返回值在无图像或计算异常时为 (-1, -1)。
        """
        if self.image_label.pixmap() is None:
            return -1, -1
        label_rect = self.image_label.rect()
        pix_rect = self.image_label.pixmap().rect()
        # 计算像素缩放因子（注意是 pixmap 相对 label 的比例）
        scale_x = pix_rect.width() / max(label_rect.width(), 1)
        scale_y = pix_rect.height() / max(label_rect.height(), 1)
        # 计算居中显示时的偏移
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
    # flags 未细化处理；当前实现会创建一个支持自动根据图像大小调整的窗口
    if winname not in _windows:
        # 默认启用 auto_resize
        _windows[winname] = QtWindow(title=winname, auto_resize=True)