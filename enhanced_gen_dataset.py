
import numpy as np
from scipy.integrate import cumtrapz

            if ptr1 == n_input - 1:
                break
        while input_timestamp[ptr2] < output_timestamp[i]:
            ptr2 += 1
            if ptr2 == n_input:
                break
        q1 = quaternion.quaternion(*quat_data[ptr1])
        q2 = quaternion.quaternion(*quat_data[ptr2])
        quat_inter[i] = quaternion.as_float_array(quaternion.quaternion_time_series.slerp(q1, q2, input_timestamp[ptr1],
                                                                                          input_timestamp[ptr2],
                                                                                          output_timestamp[i]))
    return quat_inter


def interpolate_3dvector_linear(input, input_timestamp, output_timestamp):
    """
    This function interpolate n-d vectors (despite the '3d' in the function name) into the output time stamps.
    
    Args:
        input: Nxd array containing N d-dimensional vectors.
        input_timestamp: N-sized array containing time stamps for each of the input quaternion.
        output_timestamp: M-sized array containing output time stamps.
    Return:
        quat_inter: Mxd array containing M vectors.
    """
    assert input.shape[0] == input_timestamp.shape[0]
    func = scipy.interpolate.interp1d(input_timestamp, input, axis=0)
    interpolated = func(output_timestamp)
    return interpolated


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', type=str, default=None, help='Path to a list file.')
    parser.add_argument('--path', type=str, default=None, help='Path to a dataset folder.')
    parser.add_argument('--skip_front', type=int, default=800, help='Number of discarded records at beginning.')
    parser.add_argument('--skip_end', type=int, default=800, help='Numbef of discarded records at end')
    parser.add_argument('--recompute', action='store_true',
                        help='When set, the previously computed results will be over-written.')
    parser.add_argument('--no_trajectory', action='store_true',
                        help='When set, no ply files will be written.')
    parser.add_argument('--no_magnet', action='store_true',
                        help='If set to true, Magnetometer data will not be processed. This is to deal with'
                             'occasion magnet data corruption.')
    parser.add_argument('--no_remove_duplicate', action='store_true')
    parser.add_argument('--clear_result', action='store_true')

    args = parser.parse_args()

    dataset_list = []
    root_dir = ''
    if args.path:
        dataset_list.append(args.path)
    elif args.list:
        root_dir = os.path.dirname(args.list) + '/'
        with open(args.list) as f:
            for s in f.readlines():
                if s[0] is not '#':
                    dataset_list.append(s.strip('\n'))
    else:
        raise ValueError('No data specified')

    print(dataset_list)

    nano_to_sec = 1000000000.0
    total_length = 0.0
    length_dict = {}
    for dataset in dataset_list:
        if len(dataset.strip()) == 0:
            continue

# Our Kalman Filter Class

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


# Our Sensor Fusion Function

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


# Our Trajectory Estimation Function

def integrate_trajectory_dx(angular_velocity, acceleration, dx):
    orientation = cumtrapz(angular_velocity, dx=dx, initial=0)
    velocity = cumtrapz(acceleration, dx=dx, initial=0)
    position = cumtrapz(velocity, dx=dx, initial=0)
    return position


# Incorporate sensor fusion and trajectory estimation into the data processing pipeline
# (Assuming data arrays for angular_velocity, acceleration, and time are available)
fused_angular_velocity, fused_acceleration = sensor_fusion(angular_velocity, acceleration, time)
trajectory = integrate_trajectory_dx(fused_angular_velocity, fused_acceleration, sample_duration)
