from .planner import Planner
from .executor import Executor
from ..tools.registry import TOOLS


async def run_agent(user_request: str, planner: Planner):
    plan = await planner.plan(user_request)
    print("\n================================ PLAN ===================================")
    print(plan)

    executor = Executor(tools=TOOLS)

    summary = await executor.run_plan(plan)

    print(
        "\n============================== EXECUTION ================================="
    )
    for r in executor.step_results:
        print(r)

    print(
        "\n=============================== SUMMARY =================================="
    )
    print(summary)

    if plan.fallback and summary.total_events < plan.success_criteria.min_events:
        print(
            "\n============================== FALLBACK =================================="
        )

        for step in plan.fallback.steps:
            await executor.run_step(step)

        summary = executor.summary()
        print(summary)

    return executor.events, executor.step_results, summary
