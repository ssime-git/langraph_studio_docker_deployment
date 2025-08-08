import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  const agentsDir = '/app/agents';
  const rootConfigPath = '/app/langgraph.json';

  const upsertRootConfig = (name) => {
    try {
      // Ensure parent dir exists (should be /app mounted)
      const dir = path.dirname(rootConfigPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      let rootCfg = { graphs: {} };
      if (fs.existsSync(rootConfigPath)) {
        const raw = fs.readFileSync(rootConfigPath, 'utf8');
        rootCfg = raw ? JSON.parse(raw) : { graphs: {} };
      }
      if (!rootCfg.graphs) rootCfg.graphs = {};
      rootCfg.graphs[name] = `./agents/${name}/agent.py:app`;
      fs.writeFileSync(rootConfigPath, JSON.stringify(rootCfg, null, 2));
      return { ok: true, rootCfg };
    } catch (e) {
      console.error('Failed to update langgraph.json:', e);
      return { ok: false, error: e?.message || String(e) };
    }
  };

  const removeFromRootConfig = (name) => {
    try {
      if (!fs.existsSync(rootConfigPath)) return;
      const rootCfg = JSON.parse(fs.readFileSync(rootConfigPath, 'utf8'));
      if (rootCfg.graphs && rootCfg.graphs[name]) {
        delete rootCfg.graphs[name];
        fs.writeFileSync(rootConfigPath, JSON.stringify(rootCfg, null, 2));
      }
    } catch (e) {
      console.error('Failed to update langgraph.json:', e);
    }
  };
  
  if (req.method === 'GET') {
    // Liste tous les agents
    try {
      if (!fs.existsSync(agentsDir)) {
        fs.mkdirSync(agentsDir, { recursive: true });
      }
      
      const agents = fs.readdirSync(agentsDir)
        .filter(file => fs.statSync(path.join(agentsDir, file)).isDirectory())
        .map(name => {
          const agentPath = path.join(agentsDir, name);
          let code = '';
          let config = '{}';
          
          try {
            if (fs.existsSync(path.join(agentPath, 'agent.py'))) {
              code = fs.readFileSync(path.join(agentPath, 'agent.py'), 'utf8');
            }
            if (fs.existsSync(path.join(agentPath, 'langgraph.json'))) {
              config = fs.readFileSync(path.join(agentPath, 'langgraph.json'), 'utf8');
            }
          } catch (err) {
            console.error(`Error reading agent ${name}:`, err);
          }
          
          return {
            name,
            code,
            config,
            path: agentPath
          };
        });
      
      res.status(200).json(agents);
    } catch (error) {
      console.error('Error listing agents:', error);
      res.status(500).json({ error: error.message });
    }
  } 
  else if (req.method === 'POST') {
    // Crée ou met à jour un agent
    try {
      const { name, code, config } = req.body;
      
      if (!name) {
        return res.status(400).json({ error: 'Agent name is required' });
      }
      
      const agentDir = path.join(agentsDir, name);
      
      if (!fs.existsSync(agentDir)) {
        fs.mkdirSync(agentDir, { recursive: true });
      }
      
      fs.writeFileSync(path.join(agentDir, 'agent.py'), code || '');
      fs.writeFileSync(path.join(agentDir, 'langgraph.json'), config || '{}');
      // Register into root langgraph.json so the API can discover it
      const result = upsertRootConfig(name);
      if (!result.ok) {
        return res.status(500).json({ success: false, message: 'Agent saved but failed to register in root langraph.json', error: result.error });
      }
      // Echo back updated root config for observability
      return res.status(200).json({ success: true, message: 'Agent saved and registered.', rootConfig: result.rootCfg });
    } catch (error) {
      console.error('Error saving agent:', error);
      res.status(500).json({ error: error.message });
    }
  }
  else if (req.method === 'DELETE') {
    // Supprime un agent (dossier entier)
    try {
      const { name } = req.query;
      if (!name || typeof name !== 'string') {
        return res.status(400).json({ error: 'Agent name is required' });
      }
      const agentDir = path.join(agentsDir, name);
      if (!fs.existsSync(agentDir)) {
        return res.status(404).json({ error: 'Agent not found' });
      }
      // rm récursif (Node >=14.14)
      fs.rmSync(agentDir, { recursive: true, force: true });
      removeFromRootConfig(name);
      return res.status(200).json({ success: true, message: 'Agent deleted and unregistered. Restart API to apply.' });
    } catch (error) {
      console.error('Error deleting agent:', error);
      res.status(500).json({ error: error.message });
    }
  }
  else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
