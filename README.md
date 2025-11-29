# CyberCampus CTF — Plateforme Capture The Flag

Ce projet est une plateforme web de type **Capture The Flag (CTF)** permettant aux utilisateurs d'apprendre et de pratiquer différentes techniques de cybersécurité.  
La plateforme propose des challenges vulnérables isolés (SQLi, XSS, brute force, cryptographie simple, OSINT, etc.) et inclut un système de **soumission de flags**, un **scoreboard**, une **gestion des utilisateurs** et un **panneau d'administration**.

---

## 🎯 Objectif du projet

- Proposer un environnement d’apprentissage ludique autour des vulnérabilités courantes.
- Permettre aux joueurs de résoudre des défis variés et de soumettre des flags.
- Offrir une plateforme sécurisée avec des environnements vulnérables isolés via **Docker**.
- Fournir un tableau de bord, un classement dynamique, et une gestion simple des challenges.

---

## 🏗️ Fonctionnalités principales

### ✔️ Gestion des utilisateurs  
- Inscription / Connexion  
- Tableau de bord personnel  
- Suivi de la progression et des points  

### ✔️ Challenges interactifs  
Chaque challenge comprend :  
- un énoncé,  
- un environnement vulnérable,  
- un flag à récupérer (format `CTF{...}`).  

Challenges disponibles :
- **SQL Injection (SQLi)** — Challenge vulnérable simple  
- **XSS réfléchi** — Champ commentaire vulnérable  

### ✔️ Scoreboard  
- Classement global  
- Mise à jour automatique après chaque flag validé  

### ✔️ Administration  
- Gestion des challenges  
- Gestion des utilisateurs  
- Vue d’ensemble des flags soumis  

---

## 🗂️ Structure du projet

```
/core           → logique interne (auth, modèles, validation des flags)
/webapp         → routes web, templates, assets
/challenges     → environnements vulnérables isolés
/docs           → documentation technique & utilisateur
/tests          → tests unitaires et d’intégration
docker-compose.yml
README.md
app.py
```

---

## 🧪 Tests

Pas encore disponible

---

## 🔒 Sécurité

Même si certains environnements sont volontairement vulnérables, **la plateforme principale est sécurisée** :

- Validation systématique des entrées  
- Échappement des templates  
- Protection XSS/CSRF/SQLi  
- Isolation via conteneurs Docker pour les challenges vulnérables  

---



## 📦 Installation

### 1. Cloner le dépôt  
```bash
git clone https://github.com/illeska/cybercampus-ctf
cd repo
```

### 2. Lancer avec Docker  
```bash
docker-compose up --build
```

### 3. Accéder au site  
```
http://localhost:5000
```

---

## 📚 Documentation

Pas encore disponible
