#!/bin/sh
# Container entrypoint: bootstrap site-wide Basic Auth from env, then run
# nginx + cron + gunicorn (same process layout as the old inline CMD).
set -e

# Make the runtime environment available to cron jobs.
printenv > /etc/environment

# Site-wide HTTP Basic Auth. nginx.conf `include`s /etc/nginx/auth.conf at
# server scope; we generate it (and the htpasswd) from APP_USERNAME /
# APP_PASSWORD here. Empty APP_PASSWORD => empty include => auth disabled
# (handy for local/dev). {SHA} is an nginx-supported scheme so we need no
# extra apt package (apache2-utils/openssl) just to hash one password.
if [ -n "$APP_PASSWORD" ]; then
  python -c "import base64,hashlib,os;u=os.environ.get('APP_USERNAME') or 'admin';p=os.environ['APP_PASSWORD'];open('/etc/nginx/.htpasswd','w').write(u+':{SHA}'+base64.b64encode(hashlib.sha1(p.encode()).digest()).decode()+'\n')"
  printf 'auth_basic "MediaGap";\nauth_basic_user_file /etc/nginx/.htpasswd;\n' > /etc/nginx/auth.conf
else
  : > /etc/nginx/auth.conf
fi

cron
nginx -g 'daemon off;' &
exec gunicorn mediacrawler.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-300}"
