#!/bin/sh
# Container entrypoint: bootstrap site-wide Basic Auth from env, then run
# nginx + uvicorn (FastAPI).
set -e

# Make the runtime environment available to APScheduler cron jobs.
printenv > /etc/environment

# Site-wide HTTP Basic Auth.
: > /etc/nginx/auth.conf
if [ -n "$APP_PASSWORD" ]; then
  if python -c "import base64,hashlib,os;u=os.environ.get('APP_USERNAME') or 'admin';p=os.environ['APP_PASSWORD'];open('/etc/nginx/.htpasswd','w').write(u+':{SHA}'+base64.b64encode(hashlib.sha1(p.encode()).digest()).decode()+'\n')"; then
    printf 'auth_basic "MediaGap";\nauth_basic_user_file /etc/nginx/.htpasswd;\n' > /etc/nginx/auth.conf
  else
    echo "entrypoint: htpasswd generation failed; Basic Auth DISABLED" >&2
  fi
fi

nginx -g 'daemon off;' &
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "${UVICORN_WORKERS:-1}" \
  --timeout-keep-alive 120
