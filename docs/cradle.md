# Cradle Hub

[cradle.app](https://cradle.app) · The God Particle, The Spirit, The Prince.

The plugins work normally once you're signed in. Getting signed in has two
separate problems.

## Blank window on launch

Cradle Hub starts, the process is alive, and the window is empty. It isn't
Electron — it's their own engine — so the usual `--disable-gpu` flags don't apply.

Cause is Wine stubbing `DxgiOutput::WaitForVBlank`. A vsync-driven render loop
calls it, gets an error, and exits. DXVK implements it.

**Install DXVK in a throwaway prefix for the Hub, not in your DAW prefix.** DXVK
is prefix-wide.

```bash
WINEPREFIX=$HOME/.cradle-hub winetricks -q dxvk
```

The *plugins* don't need DXVK. Only the Hub window does.

## Sign-in that never completes

Click sign in, the browser opens, you authenticate, nothing happens. The Hub sits
unsigned-in forever.

It's a custom URL scheme handoff and the handler isn't registered on Linux.

**The scheme is `app.cradle`, not `cradle`.** That's the whole problem — everyone
guesses the brand name.

Found with F12 → Network, signing in, and reading the `303`:

```
location: app.cradle://oidc/cb?code=...
```

Register that exact string in three places:

1. A `.desktop` file with `MimeType=x-scheme-handler/app.cradle;` pointing at a
   script that launches the Hub
2. `xdg-mime default <your>.desktop x-scheme-handler/app.cradle`
3. Firefox's `network.protocol-handler.*` prefs, so it offers to open the app
   instead of silently dropping the callback

After that, signing in shows an "allow this site to open the application" prompt
and completes.

## Generalisable version

If any Wine app signs you in through your browser and the handoff silently fails,
open devtools, catch the redirect, and read the `location:` header. The scheme is
often not what the brand is called. Don't guess it.
