
import numpy as np
import json
from scipy.integrate import cumtrapz
import matplotlib.pyplot as plt
import os

import argparse


class KalmanFilter:
    def __init__(self, process_variance, measurement_variance, estimate):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimate = estimate
        self.estimate_error = 1

    def update(self, measurement):
        # Prediction
        prediction = self.estimate
        prediction_error = self.estimate_error + self.process_variance

        # Update
        kalman_gain = prediction_error / (prediction_error + self.measurement_variance)
        self.estimate = prediction + kalman_gain * (measurement - prediction)
        self.estimate_error = (1 - kalman_gain) * prediction_error

        return self.estimate

def sensor_fusion(angular_velocity, acceleration, time):
    kf_angular_velocity = KalmanFilter(process_variance=0.001, measurement_variance=0.1, estimate=angular_velocity[0])
    kf_acceleration = KalmanFilter(process_variance=0.001, measurement_variance=0.1, estimate=acceleration[0])

    # Fusion
    fused_angular_velocity = []
    fused_acceleration = []
    for i in range(len(time)):
        fused_angular_velocity.append(kf_angular_velocity.update(angular_velocity[i]))
        fused_acceleration.append(kf_acceleration.update(acceleration[i]))

    return np.array(fused_angular_velocity), np.array(fused_acceleration)

def integrate_trajectory_dx(angular_velocity, acceleration, dx):
    orientation = cumtrapz(angular_velocity, dx=dx, initial=0)
    velocity = cumtrapz(acceleration, dx=dx, initial=0)
    position = cumtrapz(velocity, dx=dx, initial=0)
    return position


def main(inputPath, save):

    # Load and process data
    with open(inputPath, 'r') as f:
        data = json.load(f)

    angular_velocity_data = np.array([sample['angularvelocity'] for sample in data])
    acceleration_data = np.array([sample['acceleration'] for sample in data])
    time_data = np.array([sample['sampletime'] for sample in data])

    dx = data[0]['sampleduration']
    fused_angular_velocity, fused_acceleration = sensor_fusion(angular_velocity_data, acceleration_data, time_data)
    trajectory_scaled = integrate_trajectory_dx(fused_angular_velocity, fused_acceleration, dx)

    # Visualization
    fig_scaled = plt.figure(figsize=(10, 8))
    ax_scaled = fig_scaled.add_subplot(111, projection='3d')
    ax_scaled.plot(trajectory_scaled[:, 0], trajectory_scaled[:, 1], trajectory_scaled[:, 2], 
                label='Scaled Estimated Trajectory', color='blue')
    ax_scaled.set_xlabel('X (meters)')
    ax_scaled.set_ylabel('Y (meters)')
    ax_scaled.set_zlabel('Z (meters)')
    ax_scaled.set_title('3D Scaled Trajectory Estimation')
    ax_scaled.legend()

    if save :
        # Get the file name without extension
        file_name_without_extension = os.path.splitext(os.path.basename(inputPath))[0]

        # Get the directory of the video file and create the .txt file path
        directory = os.path.dirname(inputPath)

        plt.savefig(os.path.join(directory, f"{file_name_without_extension}_plot.png"))
    
    else :
        plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='perform sensor fusion on ricoh theta IMU data')

    parser.add_argument('-i' ,'--inputPath',    default='./video_samples/R0013405_1.json',  type=str, help='Path to the IMU data in json format')
    parser.add_argument('-s', '--save',         action='store_true', help='save the plot')

    args = parser.parse_args()

    main(args.inputPath, args.save)