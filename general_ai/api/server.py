"""
BEACON API Server
-----------------
Acts as the bridge between the React Frontend (Star Wars UI) and the Python Backend logic.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import asyncio
from pathlib import Path
import nest_asyncio

# Apply Async Fix
nest_asyncio.apply()

# Path Setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import BEACON Core
from beacon_ai.main_agent import BeaconAgent
from general_ai.scripts.gamification_engine import GamificationEngine

app = Flask(__name__)
CORS(app)  # Allow React to communicate

# Initialize Systems
print(">>> INITIALIZING BEACON CORE...")
agent = BeaconAgent()
# Run async init in a sync way for startup
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(agent.initialize())

game_engine = GamificationEngine()

def run_async(coro):
    """Helper to run async agent methods inside Flask."""
    return loop.run_until_complete(coro)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Returns LifeRPG Stats for the Squad View."""
    users = ["Micheal", "Hunter", "Fiona"]
    squad_data = []
    for u in users:
        stats = game_engine.get_user_stats(u)
        # Calculate progress
        lvl = stats.get("level", 1)
        xp = stats.get("xp", 0)
        threshold = game_engine.calculate_level_threshold(lvl)
        
        squad_data.append({
            "name": u,
            "role": stats.get("role", "Agent"),
            "level": lvl,
            "xp": xp,
            "threshold": threshold,
            "progress": (xp / threshold) * 100 if threshold else 0
        })
    return jsonify(squad_data)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Sends prompt to Beacon Agent."""
    data = request.json
    prompt = data.get('prompt')
    mode = data.get('mode', 'Auto') # 'Force Biblical', 'Force General', 'Auto'
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        response = run_async(agent.process_query(prompt, force_mode=mode))
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/xp', methods=['POST'])
def award_xp():
    """Awards XP from the frontend."""
    data = request.json
    user = data.get('user')
    amount = int(data.get('amount', 0))
    reason = data.get('reason', 'Manual Award')
    
    msg = game_engine.award_xp(user, amount, reason)
    return jsonify({"message": msg})

if __name__ == '__main__':
    print(">>> BEACON API OPERATIONAL ON PORT 5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
