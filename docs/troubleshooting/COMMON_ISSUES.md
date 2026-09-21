# Troubleshooting Web Query Interface

## HTTP 403 Error

If you're getting a 403 "Access Denied" error when trying to access `http://localhost:5000`:

### Solution 1: Try 127.0.0.1 instead

Instead of `localhost`, try:

```text
http://127.0.0.1:5000
```

### Solution 2: Check macOS Firewall

1. Go to System Settings → Network → Firewall
2. Make sure Python is allowed through the firewall
3. Or temporarily disable the firewall to test

### Solution 3: Use a different port

Edit `web_query_app.py` and change `port=5000` to `port=5001` or another port.

### Solution 4: Check if port is in use

```bash
lsof -ti:5000 | xargs kill -9
```

### Solution 5: Test the server

After starting the server, test it with:

```bash
curl http://127.0.0.1:5000/test
```

If this returns `{"status":"ok","message":"Server is working!"}`, the server is working and the issue is with your browser.

### Solution 6: Browser-specific fixes

- **Chrome/Safari**: Try clearing cache or using incognito/private mode
- **Firefox**: Check if there are any security extensions blocking localhost
- Try a different browser

### Solution 7: Check server logs

Look at the terminal where you ran `python3 web_query_app.py` - it should show any errors.

## Common Issues

### Port already in use

```bash
# Find what's using port 5000
lsof -i:5000

# Kill it
lsof -ti:5000 | xargs kill -9
```

### Database not found

Make sure `genetic_profile.db` exists in the same directory as `web_query_app.py`

### Module not found

```bash
pip3 install flask flask-cors
```
