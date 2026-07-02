"""Compatibility helpers for legacy script entry points."""

from __future__ import annotations

import runpy


def run_module(module_name: str) -> None:
    """Run a module as if it were invoked with python -m."""
    runpy.run_module(module_name, run_name="__main__")
