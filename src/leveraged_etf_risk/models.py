"""Model fitting interfaces.

Implement the GBM benchmark and GARCH(1,1)-t model here. Return structured
parameters and diagnostics; do not write presentation claims inside the model.
"""

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ModelFit:
    model_name: str
    parameters: Mapping[str, float]
    diagnostics: Mapping[str, float]


def fit_models(*args, **kwargs) -> list[ModelFit]:
    raise NotImplementedError("Model fitting must be implemented and validated by workstream C")

