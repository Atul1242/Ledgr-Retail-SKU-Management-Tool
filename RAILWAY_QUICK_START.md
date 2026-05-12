# 🚂 Railway Deployment - Quick Start

## ✅ Repository is Ready!

All fixes have been applied and pushed to GitHub:
- ✅ Dockerfile uses `$PORT` variable (not hardcoded 5000)
- ✅ Gunicorn binds to Railway's dynamic PORT
- ✅ Health check uses PORT variable
- ✅ railway.toml configuration added
- ✅ Ready for PostgreSQL via `${{Postgres.DATABASE_URL}}`

## 🚀 Deploy in 5 Minutes

### 1. Sign Up (30 seconds)
- Go to [railway.app](https://railway.app)
- Click "Login with GitHub"
- Authorize Railway

### 2. Create Project (1 minute)
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose: `HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool`

### 3. Add Database (30 seconds)
- Click "+ New" → "Database" → "Add PostgreSQL"
- Done! Railway creates it automatically

### 4. Set Environment Variables (2 minutes)
Click on your web service → "Variables" tab → Add these:

```bash
# REQUIRED - Copy these exactly:
DATABASE_URL = ${{Postgres.DATABASE_URL}}
FLASK_SECRET_KEY = [generate random 32+ chars]
FLASK_ENV = production
PYTHONUNBUFFERED = 1
HIDE_DEMO_CREDENTIALS = 1
```

**Generate FLASK_SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Or click the 🎲 dice icon in Railway to generate random value.

### 5. Get Your URL (1 minute)
- Go to "Settings" → "Networking"
- Click "Generate Domain"
- Visit: `https://your-url.up.railway.app/login`

## 🎯 That's It!

Your app is now live with:
- ✅ PostgreSQL database
- ✅ Automatic HTTPS
- ✅ Auto-deploy on git push
- ✅ $5 free credit/month
- ✅ No spin-down (stays running 24/7)

## 🔑 Login Credentials

Default demo accounts:
- **Owner**: `owner` / `owner123`
- **Manager**: `manager` / `manager123`
- **Salesman**: `salesman` / `salesman123`

## 💡 Key Differences from Render

| Feature | Railway | Render |
|---------|---------|--------|
| Free Tier | $5 credit/month | Spins down after 15 min |
| Setup | 5 minutes | 15+ minutes |
| Database URL | `${{Postgres.DATABASE_URL}}` | Manual copy/paste |
| PORT | Auto via `$PORT` | Hardcoded 5000 |
| Deployment | Instant | Slower |
| Community | Very active Discord | Less responsive |

## 🐛 Troubleshooting

**App crashes on startup?**
- Check: `DATABASE_URL = ${{Postgres.DATABASE_URL}}` (with double `{{}}`)
- Check: `FLASK_SECRET_KEY` is set

**Health check fails?**
- Wait 2-3 minutes for first deploy
- Check logs for errors

**Can't connect to database?**
- Verify both services are in same project
- Use `${{Postgres.DATABASE_URL}}` not a hardcoded URL

## 📚 Full Guide

See `RAILWAY_DEPLOYMENT.md` for:
- Detailed troubleshooting
- Custom domain setup
- Background worker setup
- Monitoring and alerts
- Cost optimization

---

**Need help?** Railway Discord is super responsive: [discord.gg/railway](https://discord.gg/railway)
