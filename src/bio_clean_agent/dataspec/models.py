from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, validator


class Dataset(BaseModel):
    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    dataset_type: Literal["sequencing", "transcriptomics", "metabolomics"]
    raw_paths: List[str] = Field(..., description="Paths to raw input files")
    metadata_path: Optional[str] = Field(None, description="Optional metadata table associated with the dataset")


class SequencingDataset(Dataset):
    dataset_type: Literal["sequencing"] = "sequencing"
    read_type: Literal["single", "paired"] = Field(..., description="Sequencing read layout")
    platform: Optional[str] = Field(None, description="Sequencing platform description")

    @validator("raw_paths")
    def ensure_fastq(cls, value: List[str]) -> List[str]:
        if any(not path.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")) for path in value):
            raise ValueError("Sequencing raw_paths must be FASTQ files")
        return value


class TranscriptomicsDataset(Dataset):
    dataset_type: Literal["transcriptomics"] = "transcriptomics"
    matrix_format: Literal["counts", "tpm", "fpkm"] = Field(..., description="Expression matrix format")
    gene_annotation: Optional[str] = Field(None, description="Path to gene annotation table")


class MetabolomicsDataset(Dataset):
    dataset_type: Literal["metabolomics"] = "metabolomics"
    analytical_platform: Optional[str] = Field(None, description="LC-MS, GC-MS, NMR, etc.")
    ion_mode: Optional[Literal["positive", "negative"]] = Field(None, description="Ionization mode for MS data")


DATASET_MODEL_MAP = {
    "sequencing": SequencingDataset,
    "transcriptomics": TranscriptomicsDataset,
    "metabolomics": MetabolomicsDataset,
}


def load_dataset(model_type: str, data: dict) -> Dataset:
    try:
        model_cls = DATASET_MODEL_MAP[model_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported dataset_type: {model_type}") from exc
    return model_cls(**data)
