import subprocess
import time
import os
import json
import re
import uuid
import numpy as np

import argparse

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


The following command utilizes the exiftool utility to extract embedded metadata from a specified video file. 
It provides detailed information about the operations being performed and the metadata extracted. 
The -V3 option sets the verbosity level to the highest detail, offering in-depth insights into the metadata processing. 
This level of verbosity is particularly useful for troubleshooting and comprehensive analysis of metadata within the file.

exiftool -ee -V3 /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4

exiftool -ee -V3 /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.MP4 > /Users/jordivallverdu/Documents/360code/apps/motion_theta/R0013304_0.txt

A bit of explanation on what's going on :

I want to sticth the images from the new format for the ricoh theta Z1, which allows to generate a 3648*3648 videos at 1 or 2 fps, resulting in to videos :
R0013350_0.MP4 and R0013350_1.MP4 for example, one for each lens.

Additionally there must be the IMU information somewhere, and yes it's there, the camm file format it's actually being used.

Extract and interpret the camera motion data (specifically, acceleration and angular velocity) embedded within a video file. This data, referred to as "camm" data, is stored in a binary format that required a careful approach to decode and understand. The journey involved multiple steps, which I'll outline below.

1. **Initial Data Extraction**: We first extracted the binary data corresponding to the "camm" track from the video file. This required understanding the structure of the video file and locating the appropriate bytes. We then wrote these bytes to a separate file for further analysis.

2. **Pattern Analysis**: We analyzed the binary data and identified some patterns, notably a repeating sequence of bytes at the beginning of each chunk of data. We hypothesized that these bytes could be serving as markers or identifiers for the data chunks.

3. **Data Interpretation**: Based on the identified patterns, we initially hypothesized that the data might be split into chunks of 16 bytes each, where each chunk corresponds to a single frame of the video. However, the number of chunks did not match the number of frames in the video, so we refined our hypothesis.

4. **Refining the Interpretation**: We noticed that the number of data chunks was roughly proportional to the video duration in seconds, suggesting that the camm data was sampled at a fixed frequency independent of the video frame rate. We then modified our approach to interpret the data accordingly.

5. **Data Parsing**: We wrote a Python script to parse the binary data into readable form. This involved reading the data in chunks of 16 bytes each and converting each chunk to three floating-point numbers using the struct module. 

6. **Exploring Other Tools**: We found that the ExifTool command-line utility could also extract the camm data from the video file in a readable format. We decided to use the output from ExifTool as a basis for further analysis.

7. **Refining the Parsing Script**: Based on the ExifTool output, we refined our Python script to parse the data more accurately. We now also extracted the sample time and duration for each data sample.

8. **Matching Samples to Frames**: Given the frame rate of the video, we wrote a function to associate each video frame with the closest camm data sample in time.

9. **Calculating Orientation**: Finally, we used the acceleration data to calculate the pitch and roll of the camera for each sample. We used the numpy library to perform these calculations.

Through this iterative process, we built a tool to extract, parse, and interpret the camm data embedded in a video file. The final result is a Python script that takes a video file as input and produces a JSON file containing the acceleration, angular velocity, sample time, duration, and calculated pitch and roll for each sample, as well as a unique ID for each sample. This data can then be used for further analysis or visualization.

