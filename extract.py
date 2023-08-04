from pymp4.parser import Box
from construct.core import RangeError
import numpy as np
import os
import struct

def extract_rotation_values(mp4_file_path):
    # Define the binary pattern for the header information
    header_pattern = b'CameraMetadataMotionHandler'

    # Open the mp4 file in binary mode and read the data
    with open(mp4_file_path, 'rb') as file:
        data = file.read()

    # Find the start position of the rotation values
    start_pos = data.find(header_pattern)
    if start_pos == -1:
        raise ValueError("Header pattern not found in file")

    print('start_pos0', start_pos)

    # Extract and print the values after the given index
    # Used to validate the starting point
    # values_after_point = data[start_pos:start_pos+173]
    # print('values_after_point', values_after_point)
    
    # we are adding 173 positions in order to get to the end of the lines that are expected to be the beginning of the rotation data
    # CameraMetadataMotionHandler�����minf���,hdlr����dhlrurl ������������DataHandler����$dinf���dref����������url ������0stbl��� stsd����������camm���������q�stts������:�
    start_pos1 = start_pos + 173
    print('start_pos1', start_pos1)


    header_bytes = b'\x4C\x4B\x40\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x4C\x4B\x40\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x4C\x4B\x40\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x4C\x4B\x40\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x4C\x4B\x40\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x4C\x4B\x40\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x4C\x4B\x40'

    start = data.find(header_bytes, start_pos)
    start += len(header_bytes)


    
    print('start',start)


   # Find the end position of the rotation values (the next null bytes)
    termination_pattern = b'\x00' * 96  # 96 null bytes

    # Find the end position of the rotation values
    end_pos = data.find(termination_pattern, start)
    print('end_pos',end_pos)

    # If no null bytes are found after the start position, use the end of the file
    if end_pos == -1:
        end_pos = len(data)

    # Extract the rotation values between the start and end positions

    camm_data = data[start:end_pos]

    with open('camm_data.txt', 'wb') as file:
        file.write(camm_data)
   

    # Calculate the total number of rows
    total_rows = len(camm_data) // 16
    print(f"Total number of rows: {total_rows}")

    parse_camm_data(camm_data)
    

def parse_camm_data(camm_data):
    rows = [camm_data[i:i+16] for i in range(0, len(camm_data), 16)]
    values = []
    for row in rows:
        value = struct.unpack('>f', row[12:])
        values.append(value)
    return values


video_path = "R0013304_0.MP4"
# video_path = "R0013312_0.MP4"
# video_path = "R0013350_0.MP4"
# camm_data = extract_camm_track(video_path)
camm_data = extract_rotation_values(video_path)

for i, matrix in enumerate(camm_data):
    print(f"Matrix {i+1}:")
    print(matrix)
    print()
