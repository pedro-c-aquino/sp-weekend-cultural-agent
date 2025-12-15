import sys

if sys.platform.startswith("win"):
    import asyncio

    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

import asyncio, json, typer
from rich import print
from .agents.orchestrator import Orchestrator

app = typer.Typer(help="Multi-agent tools for SP weekend events")


@app.command(help="Run the multi-agent weekend discovery (SERP-first).")
def weekend(
    focus: str = "samba",
    model: str = "mistral:7b",
    mode: str = typer.Option("serp", help="serp or crawl"),
):
    orch = Orchestrator(model=model)
    result = asyncio.run(orch.weekend_run(focus=focus, mode=mode))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
