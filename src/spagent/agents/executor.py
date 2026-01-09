import time
from typing import Dict, Callable, Awaitable, Any, List
from ..schemas import Plan, PlanStep, StepResult, ExecutionSummary

ToolFn = Callable[..., Awaitable[Any]]


class Executor:
    def __init__(self, tools: Dict[str, ToolFn]):
        self.tools = tools
        self.events = []
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
            result = await fn(**step.params)

            duration_ms = int((time.perf_counter() - start) * 1000)

            if isinstance(result, list):
                if step.tool.startswith("crawl") or step.tool == "websearch_events":
                    self.sources.add(step.tool)
                    self.events.extend(result)
                else:
                    self.events = result

                events_found = len(result)
            else:
                events_found = None

            sr = StepResult(
                tool=step.tool,
                ok=True,
                events_found=events_found,
                duration_ms=duration_ms,
            )

        except Exception as e:
            sr = StepResult(tool=step.tool, ok=False, errors=1, notes=str(e))

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
