# 🌐 GitHub Pages Setup - Get Your Public Link!

Get a free, permanent public link like: `https://yourusername.github.io/predictionmlstock/`

## Quick Setup (2 minutes)

### Step 1: Push to GitHub

Your code is already on branch `claude/ml-trading-system-ls0cM`.

If you haven't pushed to your main branch yet:

```bash
# Merge to main (or master)
git checkout main
git merge claude/ml-trading-system-ls0cM
git push origin main
```

### Step 2: Enable GitHub Pages

1. Go to your repository on GitHub:
   - `https://github.com/YOUR_USERNAME/predictionmlstock`

2. Click **Settings** (top right)

3. Scroll down to **Pages** (left sidebar)

4. Under **Source**, select:
   - Source: `Deploy from a branch`
   - Branch: `main` (or `master`)
   - Folder: `/frontend`
   - Click **Save**

5. Wait 1-2 minutes for deployment

6. Your site will be live at:
   ```
   https://YOUR_USERNAME.github.io/predictionmlstock/
   ```

### Step 3: Share the Link

Your dashboard is now publicly accessible! Share with anyone:
- `https://YOUR_USERNAME.github.io/predictionmlstock/`

## Alternative: GitHub Actions (Automatic)

I've already created a workflow file that auto-deploys!

### Enable GitHub Actions

1. Go to repository **Settings**
2. **Actions** → **General** (left sidebar)
3. Under **Actions permissions**, select:
   - ✅ Allow all actions and reusable workflows
4. Click **Save**

### Enable Pages with Actions

1. **Settings** → **Pages**
2. Under **Source**, select:
   - Source: `GitHub Actions`
3. The workflow will deploy automatically on push!

### Trigger Deployment

The deployment happens automatically when you push changes to:
- `main` branch
- `master` branch
- `claude/ml-trading-system-ls0cM` branch

Manual trigger:
1. Go to **Actions** tab
2. Select **Deploy Frontend to GitHub Pages**
3. Click **Run workflow**
4. Choose your branch
5. Click **Run workflow**

## Verify Deployment

After 1-2 minutes, check:

```bash
# Visit your site
https://YOUR_USERNAME.github.io/predictionmlstock/
```

You should see the ML Trading System dashboard!

## Troubleshooting

### Issue: 404 Not Found

**Solution 1: Check Settings**
- Settings → Pages
- Ensure source is set correctly
- Wait 2-3 minutes after saving

**Solution 2: Check Branch**
- Verify `frontend/` folder exists in your branch
- Push changes if missing

**Solution 3: Clear Cache**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

### Issue: Deployment Failed

**Check Actions**
1. Go to **Actions** tab
2. Click on the failed workflow
3. Check error logs
4. Common fixes:
   - Enable Pages in Settings
   - Grant workflow permissions

### Issue: Old Version Showing

**Clear Cache:**
- Hard refresh browser
- Or add `?v=2` to URL: `https://...github.io/predictionmlstock/?v=2`

## Custom Domain (Optional)

Want `trading.yourdomain.com` instead?

1. Buy a domain (Namecheap, GoDaddy, etc.)

2. Add DNS records:
```
Type: CNAME
Name: trading (or www)
Value: YOUR_USERNAME.github.io
```

3. In GitHub:
   - Settings → Pages
   - Custom domain: `trading.yourdomain.com`
   - Enable HTTPS

## Next Steps

Once your site is live:

1. ✅ Test on mobile
2. ✅ Share the link
3. ✅ Enable HTTPS (automatic)
4. ✅ Add to your portfolio

## Quick Reference

**Your URLs:**
- Local: `http://localhost:8000`
- Network: `http://21.0.0.42:8000` (same WiFi)
- Public: `https://YOUR_USERNAME.github.io/predictionmlstock/`

**Documentation:**
- Full guide: `MOBILE_ACCESS.md`
- Main README: `README.md`
- Deployment: `DEPLOYMENT.md`

---

**Get your public link in under 2 minutes! 🚀**
