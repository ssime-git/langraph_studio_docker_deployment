# 🚀 Démarrage Rapide - LangGraph Docker Stack

## 1️⃣ Configuration (2 minutes)

### Étape 1: Configurer votre clé API

Copiez le fichier exemple et ajoutez votre clé API:

```bash
cp .env.example .env
```

Éditez `.env` et remplacez `sk-...` par votre vraie clé:
```
OPENAI_API_KEY=sk-proj-xxxxx
```

## 2️⃣ Lancement (30 secondes)

### Option A: Avec le script (recommandé)
```bash
chmod +x start.sh
./start.sh
```

### Option B: Avec Docker Compose directement
```bash
docker-compose up -d
```

## 3️⃣ Accès aux interfaces

Après environ 30 secondes, accédez à :

- 🎨 **Interface Studio Local**: http://localhost:3000
- 🔧 **API LangGraph**: http://localhost:8123
- 📚 **Documentation API**: http://localhost:8123/docs
- 🌐 **Via Nginx Proxy**: http://localhost

## 4️⃣ Premier Test

1. Ouvrez http://localhost:3000
2. Cliquez sur "+ Nouvel Agent"
3. Nommez-le "test"
4. Cliquez sur "💾 Sauvegarder"
5. Allez dans l'onglet "Test"
6. Cliquez sur "▶️ Tester"

## 📊 Vérification du statut

```bash
# Voir l'état des services
docker-compose ps

# Voir les logs
docker-compose logs -f
```

## 🛑 Arrêt

```bash
docker-compose down
```

## ⚠️ Problèmes courants

### "Cannot connect to Docker daemon"
→ Assurez-vous que Docker Desktop est lancé

### "Port already in use"
→ Un service utilise déjà le port. Changez les ports dans docker-compose.yml

### "Invalid API key"
→ Vérifiez votre clé API dans le fichier .env

## 🎯 Prochaines étapes

1. Créez votre premier agent personnalisé
2. Explorez l'API avec la documentation interactive
3. Connectez LangGraph Studio officiel si besoin

---

💡 **Astuce**: Gardez une fenêtre terminal ouverte avec `docker-compose logs -f` pour voir les logs en temps réel.
