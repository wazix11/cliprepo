## Deployment on Linux
Much of this deployment is following Miguel Grinberg's guide found here: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvii-deployment-on-linux

### Connect using SSH
`ssh root@<server-ip-address>` (or an admin user you know the password to)

### Password-less Logins
SSH into your server's root account using the info above.

Create a user `ubuntu` (name this whatever you like), give it `sudo` powers, and switch to it:
```
$ adduser --gecos "" ubuntu
$ usermod -aG sudo ubuntu
$ su ubuntu
```
Leave the terminal session you have open on your server, start a second terminal on your local machine. If you are using Windows, this needs to have access to the `ssh` command, I use the Ubuntu app from WSL.

Check the contents of the ~/.ssh directory:
```
$ ls ~/.ssh
id_rsa  id_rsa.pub
```
If the directory listing shows files named `id_rsa` and `id_rsa.pub` like above, then you already have a key. If you don't have these files, or the ~/.ssh directory doesn't exist, you need to create your SSH keypair by running the following command:
```
$ ssh-keygen
```
This application will prompt you to enter a few things, you can likely accept the defaults by pressing Enter on all of the prompts.

After this command runs, you should have the two files listed above. The file `id_rsa.pub` is your *public key*, which is a file that you will provide to third parties. The `id_rsa` file is your *private key*, which should not be shared with anyone.

Configure your public key as an authorized host in your server. On the terminal opened to your own computer, print the public key to the screen:
```
$ cat ~/.ssh/id_rsa.pub
ssh-rsa some_long_string_of_characters
```
Copy the long string of characters from the command above, then switch back to the terminal on your remote server. Here you will use the following commands to store the public key:
```
$ echo <paste-your-key-here> >> ~/.ssh/authorized_keys
$ chmod 600 ~/.ssh/authorized_keys
```
Password-less login should now be working. You can now log out of your `ubuntu` session and your `root` session, then try to log in directly to the `ubuntu` account with:
```
$ ssh ubuntu@<server-ip-address>
```
You should not have to enter a password.

### Securing the server
Disable root logins via SSH. Open the file using `nano` and change a single line in this file:
```
$ sudo nano /etc/ssh/sshd_config
PermitRootLogin no
```
Locate the line that starts with `PermitRootLogin` and change the value to `no`.

Disable password logins:
```
$ sudo nano /etc/ssh/sshd_config
PasswordAuthentication no
```
Restart the service for changes to take effect:
```
$ sudo service ssh restart
```
Install a firewall to block access to the server on any ports that are not explicitly enabled:
```
$ sudo apt-get install -y ufw
$ sudo ufw allow ssh
$ sudo ufw allow http
$ sudo ufw allow 443/tcp
$ sudo ufw --force enable
$ sudo ufw status
```

### Installing Base Dependencies
```
$ sudo apt-get -y update
$ sudo apt-get -y install python3 python3-venv python3-dev
$ sudo apt-get -y install mysql-server supervisor nginx git goaccess
```

### Installing the Application
Set up your connection to GitHub.
```
$ mkdir -p -m 700 ~/.ssh/github
$ ssh-keygen -t ed25519 -C 'your-email' -f ~/.ssh/github/id_ed25519 -q -N ''
$ cat ~/.ssh/github/id_ed25519.pub
```
Copy the contents from `id_ed25519.pub` using the output of the above command.

- Go to https://github.com/settings/keys (GitHub>Settings>SSH and GPG keys)
- Click *New SSH Key*
- Enter a meaningful title, paste the content of `id_ed25519.pub` in the *Key* field
- Click the *Add SSH Key* button.
```
$ touch ~/.ssh/config
$ chmod 600 ~/.ssh/config
$ nano ~/.ssh/config

Host github.com
    IdentityFile ~/.ssh/github/id_ed25519
```
Test the setup using the following command:
```
$ ssh -T git@github.com
```
If everything is working, you should see a response about being successfully authenticated.

Clone the repository using the SSH link from GitHub.
```
$ git clone git@github.com:wazix11/cliprepo.git
$ cd cliprepo
```
Create and fill `.flaskenv` file:
```
$ nano .flaskenv

FLASK_APP=cliprepo.py
FLASK_DEBUG=0
```
Copy `.env.example` and rename to `.env`, then fill all fields:
```
$ cp .env.example .env
$ nano .env
```
Create the virtual environment and populate it with all the package dependencies:
```
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```
Additionally, install `gunicorn` to use as a web server:
```
(venv) $ pip install gunicorn
```

### Setting up MySQL
```
$ sudo mysql -u root
```
Create the database and a user with full access to it:
```
mysql> CREATE DATABASE cliprepo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql> CREATE USER 'cliprepo'@'localhost' IDENTIFIED BY '<db-password>';
mysql> GRANT ALL PRIVILEGES ON cliprepo.* TO 'cliprepo'@'localhost';
mysql> FLUSH PRIVILEGES;
mysql> quit;
```
Replace `<db-password>` with a password of your choice. This will need to match the password that you included in `DATABASE_URL` in the `.env` file.

If the database configuration is correct, you should be able to run the database migrations that create all tables:
```
(venv) $ flask db upgrade
```
Make sure this completes without error before you continue.

Seed the database with the necessary data:
```
(venv) $ python3 -m app.seed
```

