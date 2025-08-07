#!/bin/bash

echo "🧪 Test de l'API LangGraph"
echo "=========================="
echo ""

# Test de santé de l'API
echo "1. Test de santé..."
curl -s http://localhost:8123/health || echo "❌ API non accessible"
echo ""

# Test de l'endpoint des assistants
echo "2. Liste des assistants..."
curl -s http://localhost:8123/assistants | python3 -m json.tool || echo "❌ Impossible de lister les assistants"
echo ""

# Test d'exécution simple
echo "3. Test d'exécution..."
curl -X POST http://localhost:8123/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "chatbot",
    "input": {
      "messages": [
        {"role": "human", "content": "Dis bonjour!"}
      ]
    },
    "stream_mode": "messages"
  }' || echo "❌ Erreur d'exécution"

echo ""
echo "✅ Tests terminés"
