import asyncio
import os
import sys
import urllib.request
import base64
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# Set API keys and force NANO to use flash for now to ensure it works
os.environ["GEMINI_API_KEY"] = "AIzaSyDDsKcBLf2oK_1VWfWT5ugTtpA6m5I_NC0"
os.environ["GEMINI_MODEL_NANO"] = "gemini-2.0-flash" 
# Ensure Diagnostic Agent uses working models too
os.environ["GEMINI_MODEL_MED"] = "gemini-2.0-flash" 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.diagnostic.agent import DiagnosticAgent
from app.agents.visualization.agent import VisualizationAgent

async def main():
    print("Downloading a real sample chest X-Ray image...")
    # A standard public domain chest X-ray image from Wikimedia
    img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c8/Chest_Xray_PA_3-8-2010.png/500px-Chest_Xray_PA_3-8-2010.png"
    img_path = "sample_xray.png"
    
    req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(img_path, 'wb') as out_file:
        out_file.write(response.read())
        
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    
    # We can pass raw bytes to the agent, but let's base64 encode it for safety if needed.
    # The agent also accepts raw bytes.
    print(f"Downloaded image size: {len(img_bytes)} bytes")
    
    print("\n==================================")
    print("STEP 1: RUNNING DIAGNOSTIC AGENT")
    print("==================================")
    
    diag_agent = DiagnosticAgent()
    try:
        diag_response = await diag_agent.invoke(
            session_id="real_test_session_1",
            query="Analyze this chest X-ray please. 45-year-old male with persistent cough.",
            context=[],
            image_data=img_bytes,
            image_mime_type="image/png"
        )
        report_text = diag_response.content
        print("\n--- RAW MEDICAL REPORT ---")
        print(report_text)
    except Exception as e:
        print(f"Error in Diagnostic Agent: {e}")
        return

    print("\n==================================")
    print("STEP 2: RUNNING VISUALIZATION AGENT")
    print("==================================")
    
    vis_agent = VisualizationAgent()
    try:
        vis_response = await vis_agent.invoke(
            session_id="real_test_session_1",
            query="Can you break down this report for me into a tutorial with images?",
            context=[],
            report_text=report_text
        )
        
        print("\n--- VISUALIZATION TUTORIAL ---")
        print(vis_response.content)
        
    except Exception as e:
        print(f"Error in Visualization Agent: {e}")
        return

    # Cleanup
    if os.path.exists(img_path):
        os.remove(img_path)

if __name__ == "__main__":
    asyncio.run(main())
