import cv2, numpy as np

with open("no_logo_byte_array_file.txt", "rb") as file:
    no_logo_byte_array = file.read()

nparr2 = np.frombuffer(no_logo_byte_array, np.uint8)
no_img = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)
no_img_gray = cv2.cvtColor(no_img, cv2.COLOR_BGR2GRAY)

orb = cv2.ORB_create(
    nfeatures=200,
    scaleFactor=1.3,
    edgeThreshold=15
)

kpB, desB = orb.detectAndCompute(no_img_gray, None)

bf = cv2.BFMatcher(cv2.NORM_HAMMING)

def check_no_logo(img1_bytes):
    try:
        nparr1 = np.frombuffer(img1_bytes, np.uint8)
        img1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)

        if img1 is None:
            return 0

        img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        kpA, desA = orb.detectAndCompute(img1_gray, None)

        if len(kpA) < 10:
            return 0

        matches = bf.knnMatch(desA, desB, k=2)

        good_matches = [m for m, n in matches if m.distance < 0.7 * n.distance]

        max_matches = min(len(kpA), len(kpB))
        if max_matches == 0:
            return 0

        similarity = (len(good_matches) / max_matches) * 100
        return min(similarity, 100)

    except Exception as e:
        print(f"Comparison error: {e}")
        return 0