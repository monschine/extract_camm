from pymp4.parser import Box
from construct.core import RangeError
import numpy as np
import os
import struct

'''
The post that gives me more clues

https://community.theta360.guide/t/theta-z1-gps-track-in-video-files/7101/2

exiftool -a -G1 -n -handlertype /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4 
[Track1]        Handler Type                    : vide
[Track2]        Handler Type                    : camm
[Track2]        Handler Type                    : url
[QuickTime]     Handler Type                    : mdta

https://github.com/trek-view/360-camera-metadata/blob/master/0-standards/camm.md
https://developers.google.com/streetview/publish/camm-spec?hl=es-419#data-format
https://exiftool.org/forum/index.php?topic=5095.45


exiftool -ee -V3 /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4

exiftool -ee -V3 /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4 > /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.txt

'''

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

    rm = parse_camm_data(camm_data)
    return rm

    # Parse the rotation values, skipping the metadata bytes
    rotation_values = []
    for i in range(total_rows):
        row_data = camm_data[i*16:(i+1)*16]
        rotation_values.extend(np.frombuffer(row_data[8:], dtype=np.float32))

    rotation_values = np.array(rotation_values)
    print(f"Total number of rotation values: {len(rotation_values)}")

    # Reshape the array into samples of 3x3 matrices
    rotation_matrices = rotation_values.reshape((-1, 3, 3))

    return 

    with open('camm_data.txt', 'wb') as file:
        file.write(camm_data)

    rotation_values = np.frombuffer(camm_data, dtype=np.float32)
    print(f"Total number of rotation values: {len(rotation_values)}")

    # Reshape the array into samples of 3x3 matrices
    rotation_matrices = rotation_values.reshape((-1, 3, 3))

    return
    
    # Parse the rotation values
    rotation_matrices = parse_camm_data(camm_data)

    return rotation_matrices

def parse_camm_data(camm_data):
    rows = [camm_data[i:i+16] for i in range(0, len(camm_data), 16)]
    values = []
    for row in rows:
        value = struct.unpack('>f', row[12:])
        values.append(value)
    return values


def parse_camm_data_save(binary_data):
    # Check that the length of the data is a multiple of 36
    # assert len(binary_data) % 36 == 0, "Invalid data length"

    # Calculate the number of samples
    # num_samples = len(binary_data) // 36

    # Open a file in write mode and save the string
    with open('raw_rotations.txt', 'wb') as file:
        file.write(binary_data)

    # Convert the bytes into a numpy array of floats
    # data_floats = np.frombuffer(binary_data, dtype=np.float32)
    # print(data_floats)
    # np.savetxt('numpy_array_32.txt', data_floats, delimiter=',')
    # Reshape the array into samples
    # samples = data_floats.reshape((num_samples, 3, 3))

    # return samples




def parse_camm_data_(data):
    # Number of bytes in each chunk
    chunk_size = 16

    # Number of bytes in each float32 value
    float_size = 4

    # Number of chunks in the data
    num_chunks = len(data) // chunk_size

    print('num_chunks',num_chunks)

    # Initialize an array to store the rotation values
    rotations = np.empty((num_chunks, 3), dtype=np.float32)

    # Iterate over each chunk
    for i in range(num_chunks):
        for j in range(3):
            # Get the start and end indices of the float32 value in the chunk
            start = i * chunk_size + j * float_size
            end = start + float_size - 1  # subtract 1 to ignore the last byte

            # Extract the 3 bytes and append a zero byte
            three_bytes = data[start:end]
            four_bytes = three_bytes + b'\x00'

            # Interpret the four bytes as a float32 value and store it in the array
            rotations[i, j] = np.frombuffer(four_bytes, dtype=np.float32)[0]

    # Reshape the array into samples of 3x3 matrices
    rotation_matrices = rotations.reshape(-1, 3, 3)

    return rotation_matrices


video_path = "R0013304_0.MP4"
# video_path = "R0013312_0.MP4"
# video_path = "R0013350_0.MP4"
# camm_data = extract_camm_track(video_path)
camm_data = extract_rotation_values(video_path)

for i, matrix in enumerate(camm_data):
    print(f"Matrix {i+1}:")
    print(matrix)
    print()
