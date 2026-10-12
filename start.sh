#!/bin/env bash

gnome-terminal \
    --tab -t "mount" -e "bash -c 'mount | grep -q storage || mount -L stf storage; exec bash'" \
    --tab -t "ptp" -e "bash -c 'ptp4l -i end0 -l 6 -m; exec bash'" \
    --tab -t "http" -e "bash -c 'python -m http.server -d ros3djs; exec bash'" \
    --tab -t "livox" -e "bash -c 'roslaunch livox_ros_driver livox_lidar_rviz.launch publish_freq:=20 xfer_format:=2; exec bash'" \
    --tab -t "cam" -e "bash -c 'sleep 2; roslaunch hikrobot_camera multi_camera_rviz.launch; exec bash'" \
    --tab -t "rosbridge" -e "bash -c 'sleep 4; roslaunch rosbridge_server rosbridge_websocket.launch port:=22000; exec bash'" \
    --tab -t "tf2" -e "bash -c 'sleep 6; rosrun tf2_web_republisher tf2_web_republisher; exec bash'" \
    --tab -t "accumulator" -e "bash -c 'sleep 6; python cloud_accumulator.py; exec bash'" \
    --tab -t "webvideo" -e "bash -c 'sleep 6; rosrun web_video_server web_video_server _default_stream_type:=ros_compressed _verbose:=true; exec bash'" \
    --tab -t "mediamtx" -e "bash -c 'sleep 8; cd mediamtx; ./mediamtx; exec bash'" \
    --tab -t "frpc" -e "bash -c 'sleep 10; cd frp; ./frpc --config-dir cfg || true; exec bash'" \
