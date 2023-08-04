from pymp4.parser import Box
from construct.core import RangeError
import numpy as np


def find_camm_boxes(fp):
    boxes = []
    while True:
        try:
            box = Box.parse_stream(fp)
        except RangeError:
            break
        if box.type.decode('utf-8') == 'camm':
            boxes.append(box)
        if box.size > 8:
            fp.seek(box.offset + box.size)
    return boxes


def decode_angle_axis(encoded_vec):
    # Calculate the axis of rotation by normalizing the encoded vector
    axis = encoded_vec / np.linalg.norm(encoded_vec)
    
    # Calculate the rotation angle in radians by finding the length of the encoded vector
    angle_radians = np.linalg.norm(encoded_vec)
    
    return axis, angle_radians
def extract_camm_track(video_path):

    with open(video_path, 'rb') as fp:
        camm_boxes = find_camm_boxes(fp)

        print(camm_boxes)
        # Here you have all the 'camm' boxes in the video file
        # You can now decode the content of each box according to the specifications
        for box in camm_boxes:
            # Assume the content of the box is a binary representation of the encoded angle-axis vector
            encoded_vec = np.frombuffer(box.content, dtype=np.float32)
            
            # Decode the encoded angle-axis vector
            axis, angle_radians = decode_angle_axis(encoded_vec)
            
            # Now you have the axis of rotation and the rotation angle in radians
            print("Axis:", axis)
            print("Angle (in radians):", angle_radians)

    # return camm_data

video_path = "R0013304_0.MP4"
camm_data = extract_camm_track(video_path)
