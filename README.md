# CyberCampus CTF — Plateforme Capture The Flag

> Plateforme web pédagogique de type **Capture The Flag** pour apprendre la cybersécurité par la pratique.

---

## 🆕 Ce qui a changé dans cette version

Cette version marque une **refonte complète de l'interface utilisateur**. Toutes les pages ont été redessinées avec une direction artistique cohérente : dark theme, grille de fond animée, typographie Orbitron, palette vert/bleu, cartes avec hover effects, responsive mobile-first sur toutes les pages.

Pages refaites : accueil, bibliothèque de cours, pages de cours individuels, liste des challenges, page challenge, scoreboard, dashboard, actualités, CGU / mentions légales / politique de confidentialité, login et register.

Nouveautés fonctionnelles :
- **reCAPTCHA v2** sur le login et l'inscription
- Vérification email par code 6 chiffres à l'inscription
- Suppression de compte avec confirmation par email
- Modification de profil complet
- Système d'indices avec pénalités progressives
- Agrégateur d'actualités cyber (flux RSS FR/EN avec filtres)
- CI/CD via GitHub Actions avec self-hosted runner sur Azure

---

## 🎯 Objectif du projet

- Proposer un environnement d'apprentissage ludique autour des vulnérabilités web courantes
- Permettre aux joueurs de résoudre des défis et de soumettre des flags
- Offrir une plateforme sécurisée avec des environnements vulnérables isolés via Docker
- Fournir un tableau de bord, un classement dynamique et une gestion complète des utilisateurs

---

## 🏗️ Fonctionnalités

### Utilisateurs
- Inscription / Connexion avec reCAPTCHA v2
- Vérification email obligatoire par code à 6 chiffres
- Tableau de bord personnel (progression, historique, stats)
- Modification de profil (pseudo, email, mot de passe, pays, genre, année de naissance)
- Suppression de compte avec double confirmation
- Classement global (scoreboard)

### Challenges

| Challenge | Difficulté | Points |
|-----------|-----------|--------|
| SQL Injection | Débutant | 25 pts |
| XSS Reflected | Débutant | 25 pts |
| Bruteforce | Intermédiaire | 175 pts |
| Cryptographie | Intermédiaire | 75 pts |
| OSINT | Débutant | 50 pts |
| Upload de fichiers | Intermédiaire | 125 pts |
| Stéganographie | Intermédiaire | 150 pts |

### Cours
7 cours gratuits couvrant chaque vulnérabilité, avec théorie, exemples de code et lien vers le challenge.

### Actualités
Agrégateur RSS cybersécurité (CERT-FR, Zataz, The Hacker News, Bleeping Computer…) avec filtres source / langue / période.

---

## 🗂️ Structure du projet
```
/core              → logique interne (auth, modèles, forms)
/webapp            → routes web, templates, assets
/templates       → pages Jinja2
/static          → CSS, JS, images
/challenges        → environnements vulnérables isolés
docker-compose.yml
app.py
config.py
requirements.txt
```
---

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Python / Flask |
| Base de données | PostgreSQL |
| Auth | Flask-Login + bcrypt |
| Email | Flask-Mail (OVH SMTP) |
| Hébergement | Microsoft Azure (VM Ubuntu) |
| Reverse proxy | Nginx |
| Conteneurisation | Docker / Docker Compose |
| CI/CD | GitHub Actions (self-hosted runner) |
| CAPTCHA | Google reCAPTCHA v2 |

---

## 📦 Installation locale

### 1. Cloner le dépôt
```bash
git clone https://github.com/illeska/cybercampus-ctf
cd cybercampus-ctf
```

### 2. Configurer les variables d'environnement
Créer un fichier `.env` à la racine en se basant sur `.env.example`.
```env
DATABASE_URL=postgresql://user:password@db:5432/cybercampus
```

### 3. Lancer avec Docker
```bash
docker-compose up --build
```

### 4. Accéder au site
http://localhost:5000
---

## 🔒 Sécurité

- Mots de passe hashés avec bcrypt
- Vérification email obligatoire
- reCAPTCHA v2 sur les formulaires d'authentification
- Protection CSRF (Flask-WTF)
- Rate limiting sur les routes sensibles
- Isolation des environnements vulnérables via Docker
- HTTPS (TLS / Let's Encrypt)
- Cookies HttpOnly + Secure

---

*Projet académique personnel — non commercial.*  
*[github.com/illeska](https://github.com/illeska)*