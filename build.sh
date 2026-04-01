#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
echo "from core.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'yourpassword', role='admin')" | python manage.py shell
```

Push this change → Render redeploys → then **remove that line** and push again (so it doesn't run every deploy).

---

## Step 6 — Access Your Live App

After deploy finishes (2–5 mins), Render gives you a URL like:
```
https://helpdesk.onrender.com