"""
Self-contained A2A in-memory demo using the core registry + message bus + agents.
This runs without external web dependencies and showcases:
User → Orchestrator → Research → Analysis → Visualization → Final result
"""

import asyncio
from pprint import pprint

from core.registry import AgentRegistry
from core.message_bus import A2AMessageBus
from orchestrator.orchestrator import A2AOrchestrator
from agents.research_agent import ResearchAgent
from agents.analysis_agent import DataAnalysisAgent
from agents.visualization_agent import VisualizationAgent


async def run_demo_once(user_input: str):
    registry = AgentRegistry()
    bus = A2AMessageBus()

    orchestrator = A2AOrchestrator(registry, bus)
    research = ResearchAgent(registry, bus)
    analysis = DataAnalysisAgent(registry, bus)
    viz = VisualizationAgent(registry, bus)

    await research.start()
    await analysis.start()
    await viz.start()

    print("\n=== USER REQUEST ===")
    print(user_input)

    result = await orchestrator.handle_user_request(user_input)

    print("\n=== RESULT ===")
    pprint(result)

    await research.stop()
    await analysis.stop()
    await viz.stop()


async def main():
    # Scenario 1: triggers research → analysis → visualization delegation
    await run_demo_once("Research AI trends and analyze the data for visualization")

    # Scenario 2: research only (no analysis keyword)
    await run_demo_once("Research top AI companies by market cap")


if __name__ == "__main__":
    asyncio.run(main())