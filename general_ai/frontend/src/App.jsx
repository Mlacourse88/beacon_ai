import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FaJedi, FaRobot, FaGamepad, FaSpaceShuttle } from 'react-icons/fa'

const API_URL = "http://localhost:5000/api";

function App() {
  const [view, setView] = useState("squad"); // squad, comms, ops
  const [squadData, setSquadData] = useState([]);
  const [chatHistory, setChatHistory] = useState([{role: 'system', content: 'BEACON OS ONLINE. CHANNEL SECURE.'}]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Load Status on Boot
  useEffect(() => {
    fetch(`${API_URL}/status`)
      .then(res => res.json())
      .then(data => setSquadData(data))
      .catch(err => console.error("BEACON LINK OFFLINE", err));
  }, []);

  const sendMessage = async () => {
    if (!input) return;
    const msg = input;
    setInput("");
    setChatHistory(prev => [...prev, {role: 'user', content: msg}]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ prompt: msg })
      });
      const data = await res.json();
      setChatHistory(prev => [...prev, {role: 'ai', content: data.response}]);
    } catch (e) {
      setChatHistory(prev => [...prev, {role: 'error', content: 'TRANSMISSION FAILED'}]);
    }
    setLoading(false);
  };

  return (
    <div className="h-screen w-screen flex flex-col text-cyan-400 overflow-hidden relative">
      <div className="scanlines"></div>
      <div className="starfield"></div>

      {/* HEADER */}
      <header className="p-4 border-b border-cyan-900 bg-black/80 backdrop-blur-md flex justify-between items-center z-20">
        <h1 className="text-xl font-bold tracking-widest">BEACON<span className="text-white">OS</span></h1>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>ONLINE</span>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 overflow-y-auto p-4 pb-24 z-10">
        <AnimatePresence mode="wait">
          
          {/* VIEW: SQUAD */}
          {view === 'squad' && (
            <motion.div 
              key="squad"
              initial={{opacity: 0, x: -20}} 
              animate={{opacity: 1, x: 0}}
              exit={{opacity: 0, x: 20}}
              className="space-y-4"
            >
              {squadData.map((agent, i) => (
                <div key={i} className="holo-card p-4">
                  <div className="flex justify-between items-center mb-2">
                    <h2 className="text-lg font-bold text-white">{agent.name.toUpperCase()}</h2>
                    <span className="text-xs border border-cyan-500 px-2 py-0.5 rounded">{agent.role}</span>
                  </div>
                  <div className="flex justify-between text-xs mb-1 opacity-70">
                    <span>LVL {agent.level}</span>
                    <span>{agent.xp} / {agent.threshold} XP</span>
                  </div>
                  <div className="w-full h-2 bg-gray-900 rounded-full overflow-hidden border border-gray-700">
                    <div 
                      className="h-full bg-cyan-400 shadow-[0_0_10px_cyan]" 
                      style={{width: `${agent.progress}%`}}
                    ></div>
                  </div>
                </div>
              ))}
            </motion.div>
          )}

          {/* VIEW: COMMS */}
          {view === 'comms' && (
            <motion.div 
              key="comms"
              initial={{opacity: 0}} 
              animate={{opacity: 1}}
              className="h-full flex flex-col"
            >
              <div className="flex-1 overflow-y-auto space-y-3 mb-4">
                {chatHistory.map((msg, i) => (
                  <div key={i} className={`p-3 rounded-lg border max-w-[85%] text-sm ${
                    msg.role === 'user' 
                      ? 'ml-auto bg-cyan-900/20 border-cyan-500 text-right' 
                      : 'mr-auto bg-gray-900/50 border-gray-700'
                  }`}>
                    {msg.content}
                  </div>
                ))}
                {loading && <div className="text-xs animate-pulse text-cyan-500">DECRYPTING...</div>}
              </div>
              
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="TRANSMIT DATA..."
                  className="flex-1 bg-black/50 border border-cyan-700 p-3 rounded text-white outline-none focus:border-cyan-400 font-mono"
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                />
                <button onClick={sendMessage} className="bg-cyan-900/50 border border-cyan-500 px-4 rounded text-cyan-400 font-bold hover:bg-cyan-500 hover:text-black transition-all">
                  SEND
                </button>
              </div>
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      {/* GALACTIC NAV BAR */}
      <nav className="fixed bottom-0 w-full bg-black/90 border-t border-cyan-900 p-4 flex justify-around z-30 pb-8">
        <NavButton icon={<FaJedi />} label="SQUAD" active={view === 'squad'} onClick={() => setView('squad')} />
        <NavButton icon={<FaRobot />} label="COMMS" active={view === 'comms'} onClick={() => setView('comms')} />
        <NavButton icon={<FaSpaceShuttle />} label="OPS" active={view === 'ops'} onClick={() => setView('ops')} />
      </nav>
    </div>
  )
}

function NavButton({icon, label, active, onClick}) {
  return (
    <button 
      onClick={onClick}
      className={`flex flex-col items-center gap-1 transition-all ${active ? 'text-cyan-400 scale-110 drop-shadow-[0_0_5px_cyan]' : 'text-gray-600'}`}
    >
      <div className="text-xl">{icon}</div>
      <span className="text-[10px] font-bold tracking-widest">{label}</span>
    </button>
  )
}

export default App
