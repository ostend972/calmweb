# CalmWeb - Filtre de contenu intelligent

## Description
CalmWeb est un système de filtrage de contenu transparent qui protège votre navigation en bloquant automatiquement les domaines malveillants. Il fonctionne comme un proxy local avec une interface web moderne React.

## Caractéristiques principales
- ✅ Proxy transparent sur port 8080
- ✅ Interface web moderne (React/TypeScript) sur port 8081
- ✅ Dashboard React intégré dans l'exécutable
- ✅ Filtrage automatique des domaines malveillants
- ✅ Statistiques de navigation en temps réel
- ✅ Configuration avancée par domaine
- ✅ Icône système tray avec contrôles
- ✅ Démarrage automatique avec Windows
- ✅ Privilèges administrateur intégrés
- ✅ Exécutable portable (24MB, 100% autonome)

## Installation et utilisation

### 1. Compilation de l'exécutable
```bash
# Installation des dépendances Python
pip install -r requirements.txt

# Compilation du dashboard React
cd calmweb-dashboard
npm install
npm run build
cd ..

# Génération de l'exécutable avec PyInstaller
python -m PyInstaller CalmWeb_Final.spec
```

### 2. Déploiement
L'exécutable généré (`dist/CalmWeb.exe`) est **100% portable** et contient :
- ✅ Toutes les dépendances Python incluses
- ✅ Dashboard React moderne intégré
- ✅ Privilèges administrateur automatiques
- ✅ Configuration pour démarrage automatique
- ✅ Interface complète intégrée (24MB total)

**Installation sur un autre PC** : Copiez simplement `CalmWeb.exe` et lancez-le !

### 3. Utilisation
- **Interface web** : http://127.0.0.1:8081 (dashboard React moderne)
- **Contrôle système** : Icône dans la zone de notification (system tray)
- **Configuration** : Via l'interface web ou fichier `custom.cfg`

## Architecture

### Backend (Python)
- **Proxy Server** : Serveur HTTP/HTTPS transparent
- **Blocklist Manager** : Gestionnaire de listes de domaines malveillants
- **Dashboard API** : API REST pour l'interface web
- **Configuration** : Gestionnaire de configuration centralisé
- **Statistics** : Suivi des statistiques à vie
- **System Tray** : Interface système avec pystray

### Frontend (React/TypeScript)
- **Dashboard** : Vue d'ensemble et statistiques en temps réel
- **Configuration** : Gestion des paramètres de filtrage
- **Logs** : Visualisation des journaux de blocage
- **Statistics** : Statistiques détaillées avec graphiques
- **Interface moderne** : Design responsive avec Tailwind CSS

### Sécurité
- ✅ Accès local uniquement (127.0.0.1)
- ✅ Validation stricte des requêtes
- ✅ Aucune donnée transmise vers l'extérieur
- ✅ Configuration sécurisée par défaut
- ✅ Gestion d'erreurs robuste (pas de crash stdin)

## Structure du projet

```
CalmWeb_Clean/
├── standalone_main.py          # Point d'entrée principal
├── calmweb/                    # Module principal Python
│   ├── proxy/                  # Serveur proxy HTTP/HTTPS
│   ├── web/                    # Serveur dashboard et API
│   ├── config/                 # Gestionnaire de configuration
│   ├── ui/                     # Interface système tray
│   └── stats/                  # Statistiques et logs
├── calmweb-dashboard/          # Interface React/TypeScript
│   ├── src/                    # Code source React
│   ├── dist/                   # Build de production (intégré)
│   └── package.json            # Dépendances Node.js
├── CalmWeb_Final.spec          # Configuration PyInstaller
├── requirements.txt            # Dépendances Python
└── dist/CalmWeb.exe           # Exécutable final (24MB)
```

## Configuration

### Fichier `custom.cfg`
Le fichier de configuration permet de personnaliser :
- Domaines bloqués/autorisés manuellement
- URLs des listes de blocage externes
- Paramètres de filtrage avancés
- Options de proxy et d'interface

### Variables d'environnement
- `APPDATA/CalmWeb/` : Dossier de configuration utilisateur
- Port 8080 : Proxy transparent
- Port 8081 : Interface web dashboard

## Développement

### Prérequis
- Python 3.12+
- Node.js 18+
- Windows (développé et testé sur Windows 11)

### Dashboard React
```bash
cd calmweb-dashboard
npm install          # Installation des dépendances
npm run dev          # Serveur de développement (port 3000)
npm run build        # Build de production
```

### Tests
```bash
# Test de l'application Python
python standalone_main.py

# Test du dashboard seul
cd calmweb-dashboard && npm run dev
```

## Ports utilisés
- **8080** : Proxy HTTP/HTTPS (transparent)
- **8081** : Interface web dashboard React

## Compatibilité
- ✅ Windows 7/8/10/11 (x64)
- ✅ Privilèges administrateur requis (auto-demandés)
- ✅ Visual C++ Redistributables (généralement présents)
- ✅ .NET Framework recommandé

## Support et bugs
- Rapportez les bugs via les issues GitHub
- L'application génère des logs détaillés pour le débogage
- Configuration sauvegardée automatiquement

## Licence
Projet open source - voir le fichier LICENSE pour les détails.