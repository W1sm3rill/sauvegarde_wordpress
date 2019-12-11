Script pour sauvegarder un site WordPress et sa Base De Données sur un site distant.  
Les sauvegardes sont archivées dans un fichier ".tar.gz" avec la date du jour.  
Les archives périmées sont supprimées.  

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

Python version 3.x