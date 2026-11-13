#!/usr/bin/env python3
"""Square crops centred on the child's face, so every photo frames him the same way.

Uses OpenCV's YuNet face detector (tools/models/yunet.onnx, from huggingface.co/opencv/face_detection_yunet).
With several faces, the one nearest the tapped point (subject x,y in 0..1, from the test page) wins; without a
tap, the largest face. If no face is found, the photo gets a plain centre crop and is reported.

  python3 align_faces.py OUT_DIR photo1.jpg[@x,y] photo2.jpg ...
"""
import os, sys
import cv2

MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "yunet.onnx")
FACE_SHARE = 0.22   # face width as a share of the square (head and upper body)
FACE_Y = 0.38       # face centre height in the square
SIZE = 1080


def faces(img):
    h, w = img.shape[:2]
    det = cv2.FaceDetectorYN.create(MODEL, "", (w, h), 0.6, 0.3, 50)
    _, found = det.detect(img)
    return [] if found is None else [tuple(f[:4]) for f in found]


def crop(src, subject=None):
    img = cv2.imread(src)
    h, w = img.shape[:2]
    fs = faces(img)
    if not fs:
        s = min(w, h)
        return img[(h - s) // 2:(h - s) // 2 + s, (w - s) // 2:(w - s) // 2 + s], "no face: centre crop", 0
    if subject:
        px, py = subject[0] * w, subject[1] * h
        x, y, fw, fh = min(fs, key=lambda f: (f[0] + f[2] / 2 - px) ** 2 + (f[1] + f[3] / 2 - py) ** 2)
    else:
        x, y, fw, fh = max(fs, key=lambda f: f[2] * f[3])
    s = int(min(fw / FACE_SHARE, w, h))
    cx, cy = x + fw / 2, y + fh / 2
    x0 = int(min(max(cx - s / 2, 0), w - s))
    y0 = int(min(max(cy - s * FACE_Y, 0), h - s))
    return img[y0:y0 + s, x0:x0 + s], f"face {int(fw)}px, share {fw / s:.2f}", len(fs)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for i, arg in enumerate(sys.argv[2:], 1):
        path, _, pt = arg.partition("@")
        subject = tuple(float(v) for v in pt.split(",")) if pt else None
        sq, note, n = crop(path, subject)
        cv2.imwrite(os.path.join(out, f"photo{i}-sq.jpg"),
                    cv2.resize(sq, (SIZE, SIZE), interpolation=cv2.INTER_LANCZOS4), [cv2.IMWRITE_JPEG_QUALITY, 94])
        print(i, f"faces={n}", note)


if __name__ == "__main__":
    main()
