import torch
import math


class KeyPointNames:
    list = [
        "nose",
        "left_eye",
        "right_eye",
        "left_ear",
        "right_ear",
        "left_shoulder",
        "right_shoulder",
        "left_elbow",
        "right_elbow",
        "left_wrist",
        "right_wrist",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
    ]


class AngleNames:
    list = [
        "left_elbow",
        "right_elbow",
        "left_knee",
        "right_knee",
        "right_shoulder",
        "left_shoulder",
        "right_hip",
        "left_hip",
    ]
    combinations = [
        (5, 7, 9),
        (6, 8, 10),
        (11, 13, 15),
        (12, 14, 16),
        (5, 6, 8),
        (6, 5, 7),
        (11, 12, 14),
        (12, 11, 13),
    ]


def compute_angle(p1, p2, p3):
    # Calculate angle given 3 points using the dot product and arc cosine
    vector_a = p1 - p2
    vector_b = p3 - p2

    # Normalize the vectors (to make them unit vectors)
    vector_a = vector_a / torch.norm(vector_a)
    vector_b = vector_b / torch.norm(vector_b)

    # Compute the angle
    cosine_angle = torch.sum(vector_a * vector_b)
    angle_radians = torch.acos(cosine_angle)
    angle_degrees = angle_radians * 180 / math.pi

    if math.isnan(angle_degrees):
        angle_degrees = -1.0
    return angle_degrees


def write_to(out_file, results):
    """
    Writes pose output given Results list/generator [results] to [out_file].
    If angle DNE, sets angle to -1.
    """
    with open(out_file, "w") as f:
        f.write("")
    frameno = 0
    for result in results:
        frameno += 1
        if result.boxes is None:
            continue
        boxes = result.boxes
        xywh = boxes.xywh.numpy()
        xy = result.keypoints.xy.numpy()
        n, _, _ = xy.shape
        for j in range(n):
            s = str(frameno)
            s += " " + str(0)
            s += " " + str(0)
            kp = xy[j]
            for x in xywh[j, :]: # keypoints
                s += " " + str(int(x))
            s += " " + " ".join(kp.flatten().astype(int).astype(str))

            for combo in AngleNames.combinations: # angles
                angle = compute_angle(
                    torch.tensor(kp[combo[0]]),
                    torch.tensor(kp[combo[1]]),
                    torch.tensor(kp[combo[2]]),
                )
                s += " " + str(int(angle))
            with open(out_file, "a") as f:
                f.write(s + "\n")