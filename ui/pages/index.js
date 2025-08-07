import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import axios from 'axios';

const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

export default function AgentStudio() {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [code, setCode] = useState('');
  const [config, setConfig] = useState('');
  const [logs, setLogs] = useState([]);
  const [testInput, setTestInput] = useState('{"messages": [{"role": "human", "content": "Hello!"}]}');
  const [testOutput, setTestOutput] = useState('');
  const [testEvents, setTestEvents] = useState([]);
  const [activeTab, setActiveTab] = useState('code');

  const agentTemplate = `from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

class State(TypedDict):
    messages: Annotated[list, add_messages]

def agent_node(state: State):
    """Nœud principal de l'agent"""
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# Construction du graphe
graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.set_entry_point("agent")
graph.add_edge("agent", END)

# Compilation
app = graph.compile()
`;

  const configTemplate = `{
  "graphs": {
    "agent": "./agent.py:app"
  },
  "env": ".env",
  "python_version": "3.12",
  "dependencies": ["langgraph", "langchain", "langchain-openai"]
}`;

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const response = await axios.get('/api/agents');
      setAgents(response.data);
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  const createNewAgent = () => {
    const name = prompt("Nom de l'agent:");
    if (name) {
      const newAgent = {
        name,
        code: agentTemplate,
        config: configTemplate,
        created: new Date().toISOString()
      };
      setAgents([...agents, newAgent]);
      setSelectedAgent(newAgent);
      setCode(agentTemplate);
      setConfig(configTemplate);
      // Save immediately with provided code/config to avoid async state lag
      saveAgent({ name, code: agentTemplate, config: configTemplate });
    }
  };

  const saveAgent = async (agent) => {
    try {
      await axios.post('/api/agents', {
        name: agent?.name || selectedAgent?.name,
        code: agent?.code ?? code,
        config: agent?.config ?? config
      });
      addLog(`Agent ${agent?.name || selectedAgent.name} sauvegardé`);
    } catch (error) {
      addLog(`Erreur: ${error.message}`, 'error');
    }
  };

  const deleteAgent = async () => {
    if (!selectedAgent?.name) return;
    if (!confirm(`Supprimer l'agent "${selectedAgent.name}" ?`)) return;
    try {
      await axios.delete(`/api/agents`, { params: { name: selectedAgent.name } });
      addLog(`Agent ${selectedAgent.name} supprimé`);
      // Remove from local state
      const updated = agents.filter(a => a.name !== selectedAgent.name);
      setAgents(updated);
      setSelectedAgent(null);
      setCode('');
      setConfig('');
    } catch (error) {
      addLog(`Erreur suppression: ${error.message}`, 'error');
    }
  };

  const parseSSEBlocks = (buffer) => {
    // Normalize CRLF to LF first
    const norm = buffer.replace(/\r\n/g, '\n');
    const parts = norm.split('\n\n');
    const complete = parts.slice(0, -1);
    const remainder = parts[parts.length - 1];
    return { complete, remainder };
  };

  const parseSSEEvent = (block) => {
    const lines = block.replace(/\r\n/g, '\n').split('\n');
    let event = 'message';
    let dataLines = [];
    for (const line of lines) {
      if (line.startsWith('event:')) event = line.slice(6).trim();
      if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
    }
    const data = dataLines.join('');
    let json = null;
    try { json = data ? JSON.parse(data) : null; } catch (_) {}
    return { event, raw: data, json };
  };

  const testAgent = async () => {
    setTestOutput('');
    setTestEvents([]);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8123';
      const resp = await fetch(`${apiUrl}/runs/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assistant_id: selectedAgent.name,
          input: JSON.parse(testInput),
          stream_mode: 'messages-tuple'
        })
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let events = [];
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const { complete, remainder } = parseSSEBlocks(buffer);
        buffer = remainder;
        for (const block of complete) {
          const evt = parseSSEEvent(block);
          events.push(evt);
        }
        setTestEvents([...events]);
      }
      // flush any remaining block after stream end
      if (buffer.trim()) {
        const evt = parseSSEEvent(buffer);
        events.push(evt);
      }
      setTestEvents([...events]);
      addLog(`Test exécuté avec succès`);
    } catch (error) {
      addLog(`Erreur de test: ${error.message}`, 'error');
      setTestOutput(`Erreur: ${error.message}`);
    }
  };

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, {
      time: new Date().toLocaleTimeString(),
      message,
      type
    }]);
  };

  // Lightweight collapsible JSON viewer (no extra deps)
  const JSONNode = ({ name, data, level = 0 }) => {
    const isObject = data && typeof data === 'object' && !Array.isArray(data);
    const isArray = Array.isArray(data);
    if (!isObject && !isArray) {
      return (
        <div className="pl-2"><span className="text-blue-300">{name !== undefined ? `${name}: ` : ''}</span><span className="text-gray-300">{JSON.stringify(data)}</span></div>
      );
    }
    const keys = isArray ? data.map((_, i) => i) : Object.keys(data);
    return (
      <details open={level < 1} className="ml-2">
        <summary className="cursor-pointer select-none text-yellow-300">
          {name !== undefined ? `${name}: ` : ''}{isArray ? `Array(${data.length})` : 'Object'}
        </summary>
        <div className="pl-4 border-l border-gray-700">
          {keys.map((k, i) => (
            <JSONNode key={i} name={k} data={isArray ? data[k] : data[k]} level={level + 1} />
          ))}
        </div>
      </details>
    );
  };

  const EventsViewer = ({ events }) => {
    if (!events?.length) return <div className="text-gray-500">Aucun résultat</div>;
    return (
      <div className="space-y-2">
        {events.map((e, idx) => (
          <div key={idx} className="bg-gray-800 p-2 rounded">
            <div className="text-xs text-purple-300 mb-1">event: {e.event}</div>
            {e.json ? (
              <JSONNode data={e.json} />
            ) : (
              <pre className="text-xs whitespace-pre-wrap">{e.raw}</pre>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="flex h-screen">
        <div className="w-64 bg-gray-800 p-4 overflow-y-auto">
          <h2 className="text-xl font-bold mb-4">Agents</h2>
          <button
            onClick={createNewAgent}
            className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded mb-4 transition-colors"
          >
            + Nouvel Agent
          </button>
          <div className="space-y-2">
            {agents.map((agent, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setSelectedAgent(agent);
                  setCode(agent.code);
                  setConfig(agent.config);
                }}
                className={`p-2 rounded cursor-pointer hover:bg-gray-700 transition-colors ${
                  selectedAgent?.name === agent.name ? 'bg-gray-700' : ''
                }`}
              >
                {agent.name}
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 flex flex-col">
          <div className="bg-gray-800 p-4 flex justify-between items-center border-b border-gray-700">
            <h1 className="text-2xl font-bold">
              LangGraph Studio Local
            </h1>
            {selectedAgent && (
              <div className="space-x-2">
                <button
                  onClick={() => saveAgent()}
                  className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded transition-colors"
                >
                  💾 Sauvegarder
                </button>
                <button
                  onClick={deleteAgent}
                  className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded transition-colors"
                >
                  🗑️ Supprimer
                </button>
                <button
                  onClick={testAgent}
                  className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded transition-colors"
                >
                  ▶️ Tester
                </button>
              </div>
            )}
          </div>

          {selectedAgent ? (
            <div className="flex-1 flex">
              <div className="flex-1 flex flex-col">
                <div className="bg-gray-700 p-2 flex space-x-2">
                  <button 
                    onClick={() => setActiveTab('code')}
                    className={`px-4 py-1 rounded transition-colors ${activeTab === 'code' ? 'bg-gray-600' : 'hover:bg-gray-600'}`}
                  >
                    Code
                  </button>
                  <button 
                    onClick={() => setActiveTab('config')}
                    className={`px-4 py-1 rounded transition-colors ${activeTab === 'config' ? 'bg-gray-600' : 'hover:bg-gray-600'}`}
                  >
                    Config
                  </button>
                  <button 
                    onClick={() => setActiveTab('test')}
                    className={`px-4 py-1 rounded transition-colors ${activeTab === 'test' ? 'bg-gray-600' : 'hover:bg-gray-600'}`}
                  >
                    Test
                  </button>
                </div>
                
                <div className="flex-1">
                  {activeTab === 'code' && (
                    <Editor
                      height="100%"
                      defaultLanguage="python"
                      theme="vs-dark"
                      value={code}
                      onChange={setCode}
                      options={{
                        minimap: { enabled: false },
                        fontSize: 14
                      }}
                    />
                  )}
                  {activeTab === 'config' && (
                    <Editor
                      height="100%"
                      defaultLanguage="json"
                      theme="vs-dark"
                      value={config}
                      onChange={setConfig}
                      options={{
                        minimap: { enabled: false },
                        fontSize: 14
                      }}
                    />
                  )}
                  {activeTab === 'test' && (
                    <div className="p-4">
                      <h3 className="font-bold mb-2">Test Input</h3>
                      <textarea
                        value={testInput}
                        onChange={(e) => setTestInput(e.target.value)}
                        className="w-full h-32 bg-gray-800 p-2 rounded mb-4 font-mono text-sm"
                        placeholder="JSON input..."
                      />
                      <button
                        onClick={testAgent}
                        className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded mb-4"
                      >
                        Exécuter Test
                      </button>
                      <h3 className="font-bold mb-2">Output</h3>
                      <div className="bg-gray-900 p-2 rounded text-xs overflow-auto h-64 border border-gray-700">
                        {testEvents.length ? <EventsViewer events={testEvents} /> : (testOutput || 'Aucun résultat')}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="w-96 bg-gray-800 flex flex-col border-l border-gray-700">
                <div className="flex-1 p-4 overflow-y-auto">
                  <h3 className="font-bold mb-2">Logs</h3>
                  <div className="space-y-1 text-xs font-mono">
                    {logs.map((log, idx) => (
                      <div key={idx} className={`${
                        log.type === 'error' ? 'text-red-400' : 'text-green-400'
                      }`}>
                        [{log.time}] {log.message}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <p className="text-2xl mb-4">👋 Bienvenue dans LangGraph Studio Local</p>
                <p>Sélectionnez ou créez un agent pour commencer</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
