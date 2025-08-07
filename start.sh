#!/bin/bash

# Script de démarrage rapide pour LangGraph Stack
set -e

echo "🚀 LangGraph Docker Stack - Démarrage"
echo "====================================="

# Vérification de Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Installez Docker d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé."
    exit 1
fi

# Détection de la commande docker-compose
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Vérification du fichier .env
if [ ! -f .env ]; then
    echo "⚠️  Fichier .env non trouvé."
    echo "📝 Veuillez créer un fichier .env avec au minimum OPENAI_API_KEY"
    echo ""
    echo "Exemple de contenu .env:"
    echo "OPENAI_API_KEY=sk-..."
    echo ""
    exit 1
fi

# Création des dossiers nécessaires
echo "📁 Création de la structure des dossiers..."
mkdir -p agents/example
mkdir -p data

# Nettoyage des containers existants
echo "🧹 Nettoyage des containers existants..."
$COMPOSE_CMD down 2>/dev/null || true

# Construction et démarrage
echo "🔨 Construction des images Docker..."
$COMPOSE_CMD build

echo "🎯 Démarrage des services..."
$COMPOSE_CMD up -d

# Attente que les services soient prêts
echo "⏳ Attente du démarrage des services (30 secondes)..."
sleep 30

# Vérification de l'état
echo "✅ Vérification de l'état des services..."
$COMPOSE_CMD ps

# Affichage des URLs
echo ""
echo "====================================="
echo "✨ LangGraph Stack est prêt!"
echo "====================================="
echo ""
echo "📍 Accès aux services:"
echo "   • Interface Studio Local: http://localhost"
echo "   • API LangGraph: http://localhost:8123"
echo "   • Documentation API: http://localhost:8123/docs"
echo ""
echo "🔗 Pour utiliser avec LangGraph Studio officiel:"
echo "   https://smith.langchain.com/studio/?baseUrl=http://localhost:8123"
echo ""
echo "📝 Commandes utiles:"
echo "   • Voir les logs: $COMPOSE_CMD logs -f"
echo "   • Arrêter: $COMPOSE_CMD down"
echo "   • Redémarrer: $COMPOSE_CMD restart"
echo "   • Nettoyer tout: $COMPOSE_CMD down -v"
echo ""
echo "💡 Astuce: Ouvrez http://localhost pour commencer à créer des agents!"
