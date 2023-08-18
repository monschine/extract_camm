from pymp4.parser import Box
from construct import Struct

def extract_box(file_path, box_type):
    with open(file_path, 'rb') as f:
        file_bytes = f.read()
    box = Box.parse(file_bytes)
    return find_box(box, box_type)

def find_box(box, box_type):
    if box.type == box_type:
        return box
    elif isinstance(box, Struct):
        for child in box.children:
            found = find_box(child, box_type)
            if found:
                return found
    return None

# rdta_data = extract_box("/Users/jordivallverdu/Pictures/RICOH THETA Z1/R0013245.MP4", "Unknown_RDTA")
# rdtb_data = extract_box("/Users/jordivallverdu/Pictures/RICOH THETA Z1/R0013245.MP4", "Unknown_RDTB")

# print('rdta_data',rdta_data)
# print('rdtb_data',rdtb_data)


# def print_all_boxes(file_path):
#     with open(file_path, 'rb') as f:
#         file_bytes = f.read()
#     box = Box.parse(file_bytes)
#     print_boxes(box)

# def print_boxes(box):
#     print(box.type)
#     if isinstance(box, Struct):
#         for child in box.children:
#             print_boxes(child)

# print_all_boxes("/Users/jordivallverdu/Pictures/RICOH THETA Z1/R0013245.MP4")


# from mp4parse import Mp4File

# def extract_box(file_path, box_type):
#     with open(file_path, 'rb') as f:
#         mp4 = Mp4File(f)
#         for box in mp4.boxes:
#             if box.type == box_type:
#                 return box.data
#     return None

# rdta_data = extract_box("/Users/jordivallverdu/Pictures/RICOH THETA Z1/R0013245.MP4", "RDTA")
# rdtb_data = extract_box("/Users/jordivallverdu/Pictures/RICOH THETA Z1/R0013245.MP4", "RDTB")


import pymp4parse

boxes = pymp4parse.F4VParser.parse(filename='/Users/jordivallverdu/Pictures/RICOH THETA Z1/R0013245.MP4')
for box in boxes:
    print(box.type)
    print(dir(box))

