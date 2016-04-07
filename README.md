# Apetizer

Apetizer est une application d'interaction de flux.

## concepts

Elle est concue sur la bes d'un modèle de donnée hiérarchisé, traductible, versionable.

Chaque element est transversalement:

un chemin vers des données
l'expression d'un visiteur
une modération de donnée
une traduction de ces donénes
un élément hiérarchique et opérationel

On peut representer ainsi les formes principale de structure de données web.

L'interface de base est pensée pour donner accès a un ensemble d'action par objet.

Les actions forment le vocabulaire de l'application.
Elle produisent des modérations, status résultant des actions.

Ce moteur basé sur les evènements permet d'aggrèger par référence l'historique des actions.
Avec un état constant, on peut facilement synchroniser des noeuds distribués par branche.

De base, le visiteur a tous les droits.



## use

Elle peut etre utilisée:

comme une application autonome, 
comme application django,

comme une extension jupyter notebook, 
comme une application tornado


# install

Install python from 2.7 to 3.5
Looks like it works with django 1.5 to 1.10

In the directory where you have your project repo,
create a virtualenv to collect python packages


    virtualenv --no-site-packages .


Enter the virtualenv context


    source bin/activate


Install the required packages


    pip install git+https://github.com/biodigitals/apetizer.git#egg=apetizer


Create the database:


    apetizer migrate


Create a superuser:


    apetizer createsuperuser


Run the server localy:

    apetizer runserver



# Develop

utilisée comme une extension jupyter,
elle permet d'editer dans leur contexte les éléments de contenu

le développeur peut alors créer des scripts de comportement et leur assigner une périodicité.

a lot More comming about this ... keep in touch

# Installation d'un raspberrypi

raspberrypi login: pi
pass: raspberry

Trouver le réseau : ifconfig
(double tabulation permet l'affichage de la liste sous un répertoire)
 
startx

Le raspberry doit être connecté au wifi

sudo apt-get install build-essential git python-pip python-dev
sudo apt-get install libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev

sudo pip install git+http://github.com/biodigitals/apetizer.gi#egg=Apetizer

Installation du projet django


Aller sur adresseipduraspberry:8888
