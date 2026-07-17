# Password expiry implementation notes

This document describes the implemented expired-password flow across backend and frontend.

Related test guide:

- `PASSWORD_EXPIRY_TESTING.md`

## Code changes / files changed

### Backend source files

#### `openimis-be-core_py/core/models/user.py`

Password expiry is represented on `InteractiveUser` with:

```python
@property
def is_password_expired(self):
    return bool(self.password_validity and self.password_validity <= timezone.now())
```

Password reset also updates the expiry date when a new password is set:

```python
def set_password(self, raw_password, private_key=token_hex(128)):
    validate_password(raw_password)
    if self._password_was_used(raw_password):
        raise ValidationError(_("core.password_already_used"))
    if self.pk and self.password:
        self.save_history()
    self.private_key = private_key
    ...
    self.password_validity = timezone.now() + timedelta(
        days=CoreConfig.password_validity_days
    )
```

#### `openimis-be-core_py/core/services/userServices.py`

Authentication supports an `allow_expired` flag so the GraphQL login mutation can authenticate expired users and return a controlled expired-password response:

```python
def user_authentication(request, username, password, allow_expired=False):
    ...
    user = authenticate(request, username=username, password=password)
    if user:
        if user.i_user and user.i_user.is_password_expired:
            if allow_expired:
                return user
            raise exceptions.AuthenticationFailed("PASSWORD_EXPIRED")
        return user
```

The reset-link flow validates the token and updates the password:

```python
def set_user_password(request, username, token, password):
    with transaction.atomic():
        user = User.objects.select_for_update().get(
            username__iexact=username.strip()
        )

        if not default_token_generator.check_token(user, token):
            raise ValidationError("Invalid or expired token")

        user.set_password(password)
        user.save()
        user.clear_refresh_tokens()
```

Password reset link generation uses the frontend URL and includes `username` plus `token` query parameters:

```python
token = default_token_generator.make_token(user)
params = urlencode({
    "token": token,
    "username": user.username,
})
reset_url = f"{settings.FRONTEND_URL}/set_password?{params}"
```

#### `openimis-be-core_py/core/schema.py`

`ResetPasswordMutation` was changed to avoid account enumeration. It logs internally but returns success even when the username/email is unknown or email delivery fails:

```python
@classmethod
def mutate_and_get_payload(cls, root, info, username, **input):
    request = info.context

    if is_password_reset_rate_limited(request, username):
        logger.warning("Password reset request was rate limited")
        return ResetPasswordMutation(success=True)

    try:
        reset_user_password(request, username)
    except Exception:
        logger.exception("Unable to process password reset email")

    return ResetPasswordMutation(success=True)
```

`SetPasswordMutation` calls the service and now preserves validation messages instead of always hiding them behind `Failed to set password.`:

```python
try:
    check_lockout(request)
    set_user_password(info.context, username, token, new_password)
    return SetPasswordMutation(success=True)
except GraphQLError as gql_error:
    logger.exception(gql_error)
    return SetPasswordMutation(
        success=False,
        error=gql_error.message,
    )
except ValidationError as validation_error:
    logger.exception(validation_error)
    if hasattr(validation_error, "messages"):
        error_message = "; ".join(str(message) for message in validation_error.messages)
    else:
        error_message = str(validation_error)
    return SetPasswordMutation(
        success=False,
        error=error_message,
    )
except Exception as exc:
    logger.exception(exc)
    return SetPasswordMutation(
        success=False,
        error=gettext_lazy("Failed to set password."),
    )
```

The login mutation returns explicit expired-password fields:

```python
class OpenimisObtainJSONWebToken(mixins.ResolveMixin, JSONWebTokenMutation):
    password_expired = graphene.Boolean()
    reset_email_sent = graphene.Boolean()
    username = graphene.String()
```

and uses:

```python
user = user_authentication(request, username, password, allow_expired=True)
if user.i_user and user.i_user.is_password_expired:
    ...
    return cls(
        password_expired=True,
        reset_email_sent=reset_email_sent,
        refresh_expires_in=0,
        token="",
        username=user.username,
    )
```

Lockout support is handled through `django-axes`:

```python
def check_lockout(request):
    attempts = get_user_attempts(request)
    ...
    if failure_count >= settings.AXES_FAILURE_LIMIT:
        raise GraphQLError(
            f"Too many failed attempts."
            f"Try again in {remaining_minutes} minutes."
        )
```

### Backend configuration files

#### `openimis-be_py/.env`

Relevant settings:

