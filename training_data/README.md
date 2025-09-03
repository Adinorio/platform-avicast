# 🦆 Chinese Egret Training Data Architecture

This directory contains all data, scripts, and configurations related to training
the Chinese Egret detection model. It follows a clean, logical data flow.

## 📁 Directory Structure

- **`raw_images/`**: Contains the original, unprocessed training images organized in batch folders. This is the raw input.

- **`exported_annotations/`**: Contains the original annotation files as exported from labeling tools (e.g., COCO JSON, YOLO ZIPs).

- **`prepared_dataset/`**: This is an intermediate directory holding the consolidated data after initial processing.
  - `images/`: All raw images copied into a single folder.
  - `labels/`: All annotations extracted into `.txt` format in a single folder.

- **`final_yolo_dataset/`**: Contains the final, analysis-ready dataset, split into training, validation, and test sets in the format required by YOLOv8.
  - `bird_dataset_v1/`: The final dataset, ready for training.

## 🔄 Data Flow

1.  **Raw Data**: Starts in `raw_images/` and `exported_annotations/`.
2.  **Preparation**: Scripts process this raw data and place the consolidated, clean files into `prepared_dataset/`.
3.  **Organization**: Scripts then split the prepared data into `train/`, `valid/`, and `test/` sets, creating the `final_yolo_dataset/`.
4.  **Training**: The training pipeline reads directly from `final_yolo_dataset/`.

## 🚀 How to Use

1.  **Place Data**: Add raw images to `raw_images/` and annotations to `exported_annotations/`.
2.  **Run Preparation**: Execute the data preparation scripts (e.g., `prepare_data_minimal.py`).
3.  **Train Model**: Run the training script, which will automatically find the dataset in `final_yolo_dataset/`.
