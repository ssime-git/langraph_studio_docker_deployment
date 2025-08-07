#!/bin/bash

echo "📦 Installation des dépendances de l'interface web..."
echo ""

cd ui

if [ ! -f package-lock.json ]; then
    echo "Création du package-lock.json..."
    npm install
else
    echo "Installation à partir du package-lock.json existant..."
    npm ci
fi

echo ""
echo "✅ Dépendances installées!"
echo ""
echo "Pour lancer l'interface en mode développement:"
echo "  cd ui && npm run dev"
echo ""
echo "Pour builder pour la production:"
echo "  cd ui && npm run build"
