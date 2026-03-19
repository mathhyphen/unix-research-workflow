# Intent Schema Reference

## Validator-Required Fields

`scripts/validate_intent.py` currently requires:

- `branch`: Must match `expl/<name>`
- `objective`: String with at least 20 characters
- `hypothesis`: String with at least 20 characters
- `success_criteria.metrics`: Non-empty list of metric checks

Each success metric must include:

- `name`
- `threshold`
- `direction`: `lower_is_better` or `higher_is_better`

## Recommended Fields

The validator does not enforce these yet, but they are useful for real research:

- `experiment`
- `dataset`
- `task`
- `model`
- `conditioning`
- `preprocessing`
- `seed`
- `constraints`
- `notes`

## Minimal Example

```yaml
experiment: unet-baseline
branch: expl/unet-baseline
objective: |
  Train a baseline 3D U-Net and verify the preprocessing pipeline is correct.
hypothesis: |
  A clean baseline should reach stable validation loss and useful overlap metrics.
success_criteria:
  metrics:
    - name: val_loss
      threshold: 0.1
      direction: lower_is_better
constraints:
  max_runtime_hours: 24
```

## Medical Imaging Generation Example

```yaml
experiment: mri-to-ct-fm-baseline
branch: expl/mri-to-ct-fm-baseline
objective: |
  Train a flow-matching baseline for paired MRI to CT synthesis and measure image fidelity.
hypothesis: |
  Conditioning on aligned T1 MRI volumes should reduce CT synthesis error versus an unconditional baseline.
dataset:
  name: paired-brain-mri-ct
  split: train-val-test
task: mri_to_ct_synthesis
model:
  family: flow_matching
  backbone: 3d-unet
conditioning:
  modality: t1_mri
preprocessing:
  resample_spacing_mm: [1.0, 1.0, 1.0]
  intensity_normalization: zscore
  crop: brain_bbox
success_criteria:
  metrics:
    - name: val_mae
      threshold: 75.0
      direction: lower_is_better
    - name: val_ssim
      threshold: 0.90
      direction: higher_is_better
constraints:
  max_runtime_hours: 48
  gpu: 1xA100-80GB
notes: |
  Record whether training uses paired supervision, latent-space training, and EMA.
```

## Common Failure Modes

- Objective or hypothesis is too short and fails validation.
- `branch` does not match `expl/<name>`.
- `success_criteria.metrics` is empty.
- `threshold` is written as text instead of a number.
- `direction` is not one of the supported values.
