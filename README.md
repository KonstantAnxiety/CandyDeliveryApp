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
The database is more robust then it is needed for the task, e.g. new courier types can be added to the reference table CourierType.

![DB diagram](https://user-images.githubusercontent.com/58992437/112771820-63af5200-9036-11eb-948a-b559679def60.png)

## Deploy
This instruction describes how to install the app with a new virtual environment, configure PostgreSQL database, Gunicorn as a WSGI HTTP server to listen to requests on bootup and nginx as a proxy server on Ubuntu 20.04.2, assumes that the server has a user with sudo privileges named `user` and features `nano` as a text editor.

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
* Generate a new rsa key pair and add the public key to GitHub
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
* Log into Postgres session, create the database and a new user for the django app
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
* To let the app interact with the database make the following changes to ```~/webapp/candydelivery/cda/cda/settings.py``` (highlighted lines imply individual information)
```diff
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
!        'NAME': 'cda_db',
!        'USER': 'sampledbuser',
!        'PASSWORD': 'SampleDBUserPass',
        'HOST': 'localhost',
        'PORT': '',
    }

}
```
* Do not use the secret key from the repo, instead generate a new one for the app with 
```sh
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```
And change the `SECRET_KEY` in `settings.py`, make sure to keep it secret.
* Migrate the database and load initial data
```sh
cd cda/
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata initial_data
```
* You may want to create a django superuser with
```sh
python manage.py createsuperuser
```
* If you want the app to feature static files, you need to collect them with
```sh
python manage.py collectstatic
```
* The virtual environment may now be deactivated
```sh
deactivate
```

### Configure Gunicorn
* Create a socket file for gunicorn
```sh
sudo nano /etc/systemd/system/gunicorn.socket
```
Add the following to the file
```sh
[Unit]
Description=gunicorn socket

[Socket]
ListenStream=/run/gunicorn.sock

[Install]
WantedBy=sockets.target
```

* Create a service file for Gunicorn
```sh
sudo nano /etc/systemd/system/gunicorn.service
```
Add the folloeing to the file (highlighted lines imply individual information)
```diff
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
!User=user
Group=www-data
!WorkingDirectory=/home/user/webapp/candydelivery/cda
!ExecStart=/home/user/webapp/candydelivery/venv/bin/gunicorn \
          --access-logfile - \
!          --workers 9 \
          --bind unix:/run/gunicorn.sock \
          cda.wsgi:application

[Install]
WantedBy=multi-user.target
```
* Start the socket with
```sh
sudo systemctl start gunicorn.socket
sudo systemctl enable gunicorn.socket
```
Troubleshoot using
```sh
sudo systemctl status gunicorn.socket
```

At first the socket may be dead. You can wake it up with
```sh
curl --unix-socket /run/gunicorn.sock localhost
```
You should see some html (Not found, because the root page is not implemented in the app)

Now the socket should be active when you execute
```sh
sudo systemctl status gunicorn.socket
```

### Configure nginx
* Assuming you want to modify the default server block
```sh
sudo nano /etc/nginx/sites-available/default
```
Add the following to the file (highlighted lines imply individual information)
```diff
server {
        listen 8080 default_server;
        listen [::]:8080 default_server;

        root /var/www/html;

        index index.html index.htm index.nginx-debian.html;

        server_name _;

        location /static/ {
!                root /home/user/webapp/candydelivery/cda;
        }

        location / {
                include proxy_params;
                proxy_pass http://unix:/run/gunicorn.sock;
        }
}
```
* Restart nginx with
```sh
sudo service nginx restart
```
* Troubleshoot with
```sh
sudo systemctl status gunicorn
```

## Tests
* Change to the repo directory
```sh
cd ~/webapp/candydelivery
```
* Activate the virtual environment
```sh
source venv/bin/activate
```
* Change to the app directory
```sh
cd cda/
```
This app features Django's unit tests.

To run tests use the following command while in the same directory as manage.py
```sh
python3 manage.py test
```
* To see a more verbose report use
```sh
coverage run manage.py test
coverage report
```
 ## Comments for backend-school
 The app features several more useful endpoints aside from the task, e.g.
 * `GET /courier-types` – list of all courier-types
 * `POST /courier-types` – add a new courier type, e.g.
 ```json
{
    "courier_type": "scooter",
    "capacity": "10",
    "earnings_coef": 7
}
 ```
 * `GET /couriers` – list of all couriers
 * `GET /orders` – list of all orders
