import asyncio
import os
import sys

# Set environment before importing app modules
os.environ["GEMINI_API_KEY"] = "AIzaSyDDsKcBLf2oK_1VWfWT5ugTtpA6m5I_NC0"
# We will use the default Nano model name for now, but we can override it if the API rejects 'nano-banana'
os.environ["GEMINI_MODEL_NANO"] = "gemini-2.0-flash" 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.visualization.agent import VisualizationAgent

async def main():
    agent = VisualizationAgent()
    
    report_text = """
    DIAGNOSTIC REPORT
    Patient: John Doe, Age 42
    Modality: Chest X-Ray
    Findings: There is a 2cm radiopacity in the right lower lobe, suspicious for consolidation or a mass. The cardiac silhouette is within normal limits. No pleural effusion.
    Conclusion: Right lower lobe opacity. Recommend follow-up CT scan.
    """
    
    query = "I don't understand what a 2cm radiopacity means. Is it bad? Can you explain this report to me simply?"
    
    print("Testing VisualizationAgent ...")
    
    try:
        response = await agent.invoke(
            session_id="test_session_123",
            query=query,
            context=[],
            report_text=report_text
        )
        
        print("\n=== AGENT RESPONSE ===")
        print(response.content)
        print("\n=== METADATA ===")
        import json
        print(json.dumps(response.metadata, indent=2))
        
    except Exception as e:
        print(f"Error invoking agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
