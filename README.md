# Candy Delivery REST API
REST API for candy shop deliveries ([TASK](https://disk.yandex.ru/d/TbWKTZbnOST80Q?w=1)).

## Technologies used
* python3
* Django
* Django REST framework
* PostgreSQL
* Gunicorn
* nginx

## Database diagram

![DB diagram](https://user-images.githubusercontent.com/58992437/112771820-63af5200-9036-11eb-948a-b559679def60.png)

## Deploy
This instruction describes how to install the app with a new virtual environment, configure PostgreSQL database, Gunicorn as a WSGI HTTP server to listen to requests after reboot or shutdown and nginx as a proxy server on Ubuntu 20.04.2.

### Install packages
* Install python3
* Install needed and useful packages
```sh
sudo apt install git htop python3-pip python3-dev python3-virtualenv postgresql postgresql-contrib libpq-dev nginx curl
```
* You may want to change the password for the default postgres user
```sh
sudo passwd postgres
```
* Upgrade pip
```sh
python3 -m pip install --upgrade pip
```

### Configure Django app and PostgreSQL
* Change to home directory
```sh
cd
```
* Let's assume we want to store apps in a distinct directory
```sh
mkdir webapp
cd webapp/
```
* Generate a new rsa key pair and add it to GitHub
```console
ssh-keygen
cat ~/.ssh/id_rsa.pub
```
* Get the repository
```sh
git clone git@github.com:KonstantAnxiety/CandyDeliveryApp.git candydelivery
cd candydelivery/
git status
```
* Create a virtual environment, activate it and install required packages
```sh
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
* Log into Postgres session, create a database and new user for the django app
```sh
sudo -u postgres psql
postgres=# CREATE DATABASE cda_db;
postgres=# CREATE USER sampledbuser WITH PASSWORD 'SampleDBUserPass';
postgres=# ALTER ROLE sampledbuser SET client_encoding TO 'utf8';
postgres=# ALTER ROLE sampledbuser SET default_transaction_isolation to 'read committed';
postgres=# ALTER ROLE sampledbuser SET timezone TO 'UTC';
postgres=# GRANT ALL PRIVILEGES ON DATABASE cda_db to sampledbuser;
postgres=# \q
```
* To let the app to interact with the database make the following changes to ```~/webapp/candydelivery/cda/cda/settings.py```
<pre>
 ![#f03c15](https://placehold.it/15/f03c15/000000?text=+) `#f03c15`
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': ' ![#f03c15](https://placehold.it/15/f03c15/000000?text=+) `#f03c15`cda_db',
        'USER': '_sampledbuser_',
        'PASSWORD': '!SampleDBUserPass!',
        'HOST': 'localhost',
        'PORT': '',
    }

}
</pre>
* Migrate the database and load initial data
```console
cd cda/
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata initial_data
```
* You may want to create a django superuser with
```console
python manage.py createsuperuser
```
* If you want the app to feature static files, you need to collect them with
```console
python manage.py collectstatic
```

## Configure Gunicorn
### Gunicorn socket
deactivate
sudo nano /etc/systemd/system/gunicorn.socket
Add the following to the file
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target


### Gunicorn service
sudo nano /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=!entrant!
Group=www-data
WorkingDirectory=/home/!user!/webapp/candydelivery/cda
ExecStart=/home/!user!/webapp/candydelivery/venv/bin/gunicorn \
          --access-logfile - \
          --workers !9! \
          --bind unix:/run/gunicorn.sock \
          cda.wsgi:application

[Install]
WantedBy=multi-user.target

Start the socket with
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
Troubleshoot using
sudo systemctl status gunicorn.socket

At first the socket may be dead. You can wake it up with
curl --unix-socket /run/gunicorn.sock localhost
You should see some html (Not found, because the root page is not implemented in the app)

Now the socket should be active when you execute
sudo systemctl status gunicorn.socket



## Configure nginx
sudo nano /etc/nginx/sites-available/default
add the folloeing to the file
server {
        listen 8080 default_server;
        listen [::]:8080 default_server;

        root /var/www/html;

        index index.html index.htm index.nginx-debian.html;

        server_name _;

        location /static/ {
                root /home/!user!/webapp/candydelivery/cda;
        }

        location / {
                include proxy_params;
                proxy_pass http://unix:/run/gunicorn.sock;
        }
}

Restart nginx with
sudo service nginx restart

Troubleshoot with
sudo systemctl status gunicorn




Activate created virtual environment
source ~/webapp/candydelivery/venv/bin/activate

Generate a new secret key for your app with
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
And change the SECRET_KEY in settings.py, make sure to keep it secret.





Tests
Go to the repo directory
cd ~/webapp/candydelivery

Activate the virtual environment
source venv/bin/activate

Go to the app directory
cd cda/

This app features django unittest. ?????
To run tests use the following while in the same directory as manage.py
python3 manage.py test

To see a more verbose report use
coverage run manage.py test
coverage report
