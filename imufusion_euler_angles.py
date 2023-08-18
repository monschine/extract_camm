'''

https://github.com/xioTechnologies/Fusion/tree/main

Fusion is a sensor fusion library for Inertial Measurement Units (IMUs), optimised for embedded systems. Fusion is a C library but is also available as the Python package, imufusion. 
Two example Python scripts, simple_example.py and advanced_example.py are provided with example sensor data to demonstrate use of the package.


you can easilly install imufusion :

pip install imufusion==1.1.2

'''

import imufusion
import matplotlib.pyplot as pyplot
import numpy
import sys
import os



import argparse



def main(inputPath, save):

    # Import sensor data
    data = numpy.genfromtxt(inputPath, delimiter=",", skip_header=1)

    timestamp = data[:, 0]
    gyroscope = data[:, 1:4]
    accelerometer = data[:, 4:7]

    # Plot sensor data
    _, axes = pyplot.subplots(nrows=3, sharex=True)

    axes[0].plot(timestamp, gyroscope[:, 0], "tab:red", label="X")
    axes[0].plot(timestamp, gyroscope[:, 1], "tab:green", label="Y")
    axes[0].plot(timestamp, gyroscope[:, 2], "tab:blue", label="Z")
    axes[0].set_title("Gyroscope")
    axes[0].set_ylabel("Degrees/s")
    axes[0].grid()
    axes[0].legend()

    axes[1].plot(timestamp, accelerometer[:, 0], "tab:red", label="X")
    axes[1].plot(timestamp, accelerometer[:, 1], "tab:green", label="Y")
    axes[1].plot(timestamp, accelerometer[:, 2], "tab:blue", label="Z")
    axes[1].set_title("Accelerometer")
    axes[1].set_ylabel("g")
    axes[1].grid()
    axes[1].legend()

    # Process sensor data
    ahrs = imufusion.Ahrs()
    euler = numpy.empty((len(timestamp), 3))

    for index in range(len(timestamp)):
        ahrs.update_no_magnetometer(gyroscope[index], accelerometer[index], 1 / 100)  # 100 Hz sample rate
        euler[index] = ahrs.quaternion.to_euler()

    # Plot Euler angles
    axes[2].plot(timestamp, euler[:, 0], "tab:red", label="Roll")
    axes[2].plot(timestamp, euler[:, 1], "tab:green", label="Pitch")
    axes[2].plot(timestamp, euler[:, 2], "tab:blue", label="Yaw")
    axes[2].set_title("Euler angles")
    axes[2].set_xlabel("Seconds")
    axes[2].set_ylabel("Degrees")
    axes[2].grid()
    axes[2].legend()

    if save :
        # Get the file name without extension
        file_name_without_extension = os.path.splitext(os.path.basename(inputPath))[0]

        # Get the directory of the video file and create the .txt file path
        directory = os.path.dirname(inputPath)

        pyplot.savefig(os.path.join(directory, f"{file_name_without_extension}_plot.png"))
    
    else :
        pyplot.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='perform sensor fusion on ricoh theta IMU data')

    parser.add_argument('-i' ,'--inputPath',    default='./video_samples/R0013405_1.csv',  type=str, help='Path to the IMU data in csv format')
    parser.add_argument('-s', '--save',         action='store_true', help='save the plot')

    args = parser.parse_args()

    main(args.inputPath, args.save)