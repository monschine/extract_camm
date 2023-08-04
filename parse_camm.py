import subprocess
import os
import json
import re
import uuid
import numpy as np

'''
The post that gives me more clues

https://community.theta360.guide/t/theta-z1-gps-track-in-video-files/7101/2

exiftool -a -G1 -n -handlertype /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4 
[Track1]        Handler Type                    : vide
[Track2]        Handler Type                    : camm
[Track2]        Handler Type                    : url
[QuickTime]     Handler Type                    : mdta

https://github.com/trek-view/360-camerta-metadata/blob/master/0-standards/camm.md
https://developers.google.com/streetview/publish/camm-spec?hl=es-419#data-format
https://exiftool.org/forum/index.php?topic=5095.45


exiftool -ee -V3 /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4

exiftool -ee -V3 /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4 > /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.txt

A bit of explanation on what's going on :

I want to sticth the images from the new format for the ricoh theta Z1, which allows to generate a 3648*3648 videos at 1 or 2 fps, resulting in to videos :
R0013350_0.MP4 and R0013350_1.MP4 for example, one fro each lens.

Additionally there must be the IMU information somewhere, and yes it's there, the camm file format

'''

def parse_camm_data(filePath):

    with open(filePath, 'r') as f:
        lines = f.readlines()

    data = []
    current_sample = {}
    sample_time = None
    sample_duration = None

    for line in lines:
        if 'SampleTime' in line:
            sample_time = float(re.findall("\d+\.?\d*", line)[0])
        elif 'SampleDuration' in line:
            sample_duration = float(re.findall("\d+\.?\d*", line)[0])
        elif 'AngularVelocity' in line or 'Acceleration' in line:
            identifier, values = line.strip().split(' = ')
            # Remove "|" character and make the identifier lowercase
            identifier = identifier.replace("| ", "").lower()
            values = list(map(float, values.split(' ')))
            current_sample[identifier] = values
            if 'acceleration' in identifier:
                # Once we have both AngularVelocity and Acceleration, consider the sample complete
                current_sample['uuid'] = str(uuid.uuid4())
                current_sample['sampletime'] = sample_time
                current_sample['sampleduration'] = sample_duration
                data.append(current_sample)
                current_sample = {}

    
    # Get the file name without extension
    file_name_without_extension = os.path.splitext(os.path.basename(filePath))[0]

    # Get the directory of the video file and create the .txt file path
    directory = os.path.dirname(filePath)

    # Convert to JSON-like format
    data_json = json.dumps(data, indent=4)

    # Specify the file path where you want to save the JSON data
    file_path = os.path.join(directory, f"{file_name_without_extension}.json")

    # Open the file for writing and write the JSON data
    with open(file_path, "w") as json_file:
        json_file.write(data_json)

    return data




def get_frame_samples(data, frame_rate):
    frame_samples = []

    total_frames = int(data[-1]['sampletime'] * frame_rate) + 1

    for frame in range(total_frames):
        frame_time = frame / frame_rate
        closest_sample = min(data, key=lambda x:abs(x['sampletime']-frame_time))
        frame_samples.append(closest_sample)

    return frame_samples

# Function to calculate pitch and roll
def calculate_pitch_roll(acceleration):
    x, y, z = acceleration
    pitch = np.arctan2(x, np.sqrt(y**2 + z**2))
    roll = np.arctan2(y, np.sqrt(x**2 + z**2))
    return np.degrees(pitch), np.degrees(roll)

def get_video_data(video_path):

    # Get the file name without extension
    file_name_without_extension = os.path.splitext(os.path.basename(video_path))[0]

    # Get the directory of the video file and create the .txt file path
    directory = os.path.dirname(video_path)

    txt_file_path = os.path.join(directory, f"{file_name_without_extension}.txt")

    # Run exiftool to generate the .txt file
    with open(txt_file_path, 'w') as f:
        subprocess.run(['exiftool', '-ee', '-V3', video_path, '>', txt_file_path], stdout=f)

    # Get the frame rate
    result = subprocess.run(['exiftool', '-VideoFrameRate', video_path], capture_output=True, text=True)
    frame_rate_line = result.stdout
    frame_rate = float(frame_rate_line.split(':')[-1].strip())

    return frame_rate, txt_file_path



video_path = "/Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4"
frame_rate, txt_file_path = get_video_data(video_path)

camm_data = parse_camm_data(txt_file_path)

frame_samples = get_frame_samples(camm_data, frame_rate)

# for i, sample in enumerate(frame_samples):
#     print(f"Frame {i+1}:")
#     print(sample)
#     print()


