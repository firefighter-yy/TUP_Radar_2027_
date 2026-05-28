from pathlib import Path
import cv2
import yaml
import sys
from qt_display import imshow, waitKey, setMouseCallback, destroyAllWindows, namedWindow

def load_test_video(cfg_path="config.yaml"):
    cfg_path = Path(cfg_path)
    with cfg_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    video_rel = config['paths']['test_video']
    return Path(video_rel)


def play_and_save(video_path: Path, out_dir: Path = Path("test")):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    delay = int(1000.0 / fps) if fps > 0 else 33

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        imshow("Video", frame)
        key = waitKey(delay)
        if key == ord("q"):
            break
        if key == ord("s"):
            out_path = out_dir / "video_image.jpg"
            ok = cv2.imwrite(str(out_path), frame)
            if ok:
                print(f"保存成功: {out_path}")
            else:
                print(f"保存失败: {out_path}")

    cap.release()
    destroyAllWindows()


def main():
    video_path = load_test_video("config.yaml")
    try:
        play_and_save(video_path, out_dir=Path("test"))
    except Exception as e:
        print("运行出错:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
