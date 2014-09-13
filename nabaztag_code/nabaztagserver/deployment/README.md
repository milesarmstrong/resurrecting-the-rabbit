Deployment
===
These are steps required to acheive a working Django site deployment.

This method uses Nginx as the front end server, which serves static and media files, and routes other requests to uWSGI sockets.

uWSGI serves the `nabaztagserver` Django application to a socket located at `/run/uwsgi/nabaztag_django.sock`. It also serves a websocket server located at `/run/uwsgi/websocket.sock`.

Tutorial:

- http://django-websocket-redis.readthedocs.org/en/latest/running.html
- http://uwsgi.readthedocs.org/en/latest/tutorials/Django_and_nginx.html

#####Install things#####

Nginx must be version 1.4 or higher, which may be hard to install on Ubuntu 12.04 LTS:
http://askubuntu.com/questions/415033/cant-upgrade-nginx-on-ubuntu-12-04

```
sudo apt-get install nginx redis
sudo apt-get install python-setuptools python-software-properties python2.7-dev
sudo pip install django uwsgi django-websocket-redis
```
####Static, Media and Database####

* In `nabaztagserver` directory:

Create directory to hold static files, e.g. CSS & JS required for Django, these will be served by Nginx:

```
mkdir static
python django-admin.py collectstatic
````
Create directory for media files, e.g Images, these will be served by Nginx:

```
mkdir media
```

Create directory for database file, this must be writeable by the www-data user:

```
mkdir db
python manageserver.py syncdb
sudo chgrp -R www-data db/
sudo chmod -R 775 db/
```

#####Edit things#####
`nginx.conf`, `nabaztagserver_uwsgi.ini` & `websocketserver_uwsgi.ini` use absolute paths to locate the sockets and the Django application. Each of these files should be edited before symlinking.

#####Link things#####

Link Nginx config:

```
cd /etc/nginx/sites-enabled
sudo ln -s /full/path/to/nginx.conf
```

Link uWSGI ini files (for Emperor):

```
cd /etc/uwsgi/apps-enabled
sudo ln -s /full/path/to/nabaztagserver_uwsgi.ini
sudo ln -s /full/path/to/websocketserver_uwsgi.ini
```

Link uWSGI Emperor init file for Upstart:

```
cd /etc/init/
sudo ln -s /full/path/to/uwsgi.conf
```

####Test####

Reload Nginx:

```
sudo nginx -s reload
```

Start uWSGI Emperor

```
sudo service uwsgi start
```