```env
FRONTEND_URL=http://localhost:3000/front

PASSWORD_RESET_RATE_LIMIT_WINDOW=3600
PASSWORD_RESET_RATE_LIMIT_PER_IP=5
PASSWORD_RESET_RATE_LIMIT_PER_ACCOUNT=3

LOGIN_LOCKOUT_FAILURE_LIMIT=5
LOGIN_LOCKOUT_COOLOFF_TIME=5
```

#### `openimis-be_py/openIMIS/openIMIS/settings/security.py`

Lockout settings are read into django-axes:

```python
AXES_FAILURE_LIMIT = int(os.getenv("LOGIN_LOCKOUT_FAILURE_LIMIT", 5))
AXES_COOLOFF_TIME = timedelta(minutes=int(os.getenv("LOGIN_LOCKOUT_COOLOFF_TIME", 5)))
AXES_ENABLED = True if os.environ.get("AXES_ENABLED", "true").lower() == "true" else False
AXES_CACHE = "default"
```

### Frontend source files

#### `openimis-fe-core_js/src/actions.js`

The login mutation requests the expired-password fields:

```js
const mutation = `mutation authenticate($username: String!, $password: String!) {
      tokenAuth(username: $username, password: $password) {
        token
        passwordExpired
        resetEmailSent
        username
      }
    }`;
```

The action maps either GraphQL errors or `tokenAuth.passwordExpired` into a frontend login status:

```js
if (responseErrors?.length > 0) {
  const errorMessage = responseErrors[0].message;
  if (errorMessage === "PASSWORD_EXPIRED") {
    return {
      loginStatus: "CORE_AUTH_PASSWORD_EXPIRED",
      message: "PASSWORD_EXPIRED",
      username: credentials.username,
      resetEmailSent: false,
    };
  }
  dispatch(authError({ message: errorMessage }));
  return { loginStatus: "CORE_AUTH_ERR", message: errorMessage };
}

const authData = responseData?.tokenAuth;
if (authData?.passwordExpired || authData?.password_expired) {
  return {
    loginStatus: "CORE_AUTH_PASSWORD_EXPIRED",
    message: "PASSWORD_EXPIRED",
    username: authData.username || credentials.username,
    resetEmailSent: authData.resetEmailSent || authData.reset_email_sent,
  };
}
```

#### `openimis-fe-core_js/src/pages/LoginPage.js`

The login page shows the password-expired alert instead of treating the response as a normal login failure:

```js
if (loginStatus === "CORE_AUTH_PASSWORD_EXPIRED") {
  const alertMessage = response.resetEmailSent
    ? formatMessage("passwordExpiredResetEmailSent")
    : formatMessage("passwordExpiredResetRequired");
  setServerResponse({ loginStatus, message: null });
  dispatch(coreAlert(formatMessage("passwordExpired.title"), alertMessage));
  setAuthenticating(false);
  return;
}
```

#### `openimis-fe-core_js/src/pages/ForgotPasswordPage.js`

The reset request page calls `resetPassword` and keeps the UI generic:

```js
const { isLoading, error, mutate } = useGraphqlMutation(
  `
  mutation resetPassword($input: ResetPasswordMutationInput!) {
    resetPassword(input: $input) {
      clientMutationId
      success
      error
    }
  }
`,
  {
    wait: false,
  },
);
```

Submit behavior:

```js
try {
  await mutate({ username: username.trim() });
  setDone(true);
} catch (requestError) {
  // The hook stores the error; leave the form visible for retry.
}
```

#### `openimis-fe-core_js/src/pages/SetPasswordPage.js`

The set-password page reads the reset link parameters:

```js
const search = new URLSearchParams(window.location.search);

setCredentials((currentCredentials) => ({
  ...currentCredentials,
  token: search.get("token") || "",
  username: search.get("username") || "",
}));
```

The submit handler supports both GraphQL result shapes:

```js
const result = await mutate({
  username: credentials.username,
  token: credentials.token,
  newPassword: credentials.password,
});
const setPasswordResult = result?.setPassword || result?.payload?.data?.setPassword;
if (setPasswordResult?.success) {
  history.push("/");
} else {
  handleSetPasswordError(setPasswordResult?.error || formatMessage("error"));
}
```

This replaced the unsafe access:

```js
result?.setPassword.success
```

#### `openimis-fe-core_js/src/translations/en.json`

Relevant user-facing messages:

```json
{
  "core.LoginPage.passwordExpired.title": "Password expired",
  "core.LoginPage.passwordExpiredResetEmailSent": "Your password has expired. A password reset link has been sent to your registered email address.",
  "core.LoginPage.passwordExpiredResetRequired": "Your password has expired and must be reset. Use Forgot Password to request a reset link."
}
```

### Local development generated/installed files

The main frontend app consumes `@openimis/fe-core` from:

```text
openimis-fe_js/node_modules/@openimis/fe-core
```