'''


# Function to calculate pitch and roll
def calculate_pitch_roll(acceleration):
    x, y, z = acceleration
    pitch = np.arctan2(x, np.sqrt(y**2 + z**2))
    roll = np.arctan2(y, np.sqrt(x**2 + z**2))
    return np.degrees(pitch), np.degrees(roll)

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
                
                # Calculate pitch and roll
                pitch, roll = calculate_pitch_roll(values)
                current_sample['pitch'] = pitch
                current_sample['roll'] = roll

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




# Function to get frame samples
def get_frame_samples(data, frame_rate, duration):
    frame_samples = []

    total_frames = int(duration * frame_rate)

    for frame in range(total_frames):
        frame_time = frame / frame_rate
        closest_sample = min(data, key=lambda x:abs(x['sampletime']-frame_time))
        frame_samples.append(closest_sample)

    return frame_samples



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
    result = subprocess.run(['exiftool', '-VideoFrameRate', '-Duration', video_path], capture_output=True, text=True)

    lines = result.stdout.split('\n')
    
    for line in lines:
        if 'Video Frame Rate' in line:
            frame_rate = float(line.split(':')[-1].strip())
        elif 'Duration' in line:
            duration = float(line.split(':')[-1].split()[0].strip())
    

    camm_data = parse_camm_data(txt_file_path)



    return frame_rate, duration, camm_data


def animate_model(camm_data):
    import open3d as o3d

    # Prepare Open3D visualizer
    vis = o3d.visualization.Visualizer()
    vis.create_window()

    # Load the 3D model
    mesh = o3d.io.read_triangle_mesh("theta_v.stl")
    vis.add_geometry(mesh)

    # Create a line set to display the edges of the mesh
    edges = o3d.geometry.LineSet.create_from_triangle_mesh(mesh)
    edges.paint_uniform_color([0, 0, 0])  # Black edges
    vis.add_geometry(edges)

   

    # Define a function to create rotation matrix
    def create_rotation_matrix(pitch, roll):
        pitch = np.deg2rad(pitch)
        roll = np.deg2rad(roll)
        Rx = np.array([[1, 0, 0], [0, np.cos(pitch), -np.sin(pitch)], [0, np.sin(pitch), np.cos(pitch)]])
        Ry = np.array([[np.cos(roll), 0, np.sin(roll)], [0, 1, 0], [-np.sin(roll), 0, np.cos(roll)]])
        return Rx @ Ry

    # Apply rotations to the model
    for sample in camm_data:
        pitch, roll = sample['pitch'], sample['roll']
        R = create_rotation_matrix(pitch, roll)
        mesh.rotate(R, center=(0, 0, 0))  # Rotate around the origin
        edges.rotate(R, center=(0, 0, 0))  # Rotate around the origin
        vis.update_geometry(mesh)
        vis.update_geometry(edges)
        vis.poll_events()
        vis.update_renderer()
        time.sleep(0.1)  # Delay between each frame

    vis.destroy_window()


def plot_pitch_roll(camm_data):
    import matplotlib.pyplot as plt

    # Extract pitch and roll values
    pitch_values = []
    roll_values = []

    for sample in camm_data:
        pitch_values.append(sample['pitch'])
        roll_values.append(sample['roll'])

    # Plot pitch and roll values
    plt.figure(figsize=(14, 6))

    plt.subplot(1, 2, 1)
    plt.plot(pitch_values)
    plt.title('Pitch values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Pitch (degrees)')

    plt.subplot(1, 2, 2)
    plt.plot(roll_values)
    plt.title('Roll values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Roll (degrees)')

    plt.tight_layout()
    plt.show()


def plot_raw_data (camm_data):

    import matplotlib.pyplot as plt
    
    # Extract acceleration and angular velocity values
    acceleration_values = []
    angular_velocity_values = []
    # Extract pitch and roll values
    pitch_values = []
    roll_values = []


    for sample in camm_data:
        acceleration_values.append(sample['acceleration'])
        angular_velocity_values.append(sample['angularvelocity'])
        pitch_values.append(sample['pitch'])
        roll_values.append(sample['roll'])

    # Convert lists of lists into numpy arrays for easier manipulation
    acceleration_values = np.array(acceleration_values)
    angular_velocity_values = np.array(angular_velocity_values)

    # Plot acceleration, angular velocity, pitch, and roll values
    plt.figure(figsize=(18, 12))

    # Acceleration plots
    plt.subplot(3, 3, 1)
    plt.plot(acceleration_values[:, 0])
    plt.title('Acceleration X values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Acceleration (m/s^2)')

    plt.subplot(3, 3, 2)
    plt.plot(acceleration_values[:, 1])
    plt.title('Acceleration Y values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Acceleration (m/s^2)')

    plt.subplot(3, 3, 3)
    plt.plot(acceleration_values[:, 2])
    plt.title('Acceleration Z values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Acceleration (m/s^2)')

    # Angular velocity plots
    plt.subplot(3, 3, 4)
    plt.plot(angular_velocity_values[:, 0])
    plt.title('Angular Velocity X values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Angular Velocity (rad/s)')

    plt.subplot(3, 3, 5)
    plt.plot(angular_velocity_values[:, 1])
    plt.title('Angular Velocity Y values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Angular Velocity (rad/s)')

    plt.subplot(3, 3, 6)
    plt.plot(angular_velocity_values[:, 2])
    plt.title('Angular Velocity Z values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Angular Velocity (rad/s)')

    # Pitch and roll plots
    plt.subplot(3, 3, 7)
    plt.plot(pitch_values)
    plt.title('Pitch values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Pitch (degrees)')

    plt.subplot(3, 3, 8)
    plt.plot(roll_values)
    plt.title('Roll values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Roll (degrees)')

    plt.tight_layout()
    plt.show()

    return 

    # Plot acceleration and angular velocity values
    plt.figure(figsize=(14, 6))

    plt.subplot(2, 2, 1)
    plt.plot(acceleration_values[:, 0])
    plt.title('Acceleration X values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Acceleration (m/s^2)')

    plt.subplot(2, 2, 2)
    plt.plot(acceleration_values[:, 1])
    plt.title('Acceleration Y values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Acceleration (m/s^2)')

    plt.subplot(2, 2, 3)
    plt.plot(acceleration_values[:, 2])
    plt.title('Acceleration Z values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Acceleration (m/s^2)')

    plt.subplot(2, 2, 4)
    plt.plot(angular_velocity_values[:, 0], label='X')
    plt.plot(angular_velocity_values[:, 1], label='Y')
    plt.plot(angular_velocity_values[:, 2], label='Z')
    plt.title('Angular Velocity values over time')
    plt.xlabel('Time (frames)')
    plt.ylabel('Angular Velocity (rad/s)')
    plt.legend()

    plt.tight_layout()
    plt.show()



def main(videoPath, outputPath, stitch_frames, format, debug):

    frame_rate, duration, camm_data = get_video_data(videoPath)


    frame_samples = get_frame_samples(camm_data, frame_rate, duration)

    if debug :
        # animate_model(camm_data)
        # plot_pitch_roll(camm_data)
        plot_raw_data(camm_data)


    for i, sample in enumerate(frame_samples):
        print(f"Frame {i+1}:")
        print(json.dumps(sample, indent=4))
        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert camm data of a ricoh theta Z1 to a json file with')

    parser.add_argument('-v' ,'--videoPath',    default='/home/jordi/Documents/dataset/calibration_mobile/VID_20230801_130453.mp4',  type=str, help='Path to the video so that we can extract the frames')
    parser.add_argument('-o' ,'--outputPath',   default='/home/jordi/Documents/dataset/calibration_mobile/atlas1', type=str, help='Output Path folder for atlas structure')
    parser.add_argument('-s', '--stitch_frames', action='store_true', help='Set this flag to extract frames')
    parser.add_argument('-f', '--format',       type=str, default="jpg", choices=["png", "jpg", "jpeg"], help="Specify the image format for the extracted frames. Default is 'png'.")
    parser.add_argument('-d', '--debug',        action='store_true', help='Visualize the data in open3d')
    args = parser.parse_args()

    main(args.videoPath, args.outputPath, args.stitch_frames, args.format, args.debug)

