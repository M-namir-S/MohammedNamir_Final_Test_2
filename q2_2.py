#!/usr/bin/env python3
import argparse

import cv2
import numpy as np
LOWER_RED = np.array([0, 100, 100])
UPPER_RED = np.array([10, 255, 255])


def RED_mask(img_bgr):
    blurred = cv2.GaussianBlur(img_bgr, (7, 7), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, LOWER_RED, UPPER_RED)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    return mask


def detect_objects(img_bgr, min_area_frac=0.002, min_aspect=0.6, min_solidity=0.75):
    """Return list of dicts: {'bbox': (x, y, w, h), 'centroid': (cx, cy), 'area': a}."""
    mask = RED_mask(img_bgr)
    min_area = min_area_frac * img_bgr.shape[0] * img_bgr.shape[1]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    objects = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:                                   # noise / tiny RED things
            continue
        x, y, w, h = cv2.boundingRect(c)
        if h / float(w) < min_aspect:                         # upright object: not much wider than tall
            continue
        hull_area = cv2.contourArea(cv2.convexHull(c))
        if hull_area == 0 or area / hull_area < min_solidity:  # objects are convex blobs
            continue
        m = cv2.moments(c)
        cx, cy = int(m['m10'] / m['m00']), int(m['m01'] / m['m00'])
        objects.append({'bbox': (x, y, w, h), 'centroid': (cx, cy), 'area': area})
    return sorted(objects, key=lambda b: b['centroid'][0])


def draw(img_bgr, objects):
    out = img_bgr.copy()
    for i, b in enumerate(objects, 1):
        x, y, w, h = b['bbox']
        cx, cy = b['centroid']
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.circle(out, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(out, f'#{i} ({cx},{cy})', (x, max(15, y - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2, cv2.LINE_AA)
    return out


def make_demo_image():
    img = np.full((480, 720, 3), (150, 150, 150), np.uint8)             # grey warehouse floor
    cv2.rectangle(img, (0, 0), (720, 120), (110, 110, 110), -1)          # back wall
    for (x, y, w, h) in [(80, 200, 90, 160), (300, 240, 80, 140), (520, 190, 100, 180)]:
        cv2.rectangle(img, (x, y), (x + w, y + h), (200, 60, 20), -1)    # RED (BGR) object body
        cv2.rectangle(img, (x + w // 2, y), (x + w, y + h), (160, 40, 10), -1)  # shading
        cv2.ellipse(img, (x + w // 2, y), (w // 2, 12), 0, 0, 360, (230, 110, 60), -1)
    cv2.rectangle(img, (410, 330), (480, 400), (30, 30, 200), -1)       # red box distractor
    cv2.rectangle(img, (620, 400), (700, 410), (200, 60, 20), -1)       # thin RED tape (rejected)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('image', nargs='?')
    ap.add_argument('--out', default='objects_out.png')
    ap.add_argument('--show', action='store_true')
    ap.add_argument('--demo', action='store_true')
    ap.add_argument('--camera', type=int)
    a = ap.parse_args()

    if a.camera is not None:
        cap = cv2.VideoCapture(a.camera)
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            cv2.imshow('objects (q to quit)', draw(frame, detect_objects(frame)))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        return

    img = make_demo_image() if a.demo else cv2.imread(a.image)
    if img is None:
        raise SystemExit('Provide an image path, --demo, or --camera N')

    objects = detect_objects(img)
    print(f'Detected {len(objects)} object(s)')
    for i, b in enumerate(objects, 1):
        print(f"  #{i}: bbox(x,y,w,h)={b['bbox']}  centroid={b['centroid']}")

    out = draw(img, objects)
    cv2.imwrite(a.out, out)
    print(f'Saved {a.out}')
    if a.show:
        cv2.imshow('objects', out)
        cv2.waitKey(0)


if __name__ == '__main__':
    main()