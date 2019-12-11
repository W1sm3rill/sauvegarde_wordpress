Sauvegarder un site WordPress et sa Base De Données sur un site distant.  
==

Les sauvegardes sont archivées dans un fichier ".tar.gz" avec la date du jour.  
Les archives périmées sont supprimées.  

En details ?   
==

Python version 3.x   

Les variables sont récupérées dans le fichier "informations".   
Un logging basic est lancé.   

Le script va créer un dosssier de sauvegarde wordpress sur le serveur hote,   
Se connecter au serveur web,   
Créer un dossier temporaire,   
Copier le dossier Wordpress dans le dossier temporaire,   
Télécharger le dossier temporaire dans le dossier de sauvegarde wordpress   
Et supprimer le dossier temporaire.   

Il va analyser et récuperer les informations de connexion à la base de données contenu dans le fichier wp-config.php,   
Créer un dossier de sauvegarde BDD,   
sauvegarder Mysql dans le dossier de sauvegarde BDD.   

Il va archiver et compresser les sauvegardes Wordpress et BDD avec la date du jour   
Et supprimer les dossiers de sauvegarde.   

Il va supprimer les anciennes archives en comparant la date du jour et la date de l'archive,   
Si supérieur au nombre de jour spécifié.   

En cas d'erreur dans le déroulement du script, un email sera envoyé contenant le message d'erreur   
Et une inscription dans le fichier de log.


Consignes :
==

Lancez le script via la commande ```#./sauvegarde_wordpress.py```   

Pour "import pysftp" il faut installer le module au préalable via : ```pip3 install pysftp```  

Le script et le fichier "informations" doivent être dans le même dossier.  
Pour plus de sécurité sur ce fichier contenant des mots de passe, changez le propriétaire et les droits du fichier. (chown et chmod)   

"informations" contient les variables nécessaire au script :  

```
[MAIL]
mail: vôtre adresse gmail
mdp: le mot de passe de l'adresse gmail

[SFTP]
host: l'IP du serveur web
user: l'utilisateur du serveur web
mdp: le mot de passe de l'utilisateur

[VARIABLES]
sauvegarde: le chemin du dossier de sauvegarde de la machine hôte
temporaire: le chemin du dossier de sauvegarde temporaire de la machine distant
wordpress: le chemin du dossier wordpress
expiration: péremption des archives exprimés en jour
```
