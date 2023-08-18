from dataclasses import dataclass
from matplotlib import animation
from scipy.interpolate import interp1d
import imufusion
import matplotlib.pyplot as pyplot
import numpy
import os

import argparse



def main(inputPath):

    
    # Import sensor data
    data = numpy.genfromtxt(inputPath, delimiter=",", skip_header=1)

    sample_rate = 400  # 400 Hz

    timestamp = data[:, 0]
    gyroscope = data[:, 1:4]
    accelerometer = data[:, 4:7]

    # Plot sensor data
    figure, axes = pyplot.subplots(nrows=6, sharex=True, gridspec_kw={"height_ratios": [6, 6, 6, 2, 1, 1]})

    figure.suptitle("Sensors data, Euler angles, and AHRS internal states")

    axes[0].plot(timestamp, gyroscope[:, 0], "tab:red", label="Gyroscope X")
    axes[0].plot(timestamp, gyroscope[:, 1], "tab:green", label="Gyroscope Y")
    axes[0].plot(timestamp, gyroscope[:, 2], "tab:blue", label="Gyroscope Z")
    axes[0].set_ylabel("Degrees/s")
    axes[0].grid()
    axes[0].legend()

    axes[1].plot(timestamp, accelerometer[:, 0], "tab:red", label="Accelerometer X")
    axes[1].plot(timestamp, accelerometer[:, 1], "tab:green", label="Accelerometer Y")
    axes[1].plot(timestamp, accelerometer[:, 2], "tab:blue", label="Accelerometer Z")
    axes[1].set_ylabel("g")
    axes[1].grid()
    axes[1].legend()

    # Instantiate AHRS algorithms
    offset = imufusion.Offset(sample_rate)
    ahrs = imufusion.Ahrs()

    ahrs.settings = imufusion.Settings(imufusion.CONVENTION_NWU,
                                    0.5,  # gain
                                    10,  # acceleration rejection
                                    0,  # magnetic rejection
                                    5 * sample_rate)  # rejection timeout = 5 seconds

    # Process sensor data
    delta_time = numpy.diff(timestamp, prepend=timestamp[0])

    euler = numpy.empty((len(timestamp), 3))
    internal_states = numpy.empty((len(timestamp), 3))
    acceleration = numpy.empty((len(timestamp), 3))

    for index in range(len(timestamp)):
        gyroscope[index] = offset.update(gyroscope[index])

        ahrs.update_no_magnetometer(gyroscope[index], accelerometer[index], delta_time[index])

        euler[index] = ahrs.quaternion.to_euler()

        ahrs_internal_states = ahrs.internal_states
        internal_states[index] = numpy.array([ahrs_internal_states.acceleration_error,
                                            ahrs_internal_states.accelerometer_ignored,
                                            ahrs_internal_states.acceleration_rejection_timer])

        acceleration[index] = 9.81 * ahrs.earth_acceleration  # convert g to m/s/s

    # Plot Euler angles
    axes[2].plot(timestamp, euler[:, 0], "tab:red", label="Roll")
    axes[2].plot(timestamp, euler[:, 1], "tab:green", label="Pitch")
    axes[2].plot(timestamp, euler[:, 2], "tab:blue", label="Yaw")
    axes[2].set_ylabel("Degrees")
    axes[2].grid()
    axes[2].legend()

    # Plot internal states
    axes[3].plot(timestamp, internal_states[:, 0], "tab:olive", label="Acceleration error")
    axes[3].set_ylabel("Degrees")
    axes[3].grid()
    axes[3].legend()

    axes[4].plot(timestamp, internal_states[:, 1], "tab:cyan", label="Accelerometer ignored")
    pyplot.sca(axes[4])
    pyplot.yticks([0, 1], ["False", "True"])
    axes[4].grid()
    axes[4].legend()

    axes[5].plot(timestamp, internal_states[:, 2], "tab:orange", label="Acceleration rejection timer")
    axes[5].set_xlabel("Seconds")
    axes[5].grid()
    axes[5].legend()

    # Plot acceleration
    _, axes = pyplot.subplots(nrows=4, sharex=True, gridspec_kw={"height_ratios": [6, 1, 6, 6]})

    axes[0].plot(timestamp, acceleration[:, 0], "tab:red", label="X")
    axes[0].plot(timestamp, acceleration[:, 1], "tab:green", label="Y")
    axes[0].plot(timestamp, acceleration[:, 2], "tab:blue", label="Z")
    axes[0].set_title("Acceleration")
    axes[0].set_ylabel("m/s/s")
    axes[0].grid()
    axes[0].legend()

    # Identify moving periods
    is_moving = numpy.empty(len(timestamp))

    for index in range(len(timestamp)):
        is_moving[index] = numpy.sqrt(acceleration[index].dot(acceleration[index])) > 3  # threshold = 3 m/s/s

    margin = int(0.1 * sample_rate)  # 100 ms

    for index in range(len(timestamp) - margin):
        is_moving[index] = any(is_moving[index:(index + margin)])  # add leading margin

    for index in range(len(timestamp) - 1, margin, -1):
        is_moving[index] = any(is_moving[(index - margin):index])  # add trailing margin

    # Plot moving periods
    axes[1].plot(timestamp, is_moving, "tab:cyan", label="Is moving")
    pyplot.sca(axes[1])
    pyplot.yticks([0, 1], ["False", "True"])
    axes[1].grid()
    axes[1].legend()

    # Calculate velocity (includes integral drift)
    velocity = numpy.zeros((len(timestamp), 3))

    for index in range(len(timestamp)):
        if is_moving[index]:  # only integrate if moving
            velocity[index] = velocity[index - 1] + delta_time[index] * acceleration[index]

    # Find start and stop indices of each moving period
    is_moving_diff = numpy.diff(is_moving, append=is_moving[-1])


    @dataclass
    class IsMovingPeriod:
        start_index: int = -1
        stop_index: int = -1


    is_moving_periods = []
    is_moving_period = IsMovingPeriod()

    for index in range(len(timestamp)):
        if is_moving_period.start_index == -1:
            if is_moving_diff[index] == 1:
                is_moving_period.start_index = index

        elif is_moving_period.stop_index == -1:
            if is_moving_diff[index] == -1:
                is_moving_period.stop_index = index
                is_moving_periods.append(is_moving_period)
                is_moving_period = IsMovingPeriod()

    # Remove integral drift from velocity
    velocity_drift = numpy.zeros((len(timestamp), 3))

    for is_moving_period in is_moving_periods:
        start_index = is_moving_period.start_index
        stop_index = is_moving_period.stop_index

        t = [timestamp[start_index], timestamp[stop_index]]
        x = [velocity[start_index, 0], velocity[stop_index, 0]]
        y = [velocity[start_index, 1], velocity[stop_index, 1]]
        z = [velocity[start_index, 2], velocity[stop_index, 2]]

        t_new = timestamp[start_index:(stop_index + 1)]

        velocity_drift[start_index:(stop_index + 1), 0] = interp1d(t, x)(t_new)
        velocity_drift[start_index:(stop_index + 1), 1] = interp1d(t, y)(t_new)
        velocity_drift[start_index:(stop_index + 1), 2] = interp1d(t, z)(t_new)

    velocity = velocity - velocity_drift

    # Plot velocity
    axes[2].plot(timestamp, velocity[:, 0], "tab:red", label="X")
    axes[2].plot(timestamp, velocity[:, 1], "tab:green", label="Y")
    axes[2].plot(timestamp, velocity[:, 2], "tab:blue", label="Z")
    axes[2].set_title("Velocity")
    axes[2].set_ylabel("m/s")
    axes[2].grid()
    axes[2].legend()

    # Calculate position
    position = numpy.zeros((len(timestamp), 3))

    for index in range(len(timestamp)):
        position[index] = position[index - 1] + delta_time[index] * velocity[index]

    # Plot position
    axes[3].plot(timestamp, position[:, 0], "tab:red", label="X")
    axes[3].plot(timestamp, position[:, 1], "tab:green", label="Y")
    axes[3].plot(timestamp, position[:, 2], "tab:blue", label="Z")
    axes[3].set_title("Position")
    axes[3].set_xlabel("Seconds")
    axes[3].set_ylabel("m")
    axes[3].grid()
    axes[3].legend()

    # Print error as distance between start and final positions
    print("Error: " + "{:.3f}".format(numpy.sqrt(position[-1].dot(position[-1]))) + " m")

    # Create 3D animation (takes a long time, set to False to skip)
    if True:
        figure = pyplot.figure(figsize=(10, 10))

        axes = pyplot.axes(projection="3d")
        axes.set_xlabel("m")
        axes.set_ylabel("m")
        axes.set_zlabel("m")

        x = []
        y = []
        z = []

        scatter = axes.scatter(x, y, z)

        fps = 30
        samples_per_frame = int(sample_rate / fps)

        def update(frame):
            index = frame * samples_per_frame

            axes.set_title("{:.3f}".format(timestamp[index]) + " s")

            x.append(position[index, 0])
            y.append(position[index, 1])
            z.append(position[index, 2])

            scatter._offsets3d = (x, y, z)

            if (min(x) != max(x)) and (min(y) != max(y)) and (min(z) != max(z)):
                axes.set_xlim3d(min(x), max(x))
                axes.set_ylim3d(min(y), max(y))
                axes.set_zlim3d(min(z), max(z))

                axes.set_box_aspect((numpy.ptp(x), numpy.ptp(y), numpy.ptp(z)))

            return scatter
        
        # Get the file name without extension
        file_name_without_extension = os.path.splitext(os.path.basename(inputPath))[0]

        # Get the directory of the video file and create the .txt file path
        directory = os.path.dirname(inputPath)

        anim_file_path = os.path.join(directory, f"{file_name_without_extension}_anim.gif")

        anim = animation.FuncAnimation(figure, update,
                                    frames=int(len(timestamp) / samples_per_frame),
                                    interval=1000 / fps,
                                    repeat=False)

        anim.save(anim_file_path, writer=animation.PillowWriter(fps))

    pyplot.show()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert camm data of a ricoh theta Z1 to a json file with')

    parser.add_argument('-i' ,'--inputPath',    default='/home/jordi/Documents/dataset/calibration_mobile/VID_20230801_130453.mp4',  type=str, help='Path to the video so that we can extract the frames')
    parser.add_argument('-o' ,'--outputPath',   default='/home/jordi/Documents/dataset/calibration_mobile/atlas1', type=str, help='Output Path folder for atlas structure')
    parser.add_argument('-s', '--stitch_frames', action='store_true', help='Set this flag to extract frames')
    parser.add_argument('-f', '--format',       type=str, default="jpg", choices=["png", "jpg", "jpeg"], help="Specify the image format for the extracted frames. Default is 'png'.")
    parser.add_argument('-d', '--debug',        action='store_true', help='Visualize the data in open3d')
    parser.add_argument('-c', '--csv',          action='store_true', help='create csv file with the camm data')
    args = parser.parse_args()

    main(args.inputPath)