During local testing, the installed copy and built artifacts were refreshed so the app stopped serving stale code:

```text
openimis-fe_js/node_modules/@openimis/fe-core/src/pages/SetPasswordPage.js
openimis-fe_js/node_modules/@openimis/fe-core/dist/index.js
openimis-fe_js/node_modules/@openimis/fe-core/dist/index.es.js
openimis-fe_js/node_modules/@openimis/fe-core/bundle.js
```

These are development artifacts, not the primary source of truth. The primary source is `openimis-fe-core_js/src`.

## Goal

When a user logs in with a correct username and password, but their `InteractiveUser.password_validity` is in the past, the system should:

1. reject normal login,
2. return an explicit expired-password state to the frontend,
3. send or request a password reset email,
4. allow the user to set a new password from the reset link,
5. avoid leaking whether a reset username/email exists.

## Backend implementation

### Password expiry source of truth

The expiry check is based on the interactive user record:

- model: `core.models.InteractiveUser`
- field: `password_validity`
- property used by the flow: `is_password_expired`

A user is expired when `password_validity` is in the past.

### Authentication service

File:

- `openimis-be-core_py/core/services/userServices.py`

Function:

```python
def user_authentication(request, username, password, allow_expired=False):
```

Behavior:

- missing username/password raises `ParseError`
- JWT cookies are cleared before authentication
- Django authentication is attempted with the provided credentials
- if credentials are valid and the password is expired:
  - `allow_expired=False` raises `AuthenticationFailed("PASSWORD_EXPIRED")`
  - `allow_expired=True` returns the authenticated user so the caller can handle the expired state
- if credentials are invalid, it raises `AuthenticationFailed("INCORRECT_CREDENTIALS")`

Important: expired-password handling only happens after credentials are valid. If the password is wrong, the user sees the normal incorrect username/password flow.

### Login GraphQL mutation

File:

- `openimis-be-core_py/core/schema.py`

Class:

```python
class OpenimisObtainJSONWebToken(mixins.ResolveMixin, JSONWebTokenMutation):
```

Additional response fields:

```python
password_expired = graphene.Boolean()
reset_email_sent = graphene.Boolean()
username = graphene.String()
```

Login uses:

```python
user = user_authentication(request, username, password, allow_expired=True)
```

If the user is expired:

- it attempts to send a reset email via `reset_user_password`
- it rate-limits the reset email request
- it returns:

```python
password_expired=True
reset_email_sent=<bool>
refresh_expires_in=0
token=""
username=user.username
```

If the user is not expired, it continues with the normal JWT login flow.

### Password reset request mutation

File:

- `openimis-be-core_py/core/schema.py`

Class:

```python
class ResetPasswordMutation(graphene.relay.ClientIDMutation):
```

Behavior:

- accepts `username`
- checks password-reset rate limiting
- calls `reset_user_password(request, username)`
- always returns `success=True` unless the mutation itself fails catastrophically

Reason: the reset endpoint must not disclose whether the account exists, has an email address, or whether SMTP accepted the email.

### Set password mutation

File:

- `openimis-be-core_py/core/schema.py`

Class:

```python
class SetPasswordMutation(graphene.relay.ClientIDMutation):
```

Input:

```python
username
token
new_password
```

Behavior:

- logs reset-password attempt
- checks lockout
- calls `set_user_password(info.context, username, token, new_password)`
- returns:

```python
success=True
```

or:

```python
success=False
error=<message>
```

### Set password service

File:

- `openimis-be-core_py/core/services/userServices.py`

Function:

```python
def set_user_password(request, username, token, password):
```

Expected responsibilities:

- find the interactive user
- validate the reset token with Django's token generator
- set the new password
- update password validity
- clear refresh tokens
- clear JWT cookies

## Frontend implementation

### Login action

File:

- `openimis-fe-core_js/src/actions.js`

Mutation:

```graphql
mutation authenticate($username: String!, $password: String!) {
  tokenAuth(username: $username, password: $password) {
    token
    passwordExpired
    resetEmailSent
    username
  }
}
```

Response handling:

- if GraphQL returns `PASSWORD_EXPIRED`, frontend returns:

```js
{
  loginStatus: "CORE_AUTH_PASSWORD_EXPIRED",
  message: "PASSWORD_EXPIRED",
  username: credentials.username,
  resetEmailSent: false,
}
```

- if `tokenAuth.passwordExpired` is true, frontend returns:

```js
{
  loginStatus: "CORE_AUTH_PASSWORD_EXPIRED",
  message: "PASSWORD_EXPIRED",
  username: authData.username || credentials.username,
  resetEmailSent: authData.resetEmailSent || authData.reset_email_sent,
}
```

