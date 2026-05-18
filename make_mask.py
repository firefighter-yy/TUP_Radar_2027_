# 绘制掩码地图
import cv2
from qt_display import imshow, waitKey, setMouseCallback, destroyAllWindows, namedWindow

cv2.imshow = imshow
cv2.waitKey = waitKey
cv2.setMouseCallback = setMouseCallback
cv2.destroyAllWindows = destroyAllWindows
cv2.namedWindow = namedWindow

import numpy as np

# 全局变量
drawing = False
current_points = []
mask_image = None
original_image = None
color_mode = "green"  # 初始模式为绿色

# 鼠标回调函数
def mouse_callback(event, x, y, flags, param):
    """
    - event: OpenCV 鼠标事件常量（例如 EVENT_LBUTTONDOWN, EVENT_MOUSEMOVE, EVENT_LBUTTONUP)
    - (x, y): 映射到原始图像坐标的像素位置（可为超出边界的值，见 qt_display 的映射策略）
    - flags: 保留参数(当前始终为0)
    """
    global drawing, current_points, mask_image, color_mode
    real_x, real_y = x, y  # 直接使用映射后的坐标（可能超出图像边界）

    if event == cv2.EVENT_LBUTTONDOWN:  # 左键按下开始绘制
        drawing = True
        current_points = [(real_x, real_y)]  # 清空当前点列表，并添加第一个点
        # 仅打印坐标点（起点）
        print(f"起点：{real_x},{real_y}")

    elif event == cv2.EVENT_MOUSEMOVE and drawing:  # 移动时记录点并预览
        current_points.append((real_x, real_y))
        preview = original_image.copy()             # 用于预览
        pts = np.array(current_points, dtype=np.int32)  # 转换为整型数组以供绘制
        cv2.polylines(preview, [pts], False, (0, 255, 0) if color_mode == "green" else (255, 0, 0), 2)  # 绘制当前线条
        cv2.imshow("Image", preview)

    elif event == cv2.EVENT_LBUTTONUP:  # 左键释放结束绘制
        drawing = False
        current_points.append((real_x, real_y))  # 添加最后一个点
        # 仅打印坐标点（终点）
        print(f"终点：{real_x},{real_y}")

        # 绘制闭合区域到掩码图像（使用整型点数组）
        color = (0, 255, 0) if color_mode == "green" else (255, 0, 0)
        pts = np.array(current_points, dtype=np.int32)
        cv2.fillPoly(mask_image, [pts], color)

        # 显示更新后的掩码图
        mask_preview = cv2.addWeighted(original_image, 0.5, mask_image, 0.5, 0) # 叠加显示原图和掩码
        cv2.imshow("Image", mask_preview)

# 主函数
def create_irregular_mask(image_path):
    global mask_image, original_image, color_mode

    # 读取图像
    original_image = cv2.imread(image_path)
    if original_image is None:
        print("Failed to load image.")
        return

    # 创建黑色掩码图像
    mask_image = np.zeros_like(original_image, dtype=np.uint8)

    # 创建窗口并绑定鼠标事件
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", mouse_callback)

    print("Instructions:")
    print("1. Click and drag to define a region (release to finish).")
    print("2. Press 'n' to switch to the next region color (green -> blue).")
    print("3. Press 'q' to quit and save the mask.")

    while True:
        # 显示当前图像
        combined_preview = cv2.addWeighted(original_image, 0.5, mask_image, 0.5, 0)
        cv2.imshow("Image", combined_preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # 按 'q' 退出
            break
        elif key == ord('n'):  # 按 'n' 切换颜色模式
            color_mode = "blue" if color_mode == "green" else "green"
            print(f"Switched to {color_mode} mode.")

    cv2.destroyAllWindows()

    # 保存掩码图像
    cv2.imwrite("images-2027/map_mask_2027.jpg", mask_image)
    print("Mask image saved as 'images-2027/map_mask_2027.jpg'.")

# 使用示例
if __name__ == "__main__":
    # 替换为你的图像路径
    create_irregular_mask("images-2027/map_blue.jpg")
