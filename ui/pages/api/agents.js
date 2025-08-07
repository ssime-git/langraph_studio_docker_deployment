import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  const agentsDir = '/app/agents';
  
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
      
      res.status(200).json({ success: true, message: 'Agent saved' });
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
      return res.status(200).json({ success: true, message: 'Agent deleted' });
    } catch (error) {
      console.error('Error deleting agent:', error);
      res.status(500).json({ error: error.message });
    }
  }
  else {
    res.status(405).json({ error: 'Method not allowed' });
  }
}