### Setting Up Gunicorn and Supervisor
Create and fill a Supervisor configuration file for cliprepo:
```
$ sudo nano /etc/supervisor/conf.d/cliprepo.conf

[program:cliprepo]
command=/home/ubuntu/cliprepo/venv/bin/gunicorn -b localhost:8000 -w 4 cliprepo:app
directory=/home/ubuntu/cliprepo
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
```
Create and fill a Supervisor configuration file for the scheduler:
```
$ sudo nano /etc/supervisor/conf.d/scheduler.conf

[program:scheduler]
command=/home/ubuntu/cliprepo/venv/bin/python -m app.scheduler.scheduler
directory=/home/ubuntu/cliprepo
autostart=true
autorestart=true
stderr_logfile=/var/log/scheduler.err.log
stdout_logfile=/var/log/scheduler.out.log
```
Reload the supervisor service:
```
$ sudo supervisorctl reload
```

### Setting Up Nginx

Set up a self-signed SSL certificate (for test deployments only), this will be created while in the cliprepo directory:
```
$ mkdir certs
$ openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout certs/key.pem -out certs/cert.pem
```
Create the Nginx configuration file for cliprepo:
```
$ sudo nano /etc/nginx/sites-available/cliprepo

server {
    # listen on port 80 (http)
    listen 80;
    server_name alv.cliprepo.com www.cliprepo.com cliprepo.com;

    location / {
        # redirect any requests to the same URL but on https with the correct subdomain
        return 301 https://alv.cliprepo.com$request_uri;
    }
}

# redirect cliprepo.com and www.cliprepo.com https -> alv.cliprepo.com https
server {
    listen 443 ssl;
    server_name cliprepo.com www.cliprepo.com;

    ssl_certificate /home/ubuntu/cliprepo/certs/cert.pem;
    ssl_certificate_key /home/ubuntu/cliprepo/certs/key.pem;

    return 301 https://alv.cliprepo.com$request_uri;
}

# main application server for alv.cliprepo.com
server {
    # listen on port 443 (https)
    listen 443 ssl;
    server_name alv.cliprepo.com;

    # location of the self-signed SSL certificate
    ssl_certificate /home/ubuntu/cliprepo/certs/cert.pem;
    ssl_certificate_key /home/ubuntu/cliprepo/certs/key.pem;

    # write access and error logs to /var/log
    access_log /var/log/cliprepo_access.log;
    error_log /var/log/cliprepo_error.log;

    location / {
        # forward application requests to the gunicorn server
        proxy_pass http://localhost:8000;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        # handle static files directly, without forwarding to the application
        alias /home/ubuntu/cliprepo/app/static;
        expires 30d;
    }
}
```
Remove the Nginx test site:
```
$ sudo rm /etc/nginx/sites-enabled/default
```
Create a link to the cliprepo configuration:
```
$ sudo ln -s /etc/nginx/sites-available/cliprepo /etc/nginx/sites-enabled/cliprepo
```
Update static folder permissions:
```
$ sudo find /home/ubuntu/cliprepo/app/static -type d -exec chmod 755 {}
$ sudo find /home/ubuntu/cliprepo/app/static -type f -exec chmod 644 {}
$ sudo chmod 755 /home
$ sudo chmod 755 /home/ubuntu
$ sudo chmod 755 /home/ubuntu/cliprepo
$ sudo chmod 755 /home/ubuntu/cliprepo/app
$ sudo chown -R ubuntu:www-data /home/ubuntu/cliprepo/app/static
```
Tell nginx to reload the configuration:
```
$ sudo service nginx reload
```

#### Setting up Certbot
https://blog.miguelgrinberg.com/post/using-free-let-s-encrypt-ssl-certificates-in-2025
```
$ sudo snap install --classic certbot
```
Create a */var/certs/challenge* directory where certbot will write its verification files:
```
$ sudo mkdir -p /var/certs/challenge
```
In the first server block of the Nginx configuration, add the *well-known* location:
```
$ sudo nano /etc/nginx/sites-available/cliprepo
    server {
        # listen on port 80 (http)
        listen 80;
        server_name alv.cliprepo.com www.cliprepo.com cliprepo.com;

        location ~ /.well-known {
            root /var/certs/challenge;
        }

        location / {
            # redirect any requests to the same URL but on https with the correct subdomain
            return 301 https://alv.cliprepo.com$request_uri;
        }
    }
```
Reload Nginx:
```
$ sudo systemctl reload nginx
```

#### Obtaining your SSL certificate
Run the `certbot` command to request an SSL certificate from Let's Encrypt:
```
$ sudo certbot certonly --agree-tos -m your@email.com --webroot -w /var/certs/challenge -d domain.com --deploy-hook "systemctl reload nginx"
```
- `--agree-tos`: agrees to the terms of service
- `-m <email-address>`: email address to receive important notifications about your SSL certificate such as expiration reminders.
- `--webroot`: select the webroot verification method
- `-w /var/certs/challenge`: configure the webroot directory
- The `-d` option can be repeated for multiple domains/subdomains.
- `--deploy-hook "systemctl reload nginx"`: the command to run after a certificate is obtained or renewed.

Open the nginx configuration file and replace the self-signed certificate files with the "Certificate is saved at" and "Key is saved at" locations:
```
$ sudo nano /etc/nginx/sites-available/cliprepo

    ssl_certificate /etc/letsencrypt/live/domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domain.com/privkey.pem;
```
Reload Nginx manually to switch to the new certificate. In the future, this should happen automatically:
```
$ sudo systemctl reload nginx
```