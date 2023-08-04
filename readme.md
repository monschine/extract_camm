# Camera Motion Metadata Specification (CAMM) - Readme

## Introduction

The Camera Motion Metadata (CAMM) specification allows MP4 files to embed metadata about camera motion during video capture. This metadata is collected from sensors present in devices that capture videos, such as gyroscope, accelerometer, magnetometer, GPS, and more. CAMM provides information about camera orientation, exposure, gyroscope readings, accelerometer readings, 3D position, GPS coordinates, ambient magnetic field, and more.

This readme file provides a detailed description of the CAMM specification, its data formats, and potential issues to consider when implementing this standard.

## Supported API

CAMM is supported in the Street View Publish API.

## Usage and Applications

The metadata embedded using CAMM can be utilized for advanced post-processing in various applications. Some of the use cases include:

1. **Video Stabilization:** Frame-level rotation information can be used to stabilize videos, reducing shakiness and improving video quality.

2. **Rolling Shutter Effect Reduction:** Scanline-level motion data can be used to mitigate rolling shutter effects, which often occur in fast-moving scenes.

3. **Time and Geometric Alignment:** IMU readings and derived 3DoF poses can be used to evaluate time and geometric alignment between IMU (Inertial Measurement Unit) and the camera.

4. **Per-Scanline Metadata Interpolation:** Exposure information can be used to interpolate per-scanline motion metadata, improving accuracy in capturing motion details.

## Specification Details

### Case 0: Angle Axis Orientation

The angle axis orientation is a representation of the rotation from the local camera coordinates to a world coordinate system. The world coordinate system is defined by the applications using the camera motion metadata. This rotation information is essential for understanding how the camera is oriented with respect to the global reference frame.

To represent the rotation, we use a 3-dimensional vector called the "angle-axis vector." Let's denote this vector as `angle_axis`, where `angle_axis[0]`, `angle_axis[1]`, and `angle_axis[2]` are the components of the vector. The length of the `angle_axis` vector represents the rotation angle in radians, and the direction of the vector represents the axis of rotation.

#### Rotation Matrix (M) and Ray Transformation

To apply the rotation to a ray (a vector representing the direction of a point in 3D space) in the local coordinate system, we use a 3x3 rotation matrix, denoted as "M," that corresponds to the angle-axis vector.

