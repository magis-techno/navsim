#!/bin/bash

# OBS base paths
OBS_OPENSCENE_PATH="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/openscene-v1.1"
OBS_NAVSIM_PATH="training/yw-ads-training-gy1/data/opensource/huggingface/dataset/OpenDriveLab/OpenScene/main/navsim"

# Download metadata from OBS
echo "Downloading openscene_metadata_trainval.tgz from OBS..."
di-mc cp "${OBS_OPENSCENE_PATH}/openscene_metadata_trainval.tgz" .
tar -xzf openscene_metadata_trainval.tgz
rm openscene_metadata_trainval.tgz
mv openscene-v1.1/meta_datas trainval_navsim_logs
rm -r openscene-v1.1

# Download sensor data from OBS navsim directory
mkdir -p trainval_sensor_blobs/trainval

# Download current sensor data
for split in {1..4}; do
    echo "Downloading navtrain_current_${split}.tgz from OBS..."
    di-mc cp "${OBS_NAVSIM_PATH}/navtrain_current_${split}.tgz" .
    echo "Extracting file navtrain_current_${split}.tgz"
    tar -xzf navtrain_current_${split}.tgz
    rm navtrain_current_${split}.tgz

    # Check which directory structure was created and sync accordingly
    if [ -d "navtrain_current_${split}" ]; then
        rsync -rv navtrain_current_${split}/* trainval_sensor_blobs/trainval
        rm -r navtrain_current_${split}
    elif [ -d "current_split_${split}" ]; then
        rsync -rv current_split_${split}/* trainval_sensor_blobs/trainval
        rm -r current_split_${split}
    else
        echo "Warning: Unexpected directory structure after extracting navtrain_current_${split}.tgz"
    fi
done

# Download history sensor data
for split in {1..4}; do
    echo "Downloading navtrain_history_${split}.tgz from OBS..."
    di-mc cp "${OBS_NAVSIM_PATH}/navtrain_history_${split}.tgz" .
    echo "Extracting file navtrain_history_${split}.tgz"
    tar -xzf navtrain_history_${split}.tgz
    rm navtrain_history_${split}.tgz

    # Check which directory structure was created and sync accordingly
    if [ -d "navtrain_history_${split}" ]; then
        rsync -rv navtrain_history_${split}/* trainval_sensor_blobs/trainval
        rm -r navtrain_history_${split}
    elif [ -d "history_split_${split}" ]; then
        rsync -rv history_split_${split}/* trainval_sensor_blobs/trainval
        rm -r history_split_${split}
    else
        echo "Warning: Unexpected directory structure after extracting navtrain_history_${split}.tgz"
    fi
done

echo "Navtrain OBS dataset download completed!"
