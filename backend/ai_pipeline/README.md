# AI Pipeline: Demolition Material Detection & Volumetric Estimation

This subsystem is the core computer vision engine for **Demolition Intelligence & Material Recovery**. It is strictly decoupled from the web application layer to allow independent testing, model versioning, and scalable GPU worker execution.

## Supported Material Classes

The visual detector classifies 6 primary material streams:
1. `CONCRETE` (Crushed aggregate, structural precast slabs, foundation piers)
2. `BRICKS` (Clay masonry, facing bricks, refractory bricks)
3. `STEEL` (I-beams, rebar cages, structural trusses, corrugated sheeting)
4. `TIMBER` (Hardwood beams, dimensional lumber, rafters, flooring)
5. `GLASS` (Architectural window panes, tempered sheets, cullet)
6. `MIXED_DEBRIS` (Unsorted demolition rubble, plaster, insulation)

## Architecture Overview

```
Raw Image Bytes (Drone/Handheld)
             │
             ▼
     ImagePreprocessor (EXIF correction, SAHI tile slicing)
             │
             ▼
     YOLOMaterialDetector (BaseMaterialDetector contract)
             │  ↳ Yields: List[DetectionBox] (normalized coords, category, confidence)
             ▼
     GeometricQuantityEstimator (BaseQuantityEstimator contract)
             │  ↳ Yields: Volume (m³), Weight (Tonnes), Surface Area (m²)
             ▼
     HeuristicConditionAssessor (BaseConditionClassifier contract)
             │  ↳ Yields: ConditionGrade, Contamination/Hazard Flags
             ▼
     MaterialValuationService (USD value & Embodied Carbon Offsets)
```

## Dataset & Training Guide

### 1. Dataset Annotation Format
Annotations should adhere to standard YOLO format:
```
<class_id> <x_center> <y_center> <width> <height>
```
With class IDs:
- `0`: concrete
- `1`: bricks
- `2`: steel
- `3`: timber
- `4`: glass
- `5`: mixed_debris

### 2. Recommended Open-Source Datasets for Fine-Tuning
- **Construction & Demolition Waste (Roboflow / Mendeley)**: High-resolution scrap and rubble photos.
- **TACO (Trash Annotations in Context)**: Extended for outdoor industrial scrap.
- **ISPRS Benchmark on Urban Classification**: High-altitude building demolition photogrammetry.

### 3. Model Training Command
Run training using Ultralytics YOLOv8 / YOLOv11 on GPU:
```bash
yolo detect train \
  data=datasets/demolition_materials.yaml \
  model=yolov8x.pt \
  epochs=120 \
  imgsz=1280 \
  batch=8 \
  device=0 \
  project=runs/demolition \
  name=demolition_v1
```

### 4. Deploying Weights
Copy the resulting best checkpoint:
```bash
cp runs/demolition/demolition_v1/weights/best.pt backend/ai_pipeline/weights/demolition_materials_yolov8.pt
```
If the weights file is absent, the backend explicitly raises `ModelWeightsNotFoundError` rather than returning fictitious mock data.
