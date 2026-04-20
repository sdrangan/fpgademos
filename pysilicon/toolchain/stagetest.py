"""Helpers for ordered multi-stage test and build flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


StageFunc = Callable[[], object]


@dataclass(frozen=True, slots=True)
class TestStage:
    """Definition of a single named stage in an ordered flow."""

    name: str
    func: StageFunc | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Stage name must not be empty.")


class StageTest:
    """Ordered stage registry for staged demo and test flows."""

    def __init__(self, stages: Iterable[TestStage | str] = ()):
        self._stages: list[TestStage] = []
        self._index_by_name: dict[str, int] = {}
        for stage in stages:
            self.add_stage(stage)

    @classmethod
    def from_names(cls, names: Iterable[str]) -> "StageTest":
        """Construct a stage flow from a sequence of names only."""
        return cls(names)

    @property
    def stages(self) -> tuple[TestStage, ...]:
        """Registered stages in execution order."""
        return tuple(self._stages)

    @property
    def stage_names(self) -> tuple[str, ...]:
        """Registered stage names in execution order."""
        return tuple(stage.name for stage in self._stages)

    def __len__(self) -> int:
        return len(self._stages)

    def __iter__(self):
        return iter(self._stages)

    def add_stage(self, stage: TestStage | str) -> TestStage:
        """Append a new stage to the ordered flow."""
        stage_obj = stage if isinstance(stage, TestStage) else TestStage(name=stage)
        if stage_obj.name in self._index_by_name:
            raise ValueError(f"Duplicate stage name '{stage_obj.name}'.")

        self._index_by_name[stage_obj.name] = len(self._stages)
        self._stages.append(stage_obj)
        return stage_obj

    def has_stage(self, stage_name: str) -> bool:
        """Return whether the named stage exists."""
        return stage_name in self._index_by_name

    def stage_index(self, stage_name: str) -> int:
        """Return the zero-based index of a named stage."""
        try:
            return self._index_by_name[stage_name]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported stage '{stage_name}'. Expected one of {self.stage_names}."
            ) from exc

    def validate_range(
        self,
        start_at: str | None = None,
        through: str | None = None,
    ) -> tuple[str, str]:
        """Validate and normalize an inclusive stage range."""
        if not self._stages:
            raise ValueError("No stages are configured.")

        start_name = self._stages[0].name if start_at is None else start_at
        end_name = self._stages[-1].name if through is None else through

        if self.stage_index(start_name) > self.stage_index(end_name):
            raise ValueError(
                f"start_at stage '{start_name}' must not come after through stage '{end_name}'."
            )

        return start_name, end_name

    def stage_range(
        self,
        start_at: str | None = None,
        through: str | None = None,
    ) -> tuple[TestStage, ...]:
        """Return the inclusive slice of stages for a validated range."""
        start_name, end_name = self.validate_range(start_at, through)
        start_idx = self.stage_index(start_name)
        end_idx = self.stage_index(end_name)
        return tuple(self._stages[start_idx : end_idx + 1])

    def range_names(
        self,
        start_at: str | None = None,
        through: str | None = None,
    ) -> tuple[str, ...]:
        """Return only the stage names for an inclusive range."""
        return tuple(stage.name for stage in self.stage_range(start_at, through))

    def run(
        self,
        start_at: str | None = None,
        through: str | None = None,
        announce: bool = False,
    ) -> list[tuple[str, object]]:
        """Execute the callables attached to each selected stage in order."""
        results: list[tuple[str, object]] = []
        for stage in self.stage_range(start_at, through):
            if stage.func is None:
                raise RuntimeError(f"Stage '{stage.name}' has no callable to run.")
            if announce:
                print(f"Running stage: {stage.name}")
            results.append((stage.name, stage.func()))
        return results