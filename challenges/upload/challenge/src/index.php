<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberForum - Accueil</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: #f0f2f5;
            line-height: 1.6;
        }

        .navbar {
            background: #4267B2;
            color: white;
            padding: 15px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .navbar .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .navbar h1 {
            font-size: 1.5rem;
        }

        .navbar nav a {
            color: white;
            text-decoration: none;
            margin-left: 20px;
            padding: 8px 15px;
            border-radius: 5px;
            transition: background 0.3s;
        }

        .navbar nav a:hover {
            background: rgba(255,255,255,0.2);
        }

        .navbar nav a.active {
            background: rgba(255,255,255,0.3);
        }

        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }

        .welcome {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }

        .welcome h2 {
            color: #4267B2;
            margin-bottom: 15px;
        }

        .welcome p {
            color: #666;
            font-size: 1.1rem;
        }

        .categories {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }

        .category-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .category-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }

        .category-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }

        .category-card h3 {
            color: #333;
            margin-bottom: 10px;
        }

        .category-card p {
            color: #666;
            font-size: 0.95rem;
            margin-bottom: 15px;
        }

        .category-stats {
            display: flex;
            justify-content: space-between;
            color: #999;
            font-size: 0.9rem;
        }

        .btn {
            display: inline-block;
            padding: 10px 20px;
            background: #4267B2;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }

        .btn:hover {
            background: #365899;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="container">
            <h1>🌐 CyberForum</h1>
            <nav>
                <a href="index.php" class="active">Accueil</a>
                <a href="profile.php">Mon Profil</a>
            </nav>
        </div>
    </div>

    <div class="container">
        <div class="welcome">
            <h2>Bienvenue sur CyberForum</h2>
            <p>La communauté des passionnés de technologie et de cybersécurité</p>
        </div>

        <div class="categories">
            <div class="category-card">
                <div class="category-icon">💻</div>
                <h3>Programmation</h3>
                <p>Discutez de vos langages préférés, partagez vos projets et posez vos questions.</p>
                <div class="category-stats">
                    <span>📝 1,234 sujets</span>
                    <span>💬 12,456 messages</span>
                </div>
            </div>

            <div class="category-card">
                <div class="category-icon">🔒</div>
                <h3>Cybersécurité</h3>
                <p>Échangez sur les dernières vulnérabilités, techniques de protection et CTF.</p>
                <div class="category-stats">
                    <span>📝 892 sujets</span>
                    <span>💬 8,321 messages</span>
                </div>
            </div>

            <div class="category-card">
                <div class="category-icon">🌐</div>
                <h3>Web Development</h3>
                <p>HTML, CSS, JavaScript, frameworks modernes et meilleures pratiques.</p>
                <div class="category-stats">
                    <span>📝 2,156 sujets</span>
                    <span>💬 18,942 messages</span>
                </div>
            </div>

            <div class="category-card">
                <div class="category-icon">🤖</div>
                <h3>Intelligence Artificielle</h3>
                <p>Machine Learning, Deep Learning, LLMs et applications de l'IA.</p>
                <div class="category-stats">
                    <span>📝 567 sujets</span>
                    <span>💬 4,892 messages</span>
                </div>
            </div>

            <div class="category-card">
                <div class="category-icon">🐧</div>
                <h3>Linux & Open Source</h3>
                <p>Distributions, administration système, logiciels libres et scripts.</p>
                <div class="category-stats">
                    <span>📝 1,089 sujets</span>
                    <span>💬 9,654 messages</span>
                </div>
            </div>

            <div class="category-card">
                <div class="category-icon">📱</div>
                <h3>Mobile Development</h3>
                <p>iOS, Android, React Native, Flutter et développement cross-platform.</p>
                <div class="category-stats">
                    <span>📝 743 sujets</span>
                    <span>💬 6,128 messages</span>
                </div>
            </div>
        </div>

        <div class="welcome" style="margin-top: 30px;">
            <p style="color: #999; font-size: 0.9rem;">
                💡 N'oubliez pas de personnaliser votre profil et de télécharger un avatar !
            </p>
            <a href="profile.php" class="btn" style="margin-top: 15px;">
                Accéder à mon profil
            </a>
        </div>
    </div>
</body>
</html>
