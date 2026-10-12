#!/bin/env bash

IP1=8.134.158.126
IP2=47.243.214.203
PORT=8554
RTSP_URL1="rtsp://${IP1}:${PORT}/live/camera1"
RTSP_URL2="rtsp://${IP2}:${PORT}/live/camera1"
RTSP_OPTIONS="[onfail=ignore:use_fifo=1:f=rtsp:rtsp_transport=tcp]"
ENCODER=libx264

ffmpeg \
    -loglevel verbose -fflags nobuffer -flags low_delay \
    -i "http://localhost:8080/stream?topic=/hikrobot_camera1/rgb" \
    -map 0:v -c:v ${ENCODER} -preset ultrafast -tune zerolatency -g 20 -keyint_min 20 \
    -b:v 2M -maxrate 2.5M -bufsize 1M \
    -f rtsp "rtsp://localhost:8554/live/camera1"
    # -f tee "${RTSP_OPTIONS}${RTSP_URL1}|${RTSP_OPTIONS}${RTSP_URL2}"