- if no token is returned and password is not expired, frontend treats it as incorrect credentials.

### Login page UX

File:

- `openimis-fe-core_js/src/pages/LoginPage.js`

When login returns:

```js
loginStatus === "CORE_AUTH_PASSWORD_EXPIRED"
```

the page shows a password-expired alert.

If `resetEmailSent` is true, the user sees the message that a reset link was sent.

If `resetEmailSent` is false, the user is told to use Forgot Password to request a reset link.

### Set password page

File:

- `openimis-fe-core_js/src/pages/SetPasswordPage.js`

The page reads `username` and `token` from the URL query string.

On submit, it calls:

```js
mutate({
  username: credentials.username,
  token: credentials.token,
  newPassword: credentials.password,
})
```

The mutation result can come back in more than one shape depending on the GraphQL helper configuration:

- direct GraphQL data shape:

```js
result.setPassword
```

- Redux API action shape:

```js
result.payload.data.setPassword
```

The page must support both:

```js
const setPasswordResult = result?.setPassword || result?.payload?.data?.setPassword;

if (setPasswordResult?.success) {
  history.push("/");
} else {
  handleSetPasswordError(setPasswordResult?.error || formatMessage("error"));
}
```

Do not use:

```js
result?.setPassword.success
```

That only guards `result`, not `setPassword`, and causes:

```text
Cannot read properties of undefined (reading 'success')
```

when the mutation result is returned as a Redux action.

## Local frontend package gotcha

The main frontend app uses:

```json
"@openimis/fe-core": "file:../openimis-fe-core_js"
```

inside:

```text
openimis-fe_js/package.json
```

During local development, the running app may compile from:

```text
openimis-fe_js/node_modules/@openimis/fe-core/dist/index.es.js
```

not directly from:

```text
openimis-fe-core_js/src
```

After changing `openimis-fe-core_js`, make sure the installed package copy and built artifacts used by `openimis-fe_js` are refreshed.

Useful checks:

```bash
rg -n "result\\.setPassword\\.success|setPasswordResult" \
  openimis-fe_js/node_modules/@openimis/fe-core/dist/index.es.js \
  openimis-fe_js/node_modules/@openimis/fe-core/dist/index.js \
  openimis-fe_js/node_modules/@openimis/fe-core/src/pages/SetPasswordPage.js
```

If the browser still serves stale code, clear the frontend compile cache and restart:

```bash
cd /home/edweard/PyCharmMiscProject/Coremis/openimis-fe_js
rm -rf node_modules/.cache
yarn start
```

Verify the live bundle:

```bash
python - <<'PY'
from urllib.request import urlopen
data = urlopen("http://localhost:3000/front/static/js/bundle.js", timeout=10).read().decode("utf-8", "ignore")
for needle in ["result.setPassword.success", "result?.setPassword.success", "setPasswordResult"]:
    print(needle, data.find(needle))
PY
```

Expected:

```text
result.setPassword.success -1
result?.setPassword.success -1
setPasswordResult <non-negative index>
```

## Manual expiry commands

Run from:

```bash
cd /home/edweard/PyCharmMiscProject/Coremis/openimis-be_py/openIMIS
```

Set `edd` to expire in one minute:

```bash
set -a && source ../.env && set +a
USERNAME="edd" MINUTES=1 ../.venv/bin/python manage.py shell -c 'import os; from datetime import timedelta; from django.utils import timezone; from core.models import InteractiveUser; u=InteractiveUser.objects.get(login_name__iexact=os.environ["USERNAME"]); u.password_validity = timezone.now() + timedelta(minutes=int(os.environ["MINUTES"])); u.save(update_fields=["password_validity"]); print(f"{u.login_name} expires_at={u.password_validity} expired_now={u.is_password_expired}")'
```

Check whether `edd` is expired:

```bash
set -a && source ../.env && set +a
USERNAME="edd" ../.venv/bin/python manage.py shell -c 'import os; from core.models import InteractiveUser; u=InteractiveUser.objects.get(login_name__iexact=os.environ["USERNAME"]); print(f"{u.login_name} expired={u.is_password_expired} password_validity={u.password_validity}")'
```

## Expected end-to-end behavior

1. User logs in with correct credentials.
2. Backend detects expired `password_validity`.
3. Backend returns `passwordExpired=true`, no token.
4. Frontend shows the password-expired alert.
5. User follows reset link or requests one via Forgot Password.
6. User submits new password on Set Password page.
7. Frontend checks `setPasswordResult?.success`.
8. On success, user is redirected to login.

If the login form shows incorrect credentials instead of expired password, verify the entered password is correct for that user. Expiry is only checked after successful credential authentication.
