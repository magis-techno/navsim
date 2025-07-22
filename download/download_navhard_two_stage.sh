#!/bin/bash

# OBS base path for navsim-v2 data
OBS_BASE_PATH="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/navsim-v2"

# Download navhard two stage data from OBS
echo "Downloading navhard two stage data from OBS..."
di-mc cp "${OBS_BASE_PATH}/navsim_v2.2_navhard_two_stage_curr_sensors.tar.gz" .
di-mc cp "${OBS_BASE_PATH}/navsim_v2.2_navhard_two_stage_hist_sensors.tar.gz" .
di-mc cp "${OBS_BASE_PATH}/navsim_v2.2_navhard_two_stage_scene_pickles.tar.gz" .

echo "Extracting navhard two stage files..."
tar -xzvf navsim_v2.2_navhard_two_stage_curr_sensors.tar.gz
tar -xzvf navsim_v2.2_navhard_two_stage_hist_sensors.tar.gz
tar -xzvf navsim_v2.2_navhard_two_stage_scene_pickles.tar.gz

rm navsim_v2.2_navhard_two_stage_curr_sensors.tar.gz
rm navsim_v2.2_navhard_two_stage_hist_sensors.tar.gz
rm navsim_v2.2_navhard_two_stage_scene_pickles.tar.gz

echo "Navhard two stage dataset download completed!"
