#!/usr/bin/env python3
"""Publish a rolling, fixed-frame accumulation of sensor_msgs/PointCloud2."""

import threading
from collections import deque

import rospy
import tf2_ros
from sensor_msgs.msg import PointCloud2
from tf2_sensor_msgs.tf2_sensor_msgs import do_transform_cloud


def clean_frame(frame_id):
    """tf2 frame ids must not start with a slash."""
    return frame_id.lstrip("/")


class CloudAccumulator:
    def __init__(self):
        self.fixed_frame = clean_frame(rospy.get_param("~fixed_frame", "livox_frame"))
        self.decay_time = rospy.Duration.from_sec(
            max(0.01, float(rospy.get_param("~decay_time", 1.0)))
        )
        self.tf_timeout = rospy.Duration.from_sec(
            max(0.0, float(rospy.get_param("~tf_timeout", 0.1)))
        )
        self.max_points = int(rospy.get_param("~max_points", 25000))
        self.publish_rate = max(0.1, float(rospy.get_param("~publish_rate", 10.0)))
        self.lock = threading.Lock()
        self.clouds = deque()  # (scan timestamp, transformed PointCloud2)
        self.layout = None

        self.tf_buffer = tf2_ros.Buffer(cache_time=rospy.Duration(10.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        input_topic = rospy.get_param("~input_topic", "/livox/lidar")
        output_topic = rospy.get_param("~output_topic", "/livox/lidar_accumulated")
        self.publisher = rospy.Publisher(output_topic, PointCloud2, queue_size=1)
        self.subscriber = rospy.Subscriber(
            input_topic, PointCloud2, self.cloud_callback, queue_size=2
        )
        self.timer = rospy.Timer(
            rospy.Duration.from_sec(1.0 / self.publish_rate), self.publish_cloud
        )

        rospy.loginfo(
            "Accumulating %s in %s for %.2f s; publishing %s at %.1f Hz",
            input_topic,
            self.fixed_frame,
            self.decay_time.to_sec(),
            output_topic,
            self.publish_rate,
        )

    @staticmethod
    def layout_of(cloud):
        return (
            tuple((f.name, f.offset, f.datatype, f.count) for f in cloud.fields),
            cloud.point_step,
            cloud.is_bigendian,
        )

    @staticmethod
    def packed_data(cloud):
        """Remove any row padding so point records can be concatenated."""
        row_bytes = cloud.width * cloud.point_step
        if cloud.row_step == row_bytes:
            return bytes(cloud.data)
        data = bytes(cloud.data)
        return b"".join(
            data[row * cloud.row_step : row * cloud.row_step + row_bytes]
            for row in range(cloud.height)
        )

    def prune(self, now):
        cutoff = now - self.decay_time
        while self.clouds and self.clouds[0][0] < cutoff:
            self.clouds.popleft()

    def cloud_callback(self, cloud):
        if cloud.width == 0 or cloud.height == 0 or cloud.point_step == 0:
            return

        stamp = (
            cloud.header.stamp
            if cloud.header.stamp != rospy.Time()
            else rospy.Time.now()
        )
        source_frame = clean_frame(cloud.header.frame_id)
        if not source_frame:
            rospy.logwarn_throttle(5.0, "Dropping cloud with an empty frame_id")
            return

        if source_frame == self.fixed_frame:
            # The Livox driver labels the cloud with livox_frame but does not
            # publish a transform for it. Clouds already in the target frame
            # can be accumulated directly.
            fixed_cloud = cloud
        else:
            try:
                transform = self.tf_buffer.lookup_transform(
                    self.fixed_frame, source_frame, stamp, self.tf_timeout
                )
                fixed_cloud = do_transform_cloud(cloud, transform)
            except (
                tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException,
            ) as exc:
                rospy.logwarn_throttle(
                    5.0, "Cannot transform cloud into %s: %s", self.fixed_frame, exc
                )
                return

        layout = self.layout_of(fixed_cloud)
        with self.lock:
            if self.layout is not None and self.layout != layout:
                rospy.logwarn(
                    "PointCloud2 layout changed; clearing accumulated history"
                )
                self.clouds.clear()
            self.layout = layout
            self.prune(rospy.Time.now())
            self.clouds.append((stamp, fixed_cloud))

    def publish_cloud(self, _event):
        now = rospy.Time.now()
        with self.lock:
            self.prune(now)
            if not self.clouds:
                return
            clouds = list(self.clouds)

        template = clouds[-1][1]
        point_step = template.point_step
        records = b"".join(self.packed_data(cloud) for _, cloud in clouds)
        count = len(records) // point_step
        if count == 0:
            return

        # Cap the outgoing message with evenly spaced samples to keep network
        # and browser load bounded while preserving the full-resolution scans
        # in the original Livox topic.
        if self.max_points > 0 and count > self.max_points:
            records = b"".join(
                records[
                    (index * count // self.max_points)
                    * point_step : (index * count // self.max_points + 1)
                    * point_step
                ]
                for index in range(self.max_points)
            )
            count = len(records) // point_step

        output = PointCloud2()
        output.header.stamp = now
        output.header.frame_id = self.fixed_frame
        output.height = 1
        output.width = count
        output.fields = template.fields
        output.is_bigendian = template.is_bigendian
        output.point_step = point_step
        output.row_step = count * point_step
        output.data = records
        output.is_dense = all(cloud.is_dense for _, cloud in clouds)
        self.publisher.publish(output)


if __name__ == "__main__":
    rospy.init_node("cloud_accumulator")
    CloudAccumulator()
    rospy.spin()
