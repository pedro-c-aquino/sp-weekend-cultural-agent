import time
from typing import Dict, Callable, Awaitable, Any, List
from ..schemas import (
    EventList,
    FetchResult,
    Plan,
    PlanStep,
    StepResult,
    ExecutionSummary,
    Event,
)

ToolFn = Callable[..., Awaitable[Any]]


class Executor:
    def __init__(self, tools: Dict[str, ToolFn]):
        self.tools = tools
        self.pages: List[FetchResult] = []
        self.events: List[Event] = []
        self.sources = set()
        self.step_results: List[StepResult] = []

    async def run_step(self, step: PlanStep) -> StepResult:
        fn = self.tools.get(step.tool)

        if not fn:
            return StepResult(
                tool=step.tool,
                ok=False,
                errors=1,
                notes=f"Tool not registered: {step.tool}",
            )

        start = time.perf_counter()

        try:
            duration_ms = int((time.perf_counter() - start) * 1000)

            if step.tool.startswith("fetch_"):
                page: FetchResult = await fn()
                self.pages.append(page)
                self.sources.add(page.source)

                events_found = None

            elif step.tool == "extract_events":
                extracted: EventList = []

                for page in self.pages:
                    batch = await fn(page)
                    extracted.extend(batch.events or [])

                self.events.extend(extracted)
                events_found = len(extracted)

            elif step.tool in ("dedupe_events", "validate_events"):
                self.events = await fn(self.events)
                events_found = len(self.events)

            duration_ms = int((time.perf_counter() - start) * 1000)

            sr = StepResult(
                tool=step.tool,
                ok=True,
                events_found=events_found,
                duration_ms=duration_ms,
            )

        except Exception as e:
            sr = StepResult(
                tool=step.tool,
                ok=False,
                errors=1,
                notes=str(e),
            )

        self.step_results.append(sr)
        return sr

    async def run_plan(self, plan: Plan) -> ExecutionSummary:
        for step in plan.steps:
            await self.run_step(step)

        return self.summary()

    def summary(self) -> ExecutionSummary:
        return ExecutionSummary(
            total_events=len(self.events),
            sources_used=sorted(self.sources),
            erros=sum(1 for r in self.step_results if not r.ok),
        )
