"use client";
import React, { useState, useRef, useEffect } from 'react';
import { Send, MapPin, Sparkles, Building2, BedDouble, Loader2, Home } from 'lucide-react';

const fetchWithRetry = async (url, options, retries = 5) => {
  let delay = 1000;
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, options);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      return await res.json();
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= 2;
    }
  }
};

export default function App() {
  const [messages, setMessages] = useState([{ role: "ai", content: "Welcome to Propulse AI. Describe your ideal property, budget, or preferred location, and I'll find the perfect match." }]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [displayedProperties, setDisplayedProperties] = useState([]);
  const messagesEndRef = useRef(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isLoading]);

  const handleAIQuery = async (userQuery) => {
    setIsLoading(true);
    setMessages(prev => [...prev, { role: "user", content: userQuery }]);
    setInput("");

    try {
      // Direct all intelligence through our strict backend controller
      const res = await fetchWithRetry("/api/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userQuery })
      });
      
      setMessages(prev => [...prev, { role: "ai", content: res.reply }]);
      if (res.matches && res.matches.length > 0) {
        setDisplayedProperties(res.matches);
      } else {
        setDisplayedProperties([]);
      }
    } catch (error) {
      console.error("Agent Error:", error);
      setMessages(prev => [...prev, { role: "ai", content: "System error. Please ensure the Python backend is running." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = () => { if (input.trim()) handleAIQuery(input.trim()); };
  const handleKeyDown = (e) => { if (e.key === 'Enter') handleSend(); };

  const QuickPill = ({ text, query }) => (
    <button onClick={() => handleAIQuery(query)} className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-xs text-zinc-300 transition-colors whitespace-nowrap">
      {text}
    </button>
  );

  return (
    <div className="flex h-screen w-full bg-[#0a0a0a] text-zinc-200 font-sans overflow-hidden selection:bg-blue-500/30">
      <div className="absolute inset-0 z-0 pointer-events-none opacity-20" style={{ backgroundImage: 'linear-gradient(to right, #ffffff 1px, transparent 1px), linear-gradient(to bottom, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }}></div>

      <section className="w-full md:w-1/3 max-w-md h-full border-r border-white/10 bg-black/60 backdrop-blur-2xl flex flex-col relative z-10 shadow-2xl">
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <span className="relative flex h-3 w-3"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span></span>
              Propulse AI
            </h1>
            <p className="text-xs text-zinc-500 mt-1 uppercase tracking-widest">Real estate decisions, powered by intelligence.</p>
          </div>
          <button onClick={() => {setDisplayedProperties([]); setMessages([{ role: "ai", content: "Portfolio reset. What are you looking for?" }]);}} className="p-2 hover:bg-white/10 rounded-lg transition-colors text-zinc-400"><Home size={18} /></button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed ${msg.role === "user" ? "bg-blue-600/20 text-blue-50 border border-blue-500/30 rounded-tr-sm" : "bg-white/5 text-zinc-300 border border-white/10 rounded-tl-sm shadow-lg"}`}>
                {msg.role === "ai" && i > 0 && <Sparkles size={14} className="text-blue-400 mb-2 inline-block mr-2" />}
                {msg.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-[85%] rounded-2xl p-4 bg-white/5 border border-white/10 rounded-tl-sm flex items-center gap-3">
                <Loader2 size={16} className="text-blue-500 animate-spin" />
                <span className="text-xs text-zinc-400">Agent is filtering properties...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="p-6 pt-2 bg-gradient-to-t from-black via-black to-transparent">
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2 scrollbar-none">
            <QuickPill text="Under 50L" query="Show me options under 50 Lakhs" />
            <QuickPill text="Premium 3BHK" query="I want a premium 3BHK" />
          </div>
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
            <div className="relative flex items-center bg-[#121212] rounded-xl border border-white/10">
              <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="E.g., 2BHK under 50L..." className="w-full bg-transparent px-4 py-4 text-sm text-white placeholder-zinc-600 outline-none rounded-xl" disabled={isLoading} />
              <button onClick={handleSend} disabled={isLoading || !input.trim()} className="absolute right-2 p-2 bg-white/10 hover:bg-blue-600 rounded-lg transition-all text-white disabled:opacity-50 disabled:hover:bg-white/10">
                <Send size={16} className={input.trim() && !isLoading ? "text-white" : "text-zinc-500"} />
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="flex-1 h-full overflow-y-auto p-6 md:p-10 relative z-10 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
        <div className="max-w-5xl mx-auto">
          <div className="mb-8 flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-white">Curated Collection</h2>
            <span className="text-sm px-3 py-1 bg-white/10 rounded-full text-zinc-300">{displayedProperties.length} {displayedProperties.length === 1 ? 'Match' : 'Matches'}</span>
          </div>

          {displayedProperties.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-3xl bg-white/5">
              <Building2 size={48} className="text-zinc-700 mb-4" />
              <p className="text-zinc-400 text-lg">Waiting for your criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-2 gap-6 pb-20">
              {displayedProperties.map((prop) => (
                <div key={prop.id} className="group flex flex-col bg-[#121212] border border-white/10 rounded-2xl overflow-hidden hover:border-white/20 transition-all duration-300 hover:shadow-2xl hover:shadow-blue-900/20">
                  <div className={`relative h-56 w-full bg-gradient-to-br ${prop.gradient} overflow-hidden`}>
                    <div className="absolute inset-0 opacity-20 mix-blend-overlay" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '24px 24px' }}></div>
                    <div className="absolute inset-0 bg-gradient-to-t from-[#121212] to-transparent"></div>
                    <div className="absolute top-4 right-4 bg-black/60 backdrop-blur-md px-4 py-1.5 rounded-full text-sm font-bold text-white border border-white/10 shadow-lg">{prop.formatted_price}</div>
                  </div>
                  <div className="p-6 flex-1 flex flex-col">
                    <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition-colors mb-2">{prop.title}</h3>
                    <div className="flex items-center gap-4 text-xs text-zinc-400 mb-5">
                      <span className="flex items-center gap-1"><MapPin size={14} /> {prop.location}</span>
                      <span className="flex items-center gap-1"><BedDouble size={14} /> {prop.bhk} BHK</span>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-6">
                      {prop.amenities.map((amenity, i) => <span key={i} className="px-2.5 py-1 bg-white/5 border border-white/5 rounded-md text-[11px] text-zinc-300 font-medium">{amenity}</span>)}
                    </div>
                    <div className="mt-auto bg-blue-900/10 border border-blue-500/20 rounded-xl p-4 relative overflow-hidden group-hover:bg-blue-900/20 transition-colors">
                      <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                      <div className="flex items-start gap-3">
                        <Sparkles size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="text-[10px] uppercase tracking-wider text-blue-400 font-bold block mb-1">Agent Insight</span>
                          <p className="text-sm text-blue-100/80 leading-relaxed font-medium">{prop.ai_insight}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}