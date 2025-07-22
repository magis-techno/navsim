#!/bin/bash

# OBS base path for openscene-v1.1 data
OBS_BASE_PATH="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"

# Download metadata
echo "Downloading openscene_metadata_test.tgz from OBS..."
di-mc cp "${OBS_BASE_PATH}/openscene_metadata_test.tgz" .
tar -xzf openscene_metadata_test.tgz
rm openscene_metadata_test.tgz

# Download camera sensor data
echo "Downloading camera sensor data..."
for split in {0..31}; do
    echo "Downloading openscene_sensor_test_camera_${split}.tgz"
    di-mc cp "${OBS_BASE_PATH}/openscene_sensor_test_camera/openscene_sensor_test_camera_${split}.tgz" .
    echo "Extracting file openscene_sensor_test_camera_${split}.tgz"
    tar -xzf openscene_sensor_test_camera_${split}.tgz
    rm openscene_sensor_test_camera_${split}.tgz
done

# Download lidar sensor data
echo "Downloading lidar sensor data..."
for split in {0..31}; do
    echo "Downloading openscene_sensor_test_lidar_${split}.tgz"
    di-mc cp "${OBS_BASE_PATH}/openscene_sensor_test_lidar/openscene_sensor_test_lidar_${split}.tgz" .
    echo "Extracting file openscene_sensor_test_lidar_${split}.tgz"
    tar -xzf openscene_sensor_test_lidar_${split}.tgz
    rm openscene_sensor_test_lidar_${split}.tgz
done

mv openscene-v1.1/meta_datas test_navsim_logs
mv openscene-v1.1/sensor_blobs test_sensor_blobs
rm -r openscene-v1.1

echo "Test dataset download completed!"
