# Connecting Gmail (engine A)

Ascend 2.0's engine A reads your job mail with a Google sign-in you own. It takes about ten minutes, once. After that, `tools/gmail_sync.py` syncs on a schedule with no Claude session and no tokens.

If you would rather not set this up, use engine C, which reads Gmail through the claude.ai Gmail connector inside a Claude session. It works the same way but costs tokens on every sync.

## What Ascend can and cannot do with this access

- **Read-only.** The only scope requested is `gmail.readonly`. Ascend cannot send, delete, label or change anything.
- **Your client, your project.** The OAuth client lives in your Google Cloud project. No third-party app is involved.
- **Kept locally:** sender, subject, date, labels and the first 2,000 characters of each message, in `workspace/<name>/data/mail.jsonl` (gitignored). Never attachments. Your sent mail, drafts, spam and trash are skipped.
- **The refresh token** is stored in the macOS Keychain under the service name `ascend-gmail`, not in a file.
- **Revoke any time** at [myaccount.google.com/permissions](https://myaccount.google.com/permissions). The next sync notices and tells you to reconnect.

## One-time setup

1. Open [console.cloud.google.com](https://console.cloud.google.com/) and create a project (for example "ascend-personal").
2. **APIs & Services → Library →** search for **Gmail API** and enable it.
3. **APIs & Services → OAuth consent screen:**
   - User type: **External**, publishing status: **Testing**.
   - Add your own Gmail address under **Test users**. Only test users can sign in, which here means only you.
   - Scopes: add `https://www.googleapis.com/auth/gmail.readonly`.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID:**
   - Application type: **Desktop app**.
   - Download the JSON.
5. Save it as `workspace/<your-name>/gmail-client.json`. The `workspace/` folder is gitignored, so the file never reaches git.
6. Connect:

   ```
   python3 tools/gmail_sync.py connect workspace/<your-name>
   ```

   Your browser opens Google's sign-in. Google will warn that the app is unverified, because it is your own private app in testing mode. Choose **Continue**, approve read-only access, and close the tab when it says you are connected.

7. First sync (the last 30 days), then classify, update job statuses and rebuild the hub, all at zero tokens:

   ```
   python3 tools/gmail_sync.py sync workspace/<your-name> --then-classify
   ```

## Day to day

```
python3 tools/gmail_sync.py sync workspace/<your-name> --then-classify   # new mail only
python3 tools/gmail_sync.py status workspace/<your-name>                  # connected? last sync?
```

Testing-mode refresh tokens from Google can expire after seven days. If a sync exits with code 4, run `connect` again.
