Camera Motion Metadata Spec

bookmark_border
This standard is supported in the Street View Publish API.
This page describes a specification that allows MP4 files to embed metadata about camera motion during video capture. Devices that capture video typically have sensors that can provide additional information about capture. For example:

Mobile phones typically have sensors for gyroscope, accelerometer, magnetometer, and GPS.
Sensor fusion can be used to track the 3 degrees of freedom (3DoF) pose of devices.
Simultaneous localization and mapping (SLAM) can be used to track the 6 degrees of freedom (6DoF) pose of the device (for example, Tango).
Exposure information can be used to interpolate per-scanline motion.
This metadata can be saved in the video for advanced post-processing in various applications. For example:

Frame-level rotation information can be used to stabilize videos, and scanline-level motion data can be used to reduce rolling shutter effects.
IMU readings and derived 3DoF poses can be used to evaluate time alignment and geometric alignment between IMU and the camera.
The sections below specify the CAmera Motion Metadata (CAMM) track, which includes a new sample entry that indicates the existence of the track and the data format of track samples.

Sample entry
The video file should contain the following sample entry box to indicate the custom metadata track, and the subComponentType of the track should be set to meta.


Camera Motion Metadata Sample Entry (camm)

Definition
Box Type: camm
Container: stsd
A sample entry indicating the data track that saves the camera motion.

Syntax
aligned(8) class CameraMotionMetadataSampleEntry extends SampleEntry('camm') {
}
  
Data format
The metadata track contains a stream of metadata samples that are formatted as follows.

Field	Unit	Description

uint16 reserved;
Reserved. Should be 0.

uint16 type;
The type of the data packet (see below). Each packet has one type of data.

switch (type) {

  case 0:
    float angle_axis[3];
  break;
          
Angle axis orientation in radians representing the rotation from local camera coordinates to a world coordinate system. The world coordinate system is defined by applications.

Let M be the 3x3 rotation matrix corresponding to the angle axis vector. For any ray X in the local coordinate system, the ray direction in the world coordinate is M * X.

This information can be obtained by running 3DoF sensor fusion on the device. After integrating the IMU readings, only the integrated global orientation needs to be recorded.

The three values represent the angle-axis vector, such that the rotation angle in radians is given by the length of the vector, and the rotation axis is given by the normalized vector.

The encoded representation can be created from an axis and angle with float[3] angle_axis := angle_radians * normalized_axis_vec3. A positive angle represents a counterclockwise rotation around the axis.

And the encoded representation can be transformed back to an axis and angle with float[3] axis := normalize(axis_angle) and float angle_radians := length(angle_axis).


  case 1:
    int32 pixel_exposure_time;
    int32 rolling_shutter_skew_time;
  break;
          
nanoseconds	
This metadata is per video frame. The presentation time (PTS) of this metadata should be the start of the exposure of the first-used scanline in a video frame.

pixel_exposure_time_ns is the exposure time for a single pixel in nanoseconds and rolling_shutter_skew_time_ns is the delay between the exposure of the first-used scanline and the last-used scanline. They can be used to interpolate per-scanline metadata.

The PTS of the corresponding frame should be within pts_of_this_metadata and pts_of_this_metadata + pixel_exposure_time_ns + rolling_shutter_skew_time_ns.

When this information is not saved, the device should make a best-effort attempt to adjust the PTS of the video frame to be at the center of the frame exposure.


  case 2:
    float gyro[3];
  break;
          
radians/seconds	
Gyroscope signal in radians/seconds around XYZ axes of the camera. Rotation is positive in the counterclockwise direction.

Applications define the relationship between the IMU coordinate system and the camera coordinate system. We recommend aligning them if possible.

Note that initial gyro readings are in the IMU coordinate system defined by its driver, and proper transformation is required to convert it to the camera coordinate system.

Refer to Android Sensor.TYPE_GYROSCOPE.


  case 3:
    float acceleration[3];
  break;
          
meters/seconds^2	
Accelerometer reading in meters/second^2 along XYZ axes of the camera.

Applications define the relationship between the IMU coordinate system and the camera coordinate system. We recommend aligning them if possible.

Refer to Android Sensor.TYPE_ACCELEROMETER.


  case 4:
    float position[3];
  break;
          
3D position of the camera. 3D position and angle axis rotation together defines the 6DoF pose of the camera, and they are in a common application-defined coordinate system.

You can get this information by running 6DoF tracking on the device.


  case 5:
    double latitude;
    double longitude;
    double altitude;
  break;
          
degrees	
Minimal GPS coordinate of the sample.

Note: The GPS samples must be raw values, and not interpolated or repeated when there is no change.

  case 6:
    double time_gps_epoch;
    int gps_fix_type;
    double latitude;
    double longitude;
    float altitude;
    float horizontal_accuracy;
    float vertical_accuracy;
    float velocity_east;
    float velocity_north;
    float velocity_up;
    float speed_accuracy;
  break;
          


seconds

degrees
degrees
meters
meters
meters
meters/seconds
meters/seconds
meters/seconds
meters/seconds
          
time_gps_epoch - Time since the GPS epoch when the measurement was taken

gps_fix_type - 0 ( no fix), 2 (2D fix), 3 (3D fix)

latitude - Latitude in degrees

longitude - Longitude in degrees

altitude - Height above the WGS-84 ellipsoid

horizontal_accuracy - Horizontal (lat/long) accuracy

vertical_accuracy - Vertical (altitude) accuracy

velocity_east - Velocity in the east direction

velocity_north - Velocity in the north direction

velocity_up - Velocity in the up direction

speed_accuracy - Speed accuracy

Note: The GPS samples must be raw values, and not interpolated or repeated when there is no change.

  case 7:
    float magnetic_field[3];
  break;
          
microtesla	
Ambient magnetic field.

Refer to Android Sensor.TYPE_MAGNETIC_FIELD.

}		
Notes
There should be only one CAMM track per MP4 file, which contains all of the above data types by muxing them together.
GPS samples in cases 5 and 6 must be raw values generated by sensors. They can not be interpolated or repeated when there is no GPS change.
The coordinate systems are right-hand sided. The camera coordinate system is defined as X pointing right, Y pointing downward, and Z pointing forward. The Y-axis of the global coordinate system should point down along the gravity vector.
IMU readings are typically in a separate IMU coordinate system, and rotation is needed to map them to the camera coordinate system if the two coordinate systems are different.
All fields are little-endian (least significant byte first), and the 32-bit floating points are of IEEE 754-1985 format.
To accurately synchronize the video frame and the metadata, the PTS of the video frame should be at the center of its exposure (this can also be inferred from exposure metadata).
The application muxing this data should choose a large enough time scale to get an accurate PTS.
Potential issues
This design only allows one packet per data sample. Embedded devices may have issues writing very high frequency packets because it increases I/O pressure, as well as the header size (for example, the stsc and stsz atoms) if the packet size varies.
Mixing different types of data with different delays can cause the PTS to go both forward and backward as packets are written to the file. However, this can be overcome by buffering packets and writing them in monotonic order.