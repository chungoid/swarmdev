#!/usr/bin/env python3
"""
Demonstration of the Enhanced Collaborative Agent's improved MCP tool integration.
This shows the new retry logic, better error handling, and enhanced user feedback.
"""

import sys
import os
import time
import json

# Add SwarmDev source to path and ensure we're running from project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # Parent of scripts/ directory
sys.path.insert(0, os.path.join(project_root, 'src'))

# Change to project root directory
original_cwd = os.getcwd()
os.chdir(project_root)

from swarmdev.utils.mcp_manager import MCPManager
from swarmdev.interactive_agent.collaborative_agent import CollaborativeAgent

class MockLLMProvider:
    """Mock LLM provider for demonstration."""
    
    def generate_text(self, prompt, **kwargs):
        if "tool selection" in prompt.lower():
            # Demo various tool selection scenarios
            if "time" in prompt:
                return "time"
            elif "analyze" in prompt or "step by step" in prompt:
                return "sequential-thinking"
            elif "files" in prompt or "directory" in prompt:
                return "filesystem"
            elif "research" in prompt or "search" in prompt:
                return "fetch"
            else:
                return "sequential-thinking"
        
        return "This is a demonstration of the enhanced collaborative agent with improved tool handling, retry logic, and better user feedback."
    
    def generate_chat(self, messages, **kwargs):
        return "I'm here to help demonstrate the enhanced agent capabilities."
    
    def get_capabilities(self):
        return {"text_generation": True, "chat": True}


def demo_enhanced_features():
    """Demonstrate the enhanced collaborative agent features."""
    print("🚀 Enhanced Collaborative Agent Demonstration")
    print("=" * 60)
    
    # Initialize MCP Manager
    print("🔧 Setting up MCP tools...")
    config = {'enabled': True}
    mcp_manager = MCPManager(config)
    success = mcp_manager.initialize_tools()
    
    if not success:
        print("❌ Failed to initialize MCP tools")
        return False
    
    # Set up agent with verbose mode to show enhancements
    llm_provider = MockLLMProvider()
    agent = CollaborativeAgent(
        llm_provider=llm_provider,
        mcp_manager=mcp_manager,
        project_dir=".",
        config={"verbose": False}  # Set to True for detailed debugging
    )
    
    print(f"✅ Agent initialized with {len(mcp_manager.get_available_tools())} MCP tools")
    
    # Start session
    welcome = agent.start_session()
    print("\n" + "="*50)
    print("SESSION STARTED")
    print("="*50)
    print(welcome)
    
    # Demo scenarios to show enhanced features
    demo_scenarios = [
        {
            "name": "🕐 Basic Working Tool",
            "message": "What time is it?",
            "description": "Demonstrates successful tool usage with timing feedback"
        },
        {
            "name": "🧠 Analysis with Sequential Thinking", 
            "message": "Can you analyze this step by step: How should I structure a Python web API?",
            "description": "Shows multi-step reasoning tool with progress indicators"
        },
        {
            "name": "📁 Filesystem Access (May Fail)",
            "message": "What files are in this directory?",
            "description": "Demonstrates retry logic and graceful failure handling"
        },
        {
            "name": "🔍 Research Query",
            "message": "Research the latest Python web frameworks",
            "description": "Shows web research tool with meaningful URLs"
        },
        {
            "name": "📚 Documentation Lookup (May Timeout)",
            "message": "Look up FastAPI documentation",
            "description": "Demonstrates timeout handling and cooldown management"
        }
    ]
    
    for i, scenario in enumerate(demo_scenarios, 1):
        print(f"\n" + "="*60)
        print(f"DEMO {i}/5: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print("="*60)
        print(f"👤 User: {scenario['message']}")
        print(f"🤖 Agent: ", end="", flush=True)
        
        # Show typing indicator
        for _ in range(3):
            print(".", end="", flush=True)
            time.sleep(0.3)
        print()
        
        # Get agent response
        response = agent.send_message(scenario['message'])
        print(f"\n{response}")
        
        # Show current tool status after each interaction
        status = agent.get_status()
        if status["mcp_tools"]["in_cooldown"]:
            print(f"\n⚠️  Tools in cooldown: {', '.join(status['mcp_tools']['in_cooldown'])}")
        
        if i < len(demo_scenarios):
            print(f"\n⏳ Waiting 2 seconds before next demo...")
            time.sleep(2)
    
    # Demonstrate tool health refresh feature
    print(f"\n" + "="*60)
    print("🔄 TOOL HEALTH REFRESH DEMONSTRATION")
    print("="*60)
    
    refresh_result = agent.refresh_tool_health()
    print(refresh_result)
    
    # Show final status
    print(f"\n" + "="*60)
    print("📊 FINAL AGENT STATUS")
    print("="*60)
    
    final_status = agent.get_status()
    print(f"Session ID: {final_status['session_id']}")
    print(f"Conversation length: {final_status['conversation_length']} messages")
    
    tools_info = final_status['mcp_tools']
    print(f"\nTool Status:")
    print(f"  • Total available: {len(tools_info['total_available'])}")
    print(f"  • Currently working: {len(tools_info['currently_working'])}")
    print(f"  • In cooldown: {len(tools_info['in_cooldown'])}")
    
    if tools_info['retry_summary'] != "All tools healthy":
        print(f"\nRetry Summary: {tools_info['retry_summary']}")
    else:
        print(f"\n✅ All tools are healthy!")
    
    # End session
    print(f"\n" + "="*60)
    print("SESSION ENDING")
    print("="*60)
    
    farewell = agent.stop_session()
    print(farewell)
    
    return True


def main():
    """Run the enhanced collaborative agent demonstration."""
    try:
        success = demo_enhanced_features()
        return success
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


if __name__ == "__main__":
    try:
        success = main()
        print(f"\n{'✅ Demo completed successfully!' if success else '❌ Demo had issues'}")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n👋 Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Demo crashed: {e}")
        sys.exit(1) 