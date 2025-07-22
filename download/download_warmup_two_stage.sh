#!/bin/bash

# OBS base path for navsim-v2 data
OBS_BASE_PATH="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/navsim-v2"

# Download warmup two stage data from OBS
echo "Downloading navsim_v2.2_warmup_two_stage.tar.gz from OBS..."
di-mc cp "${OBS_BASE_PATH}/navsim_v2.2_warmup_two_stage.tar.gz" .
tar -xzvf navsim_v2.2_warmup_two_stage.tar.gz
rm navsim_v2.2_warmup_two_stage.tar.gz

echo "Warmup two stage dataset download completed!"