For any ray `X` in the local coordinate system, the transformed ray direction in the world coordinate system (X') is obtained by multiplying `X` with the rotation matrix `M`: `X' = M * X`.

This allows us to understand how the camera's view direction is transformed in the world coordinate system after applying the rotation.

#### Obtaining Angle Axis Information

The angle-axis vector can be obtained by running 3DoF (Three Degrees of Freedom) sensor fusion on the device. 3DoF sensor fusion combines data from the device's sensors, such as the gyroscope, accelerometer, and magnetometer, to estimate the device's orientation in 3D space.

After the sensor fusion process, the integrated global orientation, represented by the angle-axis vector, needs to be recorded as part of the camera motion metadata.

#### Encoded Representation

The angle-axis vector, represented by the `angle_axis` array, can be encoded into a single value that combines the axis and angle information. The encoded representation is calculated using the following formula:

```c
angle_axis := angle_radians * normalized_axis_vec3
```

Here, `angle_radians` is the rotation angle in radians (the length of the `angle_axis` vector), and `normalized_axis_vec3` is the normalized vector representing the axis of rotation.

#### Decoding the Encoded Representation

To transform the encoded representation back into an axis and angle, we use the following formulas:

```c
axis := normalize(angle_axis)
angle_radians := length(angle_axis)
```

Here, `axis` is the normalized vector representing the axis of rotation, and `angle_radians` is the rotation angle in radians.

#### Positive Angle Representation

In the encoded representation, a positive angle represents a counterclockwise rotation around the axis. This convention is commonly used in 3D graphics and computer vision to define rotations.

By utilizing the angle-axis orientation, applications can understand and interpret the camera's orientation with respect to the world coordinate system. This information is valuable for various post-processing tasks, such as stabilizing videos or aligning camera motion with other data sources.

### Case 1: Pixel Exposure Time and Rolling Shutter Skew Time

This metadata case provides exposure information per video frame, specifically pixel exposure time and rolling shutter skew time. The PTS (Presentation Time Stamp) of this metadata should be the start of the exposure of the first-used scanline in a video frame.

#### Pixel Exposure Time

The `pixel_exposure_time` metadata represents the exposure time for a single pixel in nanoseconds. It defines how long each pixel in the video frame is exposed to light during the capture process.

#### Rolling Shutter Skew Time

The `rolling_shutter_skew_time` metadata represents the delay between the exposure of the first-used scanline and the last-used scanline in nanoseconds. It accounts for the rolling shutter effect, which causes distortion in fast-moving scenes.

The combined information of pixel exposure time and rolling shutter skew time can be used to interpolate per-scanline metadata and improve the accuracy of post-processing tasks.

### Case 2: Gyroscope Readings

This metadata case provides gyroscope signal readings in radians per second around the XYZ axes of the camera. The rotation is positive in the counterclockwise direction.

#### Usage and Alignment

Applications define the relationship between the IMU coordinate system and the camera coordinate system. To ensure consistent interpretation of gyroscope readings, it is recommended to align the IMU coordinate system with the camera coordinate system.

Note that initial gyro readings are typically in the IMU coordinate system defined by its driver, and proper transformation is required to convert it to the camera coordinate system.

### Case 3: Accelerometer Readings

This metadata case provides accelerometer readings in meters per second squared (m/s^2) along the XYZ axes of the camera.

#### Usage and Alignment

Similar to gyroscope readings, applications define the relationship between the IMU coordinate system and the camera coordinate system. Aligning the two coordinate systems is recommended for accurate interpretation of accelerometer readings.

### Case 4: 3D Position of the Camera

This metadata case provides the 3D position of the camera, which, together with the angle-axis rotation, defines the 6DoF (Six Degrees of Freedom) pose of the camera. These values are in a common application-defined coordinate system.

#### Obtaining 3D Position

The 3D position of the camera can be obtained by running 6DoF tracking on the device. 6DoF tracking combines data from various sensors to estimate the position and orientation of the camera in 3D space.

### Case 5: GPS Coordinates (Minimal)

This metadata case provides minimal GPS coordinates of the sample, including latitude, longitude, and altitude.

#### Note on GPS Samples

The GPS samples must be raw values and not interpolated or repeated when there is

 no change. This ensures that the GPS coordinates accurately represent the device's location during video capture.

### Case 6: GPS Metadata

This metadata case provides comprehensive GPS information, including time, fix type, latitude, longitude, altitude, and accuracy.

#### GPS Time and Fix Type

The `time_gps_epoch` represents the time since the GPS epoch when the GPS measurement was taken. The `gps_fix_type` indicates the quality of the GPS fix, where 0 represents no fix, 2 represents a 2D fix, and 3 represents a 3D fix.

#### GPS Coordinates and Accuracy

The `latitude` and `longitude` represent the GPS coordinates in degrees. The `altitude` is the height above the WGS-84 ellipsoid. The `horizontal_accuracy` and `vertical_accuracy` represent the accuracy of the latitude/longitude and altitude measurements, respectively.

#### GPS Velocity

The metadata also includes velocity information, represented by `velocity_east`, `velocity_north`, and `velocity_up`, which represent the velocity components in meters per second in the east, north, and up directions, respectively. The `speed_accuracy` provides the accuracy of the velocity measurements.

### Case 7: Ambient Magnetic Field

This metadata case provides information about the ambient magnetic field in microtesla.

#### Usage and Reference

Applications can use this data to understand the magnetic environment in which the video was captured. It is often used in conjunction with other sensor data to analyze the device's orientation and position.

Refer to the Android Sensor.TYPE_MAGNETIC_FIELD for more information on the sensor used to measure the ambient magnetic field.

## Additional Notes

- There should be only one CAMM track per MP4 file, which contains all the above data types by muxing them together.
- The coordinate systems are right-handed. The camera coordinate system is defined as X pointing right, Y pointing downward, and Z pointing forward. The Y-axis of the global coordinate system should point down along the gravity vector.
- IMU readings are typically in a separate IMU coordinate system, and rotation is needed to map them to the camera coordinate system if the two systems differ.
- All fields are in little-endian format, and the 32-bit floating points are in IEEE 754-1985 format.
- To accurately synchronize the video frame and the metadata, the PTS of the video frame should be at the center of its exposure.
- The application muxing this data should choose a large enough time scale to get an accurate PTS.

## Potential Issues

- Writing very high-frequency packets may increase I/O pressure and header size, particularly for embedded devices.
- Mixing different types of data with different delays can cause the PTS to go both forward and backward. Buffering packets and writing them in monotonic order can overcome this issue.

## Conclusion

The Camera Motion Metadata Specification (CAMM) allows for the embedding of camera motion metadata in MP4 files, enabling advanced post-processing and analysis in various applications. By providing detailed information about camera orientation, exposure, gyroscope readings, GPS coordinates, and more, CAMM enhances video stabilization, reduces rolling shutter effects, and improves the accuracy of time and geometric alignment. Implementers should consider potential issues related to packet frequency and data mixing while using this specification.

For further details and implementation guidance, refer to the CAMM Sample Entry and Data Format sections above.

---