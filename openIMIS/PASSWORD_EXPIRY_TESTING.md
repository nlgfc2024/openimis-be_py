# Password expiry test instructions

Run all commands from this folder:

```bash
cd /home/edweard/PyCharmMiscProject/Coremis/openimis-be_py/openIMIS
```

## Test users

| Username | Password | Email | Name |
|---|---|---|---|
| `pwd_expiry_test` | `TestExpiry123!` | `pwd_expiry_test@example.invalid` | Test Expiry |
| `edd` | Use the password you created in the UI | `edwardacan@gil.com` | cquaron cquaron |

## What you are testing

The password expires when the user's `password_validity` time is in the past.

To avoid waiting 3 months, the commands below set `password_validity` to a few minutes from now.

---

# Test user: `pwd_expiry_test`

## 1. Make the password expire in 3 minutes

```bash
USERNAME="pwd_expiry_test" MINUTES=3 python manage.py shell -c 'import os; from datetime import timedelta; from django.utils import timezone; from core.models import InteractiveUser; u=InteractiveUser.objects.get(login_name__iexact=os.environ["USERNAME"]); u.password_validity = timezone.now() + timedelta(minutes=int(os.environ["MINUTES"])); u.save(update_fields=["password_validity"]); print(f"{u.login_name} expires_at={u.password_validity} expired_now={u.is_password_expired}")'
```

Expected immediately:

```text
expired_now=False
```

## 2. Wait 3 minutes, then check expiry

```bash
USERNAME="pwd_expiry_test" python manage.py shell -c 'import os; from core.models import InteractiveUser; u=InteractiveUser.objects.get(login_name__iexact=os.environ["USERNAME"]); print(f"{u.login_name} expired={u.is_password_expired} password_validity={u.password_validity}")'
```

Expected after 3 minutes:

```text
expired=True
```

## 3. Confirm login is rejected

```bash
USERNAME="pwd_expiry_test" PASSWORD="TestExpiry123!" python manage.py shell -c 'import os; from django.test import RequestFactory; from core.services.userServices import user_authentication; req=RequestFactory().post("/");
try:
    user_authentication(req, os.environ["USERNAME"], os.environ["PASSWORD"])
    print("AUTH_OK")
except Exception as e:
    print(type(e).__name__, getattr(e, "detail", str(e)))'
```

Expected after expiry:

```text
AuthenticationFailed PASSWORD_EXPIRED
```

---

# Test user: `edd`

Use this section for the user you created in the UI.

## 1. Make `edd` expire in 3 minutes

```bash

USERNAME="edd" MINUTES=3 python manage.py shell -c 'import os; from datetime import timedelta; from django.utils import timezone; from core.models import InteractiveUser; u=InteractiveUser.objects.get(login_name__iexact=os.environ["USERNAME"]); u.password_validity = timezone.now() + timedelta(minutes=int(os.environ["MINUTES"])); u.save(update_fields=["password_validity"]); print(f"{u.login_name} expires_at={u.password_validity} expired_now={u.is_password_expired}")'


```

Expected immediately:

```text
expired_now=False
```

## 2. Wait 3 minutes, then check expiry

```bash
USERNAME="edd" python manage.py shell -c 'import os; from core.models import InteractiveUser; u=InteractiveUser.objects.get(login_name__iexact=os.environ["USERNAME"]); print(f"{u.login_name} expired={u.is_password_expired} password_validity={u.password_validity}")'
```

Expected after 3 minutes:

```text
expired=True
```

## 3. Confirm login is rejected

Replace `PUT_EDD_PASSWORD_HERE` with the password you used when creating `edd`.

```bash
USERNAME="edd" PASSWORD="PUT_EDD_PASSWORD_HERE" python manage.py shell -c 'import os; from django.test import RequestFactory; from core.services.userServices import user_authentication; req=RequestFactory().post("/");
try:
    user_authentication(req, os.environ["USERNAME"], os.environ["PASSWORD"])
    print("AUTH_OK")
except Exception as e:
    print(type(e).__name__, getattr(e, "detail", str(e)))'
```

Expected after expiry:

```text
AuthenticationFailed PASSWORD_EXPIRED
```

---

# Change the test duration

To test with 1 minute instead of 3 minutes, change:

```bash
MINUTES=3
```

to:

```bash
MINUTES=1
```

---

# Make a user valid again

Use this if you want the user to stop being expired.

For `pwd_expiry_test`:

```bash
USERNAME="pwd_expiry_test" python manage.py shell -c 'import os; from datetime import timedelta; from django.utils import timezone; from core.models import InteractiveUser; from core.apps import CoreConfig; u=InteractiveUser.objects.get(login_name__iexact=os.environ["USERNAME"]); u.password_validity = timezone.now() + timedelta(days=CoreConfig.password_validity_days); u.save(update_fields=["password_validity"]); print(f"{u.login_name} valid_until={u.password_validity} expired_now={u.is_password_expired}")'
```

For `edd`:

```bash
USERNAME="edd" python manage.py shell -c 'import os; from datetime import timedelta; from django.utils import timezone; from core.models import InteractiveUser; from core.apps import CoreConfig; u=InteractiveUser.objects.get(login_name__iexact=os.environ["USERNAME"]); u.password_validity = timezone.now() + timedelta(days=CoreConfig.password_validity_days); u.save(update_fields=["password_validity"]); print(f"{u.login_name} valid_until={u.password_validity} expired_now={u.is_password_expired}")'
```
