#!/bin/bash

# OBS base path for openscene-v1.1 data
OBS_BASE_PATH="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"

# Download navsim-v2 data (keep original wget for now)
echo "Downloading navsim_v2.2_private_test_hard_two_stage.tar.gz..."
wget https://huggingface.co/datasets/OpenDriveLab/OpenScene/resolve/main/navsim-v2/navsim_v2.2_private_test_hard_two_stage.tar.gz
tar -xzf navsim_v2.2_private_test_hard_two_stage.tar.gz
rm navsim_v2.2_private_test_hard_two_stage.tar.gz

# Download sensor data from OBS
echo "Downloading openscene_sensor_private_test_hard.tar.gz from OBS..."
di-mc cp "${OBS_BASE_PATH}/openscene_sensor_private_test_hard.tar.gz" .
tar -xzf openscene_sensor_private_test_hard.tar.gz
rm openscene_sensor_private_test_hard.tar.gz
mv openscene-v1.1/sensor_blobs/ private_test_hard_navsim_sensor
rm -r openscene-v1.1

# Download metadata from OBS
echo "Downloading openscene_metadata_private_test_hard.tar.gz from OBS..."
di-mc cp "${OBS_BASE_PATH}/openscene_metadata_private_test_hard.tar.gz" .
tar -xzf openscene_metadata_private_test_hard.tar.gz
rm openscene_metadata_private_test_hard.tar.gz
mv openscene-v1.1/meta_datas/ private_test_hard_navsim_log
rm -r openscene-v1.1

echo "Private test hard two stage dataset download completed!"
