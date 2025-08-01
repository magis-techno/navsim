#!/bin/bash

# OBS base path for openscene-v1.1 data
OBS_BASE_PATH="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"

# Download metadata from OBS
echo "Downloading openscene_metadata_trainval.tgz from OBS..."
di-mc cp "${OBS_BASE_PATH}/openscene_metadata_trainval.tgz" .
tar -xzf openscene_metadata_trainval.tgz
rm openscene_metadata_trainval.tgz
mv openscene-v1.1/meta_datas trainval_navsim_logs
rm -r openscene-v1.1

# Download sensor data from HuggingFace navsim repository (keep original logic)
mkdir -p trainval_sensor_blobs/trainval
for split in {1..32}; do
    echo "Downloading navtrain_current_${split}.tgz from HuggingFace..."
    wget https://huggingface.co/datasets/OpenDriveLab/OpenScene/resolve/main/navsim/navtrain_current_${split}.tgz
    echo "Extracting file navtrain_current_${split}.tgz"
    tar -xzf navtrain_current_${split}.tgz
    rm navtrain_current_${split}.tgz

    rsync -rv navtrain_current_${split}/* trainval_sensor_blobs/trainval
    rm -r navtrain_current_${split}
done

for split in {1..32}; do
    echo "Downloading navtrain_history_${split}.tgz from HuggingFace..."
    wget https://huggingface.co/datasets/OpenDriveLab/OpenScene/resolve/main/navsim/navtrain_history_${split}.tgz
    echo "Extracting file navtrain_history_${split}.tgz"
    tar -xzf navtrain_history_${split}.tgz
    rm navtrain_history_${split}.tgz

    rsync -rv navtrain_history_${split}/* trainval_sensor_blobs/trainval
    rm -r navtrain_history_${split}
done

echo "Navtrain HuggingFace dataset download completed!"
