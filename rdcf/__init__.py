"""Core utilities for Thai reverse DCF research workflows."""

__all__ = ["ResearchDataPipeline"]


def __getattr__(name):
    if name == "ResearchDataPipeline":
        from .data_pipeline import ResearchDataPipeline

        return ResearchDataPipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
