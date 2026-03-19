# Medical Imaging Reference

Use this reference when the experiment involves MRI, CT, PET, ultrasound, or other medical imaging generation work.

## Good Fit for This Workflow

This repository works well for:

- MRI-to-CT or CT-to-MRI synthesis
- diffusion or flow matching baselines
- image-to-image translation with paired or weakly paired data
- ablations on preprocessing, conditioning, losses, and samplers
- local experiments that need reproducible intents and report artifacts

## Recommended Intent Additions

Add domain-specific fields to `intent.yaml` even if validation does not yet require them:

```yaml
task: mri-to-ct-synthesis
modalities:
  source: MRI-T1
  target: CT
dataset:
  name: BraTS2020
  split: patient-level
  pairing: paired
preprocessing:
  spacing_mm: [1.0, 1.0, 1.0]
  intensity_normalization: zscore
  registration: rigid
model:
  family: flow-matching
  backbone: 3d-unet
training:
  patch_size: [128, 128, 128]
  batch_size: 2
  seed: 42
evaluation:
  primary_metrics: [mae, psnr, ssim]
```

## Metrics Worth Tracking

For synthesis quality:

- `mae`
- `rmse`
- `psnr`
- `ssim`
- `lpips`

For downstream usefulness:

- segmentation `dice`
- lesion sensitivity
- HU calibration error for CT-like outputs

## Practical Guardrails

- Record whether training is `2D`, `2.5D`, or `3D`.
- Record whether data is paired, unpaired, or pseudo-paired.
- Keep patient-level splits explicit to avoid leakage.
- Log the preprocessing recipe, especially registration, resampling, clipping, and normalization.
- Prefer evaluation on clinically meaningful regions, not only whole-volume averages.
- If a metric is modality-specific, state it in `success_criteria`.

## Example Requests This Skill Should Handle

- Create a baseline experiment for MRI-to-CT synthesis with flow matching.
- Compare diffusion and flow matching runs on validation SSIM and MAE.
- Summarize a 3D medical imaging generation run and check whether the success criteria were met.
