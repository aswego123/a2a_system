import asyncio

from core.registry import AgentRegistry
from core.message_bus import A2AMessageBus
from orchestrator.orchestrator import A2AOrchestrator
from agents.research_agent import ResearchAgent
from agents.analysis_agent import DataAnalysisAgent
from agents.visualization_agent import VisualizationAgent


async def main():
    """Main application entry point"""
    # Initialize core components
    registry = AgentRegistry()
    message_bus = A2AMessageBus()

    # Create orchestrator
    orchestrator = A2AOrchestrator(registry, message_bus)

    # Create and start agents
    research_agent = ResearchAgent(registry, message_bus)
    analysis_agent = DataAnalysisAgent(registry, message_bus)
    visualization_agent = VisualizationAgent(registry, message_bus)

    await research_agent.start()
    await analysis_agent.start()
    await visualization_agent.start()

    print("A2A System initialized")
    print(f"Registered agents: {list(registry.agents.keys())}")

    # Simulate user request
    user_input = "Research AI trends and analyze the data"
    print(f"\nUser Request: {user_input}")

    result = await orchestrator.handle_user_request(user_input)
    print(f"\nResult: {result}")

    # Cleanup
    await research_agent.stop()
    await analysis_agent.stop()
    await visualization_agent.stop()


if __name__ == "__main__":
    asyncio.run(main())

async def main():
    """Main application entry point"""
    # Initialize core components
    registry = AgentRegistry()
    message_bus = A2AMessageBus()
    
    # Create orchestrator
    orchestrator = A2AOrchestrator(registry, message_bus)
    
    # Create and start agents
    research_agent = ResearchAgent(registry, message_bus)
    analysis_agent = DataAnalysisAgent(registry, message_bus)
    
    await research_agent.start()
    await analysis_agent.start()
    
    print("A2A System initialized")
    print(f"Registered agents: {list(registry.agents.keys())}")
    
    # Simulate user request
    user_input = "Research AI trends and analyze the data"
    print(f"\nUser Request: {user_input}")
    
    result = await orchestrator.handle_user_request(user_input)
    print(f"\nResult: {result}")
    
    # Cleanup
    await research_agent.stop()
    await analysis_agent.stop()


if __name__ == "__main__":
    asyncio.run(main())