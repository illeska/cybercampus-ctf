<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberForum - Mon Profil</title>
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
            max-width: 800px;
            margin: 30px auto;
            padding: 0 20px;
        }

        .profile-card {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }

        .profile-header {
            display: flex;
            align-items: center;
            gap: 30px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f2f5;
        }

        .avatar-placeholder {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: white;
            flex-shrink: 0;
        }

        .profile-info h2 {
            color: #333;
            margin-bottom: 10px;
        }

        .profile-info p {
            color: #666;
        }

        .upload-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            border: 2px dashed #ddd;
        }

        .upload-section h3 {
            color: #333;
            margin-bottom: 15px;
        }

        .upload-form {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .file-input-wrapper {
            position: relative;
        }

        .file-input-label {
            display: inline-block;
            padding: 12px 25px;
            background: #4267B2;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.3s;
        }

        .file-input-label:hover {
            background: #365899;
        }

        input[type="file"] {
            position: absolute;
            opacity: 0;
            width: 0;
            height: 0;
        }

        .file-name {
            margin-left: 15px;
            color: #666;
        }

        .upload-btn {
            padding: 12px 30px;
            background: #42b72a;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.3s;
        }

        .upload-btn:hover {
            background: #36a420;
        }

        .upload-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .message {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .message.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }

        .message.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }

        .hint-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
        }

        .hint-box h4 {
            color: #856404;
            margin-bottom: 10px;
        }

        .hint-box p {
            color: #856404;
            font-size: 0.95rem;
        }

        .hint-box ul {
            margin: 10px 0 0 20px;
            color: #856404;
        }

        .hint-box li {
            margin: 5px 0;
        }

        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            color: #d63384;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="container">
            <h1>🌐 CyberForum</h1>
            <nav>
                <a href="index.php">Accueil</a>
                <a href="profile.php" class="active">Mon Profil</a>
            </nav>
        </div>
    </div>

    <div class="container">
        <?php
        $message = '';
        $messageType = '';

        if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['avatar'])) {
            $uploadDir = 'uploads/';
            $file = $_FILES['avatar'];
            $fileName = basename($file['name']);
            $fileTmpName = $file['tmp_name'];
            $fileSize = $file['size'];
            
            // Vulnérabilité : Validation insuffisante !
            // Seule l'extension est vérifiée, pas le contenu réel
            $allowedExtensions = ['jpg', 'jpeg', 'png', 'gif'];
            $fileExtension = strtolower(pathinfo($fileName, PATHINFO_EXTENSION));
            
            if (!in_array($fileExtension, $allowedExtensions)) {
                $message = "❌ Format de fichier non autorisé. Seuls JPG, JPEG, PNG et GIF sont acceptés.";
                $messageType = 'error';
            } elseif ($fileSize > 2000000) {
                $message = "❌ Le fichier est trop volumineux (max 2MB).";
                $messageType = 'error';
            } else {
                // VULNÉRABILITÉ CRITIQUE : Aucune vérification du contenu réel
                // Le fichier est déplacé directement sans analyse
                if (move_uploaded_file($fileTmpName, $uploadDir . $fileName)) {
                    $message = "✅ Avatar téléchargé avec succès : <a href='{$uploadDir}{$fileName}' target='_blank'>{$fileName}</a>";
                    $messageType = 'success';
                } else {
                    $message = "❌ Erreur lors du téléchargement.";
                    $messageType = 'error';
                }
            }
        }
        ?>

        <?php if ($message): ?>
        <div class="message <?php echo $messageType; ?>">
            <?php echo $message; ?>
        </div>
        <?php endif; ?>

        <div class="profile-card">
            <div class="profile-header">
                <div class="avatar-placeholder">
                    👤
                </div>
                <div class="profile-info">
                    <h2>John Doe</h2>
                    <p>Membre depuis Janvier 2024</p>
                    <p>📧 john.doe@cyberforum.com</p>
                </div>
            </div>

            <div class="upload-section">
                <h3>📸 Changer votre avatar</h3>
                <form method="POST" enctype="multipart/form-data" class="upload-form" id="uploadForm">
                    <div class="file-input-wrapper">
                        <label for="avatar" class="file-input-label">
                            📁 Choisir un fichier
                        </label>
                        <input type="file" id="avatar" name="avatar" accept="image/*" onchange="updateFileName(this)" required>
                        <span class="file-name" id="fileName">Aucun fichier sélectionné</span>
                    </div>
                    <button type="submit" class="upload-btn">
                        ⬆️ Télécharger l'avatar
                    </button>
                </form>
            </div>
        </div>
    </div>

    <script>
        function updateFileName(input) {
            const fileName = input.files[0] ? input.files[0].name : 'Aucun fichier sélectionné';
            document.getElementById('fileName').textContent = fileName;
        }
    </script>
</body>
</html>
