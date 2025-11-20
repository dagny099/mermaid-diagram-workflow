# One Command, Many Docs: Automating MkDocs Deployments on EC2
*or: How I Finally Stopped Rebuilding Every Documentation Site by Hand*

If you’re juggling multiple personal or portfolio projects — each with its own MkDocs site — you may have discovered the same thing I did:

Rebuilding documentation manually gets old.  
Fast.

Especially on a free-tier EC2 instance, where:

- each project has similar dependencies,
- lots of tiny virtual environments waste space,
- and keeping track of which docs live where feels… fuzzy.

Eventually, even a patient person hits the point where they think:  
**“There has to be an easier way.”**

And there is.

This post walks through the small, elegant system I now use to rebuild *all* of my MkDocs sites with just four steps:

1. Edit my `app_inventory.yml`  
2. Update my unified `docs.conf`  
3. Run `rebuild_docs.sh`  
4. Restart Nginx  

That’s it.  
Let’s get you there.

---

## 🌱 The Big Idea: Treat All Docs as One Cohesive System

Instead of treating each MkDocs project as a special snowflake, we create:

- one **inventory** file that names all your MkDocs apps  
- one **script** that loops through them and rebuilds each site  
- one **Nginx config** that serves everything at `https://docs.yourdomain.com/*`

It feels like a small shift, but it gives you:

- a single place to update paths  
- a predictable build process  
- a repeatable deployment flow  
- dramatically less cognitive overhead  

---

## 🗂️ Directory Structure

```
/var/www/mkdocs-sites/
├── beehive-tracker/
├── fitness-dashboard/
├── convoscope/
└── citation-compass/

~/ops/
├── app_inventory.yml
├── rebuild_docs.sh
└── nginx/
    └── docs.conf
```

---

## 🎛️ Architecture Overview (D2 Diagram)

```d2
direction: right

app_inventory: "app_inventory.yml\n(Defines which apps have docs)"
rebuild: "rebuild_docs.sh\n(Rebuilds all MkDocs sites)"
nginx: "docs.conf\n(Nginx routes all docs)"

app_inventory -> rebuild: "Script reads inventory"
rebuild -> nginx: "Output copied to /var/www/mkdocs-sites"
nginx -> "https://docs.barbhs.com/*": "Served over HTTPS"
```

---

# 🪜 Step-by-Step Setup

## Step 1: Create Your app_inventory.yml

```yaml
apps:
  - name: beehive-tracker
    path: /home/ec2-user/apps/beehive-tracker
  - name: fitness-dashboard
    path: /home/ec2-user/apps/fitness-dashboard
  - name: convoscope
    path: /home/ec2-user/apps/convoscope
  - name: citation-compass
    path: /home/ec2-user/apps/citation-compass
```

---

## Step 2: Create rebuild_docs.sh

```bash
#!/usr/bin/env bash
set -e
echo "Starting full MkDocs rebuild..."

source /opt/mkdocs-venv/bin/activate

ROOT_DIR="/var/www/mkdocs-sites"
mkdir -p "$ROOT_DIR"

APPS=()
while IFS= read -r line; do
    APPS+=("$line")
done < <(yq e '.apps[].name' ~/ops/app_inventory.yml)

for NAME in "${APPS[@]}"; do
    echo "--- Rebuilding $NAME ---"
    SRC=$(yq e ".apps[] | select(.name==\"$NAME\") | .path" ~/ops/app_inventory.yml)
    DEST="$ROOT_DIR/$NAME"
    mkdir -p "$DEST"
    rm -rf "$DEST/*"

    (cd "$SRC" && mkdocs build -d "$DEST")
    echo "Built docs for $NAME"
done

sudo systemctl reload nginx
echo "All docs rebuilt!"
```

---

## Step 3: Configure Nginx with docs.conf

```nginx
server {
    server_name docs.barbhs.com;
    root /var/www/mkdocs-sites;

    location /beehive-tracker/ {
        alias /var/www/mkdocs-sites/beehive-tracker/;
        index index.html;
    }

    location /fitness-dashboard/ {
        alias /var/www/mkdocs-sites/fitness-dashboard/;
        index index.html;
    }

    location /convoscope/ {
        alias /var/www/mkdocs-sites/convoscope/;
        index index.html;
    }

    location /citation-compass/ {
        alias /var/www/mkdocs-sites/citation-compass/;
        index index.html;
    }

    listen 443 ssl;
    http2;

    ssl_certificate /etc/letsencrypt/live/docs.barbhs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docs.barbhs.com/privkey.pem;
}
```

---

## 🔐 Enable HTTPS with Certbot

```bash
sudo certbot --nginx -d docs.barbhs.com
```

---

## 🐧 EC2 Differences: Amazon Linux vs Ubuntu

| Task | Amazon Linux | Ubuntu |
|------|--------------|--------|
| Install Nginx | `sudo yum install nginx` | `sudo apt install nginx` |
| Nginx conf dir | `/etc/nginx/conf.d/` | `/etc/nginx/sites-available/` |
| Certbot | `sudo yum install certbot python3-certbot-nginx` | `sudo apt install certbot python3-certbot-nginx` |

---

## 🧪 Quick-Start: Redeploy Everything

```bash
nano ~/ops/app_inventory.yml
sudo nano /etc/nginx/conf.d/docs.conf
bash ~/ops/rebuild_docs.sh
sudo systemctl restart nginx
```

---

# 🌻 Conclusion

You now have a unified, dependable workflow for rebuilding and serving many MkDocs sites on a single EC2 instance.

Next up:  
👉 **From tmux to systemd: Leveling Up Your Personal Data Apps**

