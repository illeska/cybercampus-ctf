FROM php:8.1-apache

# Activer mod_rewrite
RUN a2enmod rewrite

# Créer les dossiers nécessaires
RUN mkdir -p /var/www/html/uploads && \
    chmod 777 /var/www/html/uploads

# Copier les fichiers du challenge
COPY src/ /var/www/html/

# Copier la configuration .htaccess pour uploads
COPY uploads/.htaccess /var/www/html/uploads/.htaccess

# Créer le fichier flag
RUN echo "CTF{Upl04d_PHP_Sh3ll_M4st3r}" > /flag.txt && \
    chmod 644 /flag.txt

# Permissions Apache
RUN chown -R www-data:www-data /var/www/html

EXPOSE 80

CMD ["apache2-foreground"]
