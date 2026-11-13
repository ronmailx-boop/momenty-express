import cv2, sys
casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
FACE_FRAC, CY = 0.28, 0.40  # face width as share of the square, face centre height
for i, src in enumerate(sys.argv[1:], 1):
    img = cv2.imread(src); h, w = img.shape[:2]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = casc.detectMultiScale(g, 1.1, 6, minSize=(int(min(w, h) * 0.06),) * 2)
    if len(faces) == 0: print(i, "no face"); continue
    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
    S = min(int(fw / FACE_FRAC), w, h)
    cx, cy = x + fw / 2, y + fh / 2
    x0 = int(min(max(cx - S / 2, 0), w - S)); y0 = int(min(max(cy - S * CY, 0), h - S))
    out = cv2.resize(img[y0:y0 + S, x0:x0 + S], (1080, 1080), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(f"photo{i}-sq.jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 94])
    print(i, "faces", len(faces), "face", (x, y, fw, fh), "crop", S, "face share", round(fw / S, 2))
