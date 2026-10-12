#!/bin/env bash

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y --no-install-recommends \
    bash-completion \
    command-not-found \
    dialog \
    apt-utils \
    net-tools \
    iputils-ping \
    iproute2 \
    ethtool \
    linuxptp \
    dbus-x11 \
    libcanberra-gtk3-module \
    gnome-terminal \
    git \
    ninja-build \
    ros-${ROS_DISTRO}-rviz \
    ros-${ROS_DISTRO}-rosbridge-suite \
    ros-${ROS_DISTRO}-tf2-web-republisher \
    ros-${ROS_DISTRO}-web-video-server \
    ros-${ROS_DISTRO}-tf2-sensor-msgs \
    python3-catkin-tools \
    python-is-python3
