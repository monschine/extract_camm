
# 3D Trajectory Estimation from IMU Data

This code provides a method to estimate a 3D trajectory based on Inertial Measurement Unit (IMU) data. The IMU data includes angular velocity (from a gyroscope) and linear acceleration (from an accelerometer).

## Overview

1. **Kalman Filter**: A basic Kalman filter is used to fuse the angular velocity and acceleration data. This helps in reducing noise and getting a smoother estimate of the IMU data.
2. **Sensor Fusion**: The fused angular velocity and acceleration data are integrated over time to estimate the relative position or trajectory of the IMU sensor in 3D space.
3. **Visualization**: The estimated 3D trajectory is visualized using matplotlib.

## How to Use

1. Load the IMU data from a JSON file. The expected keys in the JSON file are 'angularvelocity', 'acceleration', and 'sampletime'.
2. The Kalman filter is applied to both the angular velocity and acceleration data to get the fused estimates.
3. The fused data is then integrated to get the estimated 3D trajectory.
4. Finally, the 3D trajectory is visualized.

## Assumptions

- The IMU and camera coordinate systems are aligned.
- The angular velocity is provided in radians/second.
- The acceleration data is in meters/second^2.
- The sample duration (time between samples) is consistent across all samples.

## Note

This is a basic demonstration of trajectory estimation using IMU data. In real-world scenarios, the accuracy of the estimated trajectory can be affected by various factors, including sensor noise, drift, biases, and external disturbances. More advanced methods, such as Extended Kalman Filters, Particle Filters, or other sensor fusion techniques, may be required for high-precision applications.

