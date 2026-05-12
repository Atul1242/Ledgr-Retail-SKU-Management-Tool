# 🆓 Deploy Ledgr to Render - FREE Native Python Setup

## Why Native Python Build?

✅ **Simpler** - No Docker complexity
✅ **Faster builds** - ~2-3 minutes vs 5-10 minutes
✅ **FREE tier compatible** - Works perfectly with free plan
✅ **Auto-deploys** - Push to GitHub = automatic deployment

## 🚀 Quick Setup (5 Minutes)

### Option A: Manual Setup (Recommended for Free Tier)

#### Step 1: Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"PostgreSQL"**
3. Fill in:
   - **Name**: `ledgr-db`
   - **Database**: `ledgr_prod`
   - **User**: `ledgr_prod`
   - **Region**: Oregon (or closest to you)
   - **Plan**: **Free** (90 days free)
4. Click **"Create Database"**
5. **COPY** the **"Internal Database URL"** from the Connections section
   - Format: `postgresql://ledgr_prod:xxxxx@dpg-xxxxx/ledgr_prod`
   - You'll need this in Step 2!

#### Step 2: Create Web Service

1. Click **"New"** → **"Web Service"**
2. Connect GitHub:
   - Click **"Connect account"** if needed
   - Select repository: `HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool`
3. Configure:
   - **Name**: `ledgr-web` (or your choice)
   - **Region**: Same as database (Oregon)
   - **Branch**: `main`
   - **Root Directory**: (leave blank)
   - **Runtime**: **Python 3**
   - **Build Command**: `./build.sh`
   - **Start Command**: `./start.sh`
   - **Plan**: **Free** ⚠️ (spins down after 15 min)

#### Step 3: Add Environment Variables

Scroll down to "Environment Variables" and add these:

**Required:**

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Paste the Internal Database URL from Step 1 |
| `FLASK_SECRET_KEY` | Generate random string (see below) |
| `FLASK_ENV` | `production` |
| `PYTHONUNBUFFERED` | `1` |
| `HIDE_DEMO_CREDENTIALS` | `1` |

**Generate FLASK_SECRET_KEY:**
Run this locally:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Or use: `your-random-secret-key-change-this-12345678`

**Optional (add later if needed):**

| Key | Value |
|-----|-------|
| `OPENROUTER_KEY` | Your OpenRouter API key (for AI chatbot) |
| `DEMO_OWNER_PASSWORD` | Custom password for owner account |
| `DEMO_MANAGER_PASSWORD` | Custom password for manager account |
| `DEMO_SALESMAN_PASSWORD` | Custom password for salesman account |

#### Step 4: Deploy!

1. Click **"Create Web Service"**
2. Watch the build logs (takes ~2-3 minutes)
3. Wait for "Your service is live 🎉"
4. Click the URL (looks like: `https://ledgr-web-xxxx.onrender.com`)
5. Add `/login` to the URL and press Enter
6. Login with demo credentials:
   - **Owner**: `owner` / `owner123`
   - **Manager**: `manager` / `manager123`
   - **Salesman**: `salesman` / `salesman123`

### Option B: Blueprint (Requires Payment)

If you want to use the blueprint (not free):

1. Click **"New"** → **"Blueprint"**
2. Select repository: `HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool`
3. Use file: `render-native.yaml`
4. Click **"Apply"**

## 📊 What You Get (FREE)

✅ **Web Application**
- 750 hours/month free
- Automatic HTTPS
- Auto-deploy on git push
- ⚠️ Spins down after 15 min inactivity
- ⚠️ First request takes ~30s to wake up

✅ **PostgreSQL Database**
- Free for 90 days
- 1GB storage
- Daily backups
- ⚠️ After 90 days: $7/month or gets deleted

✅ **Total Cost**
- **First 90 days**: $0
- **After 90 days**: $7/month (database only)

## 🔄 Auto-Deploy on Git Push

Every time you push to GitHub:
```bash
git add .
git commit -m "your changes"
git push origin main
```
Render automatically detects and deploys! 🚀

## 🎯 Default Login Credentials

After deployment, login at: `https://your-app.onrender.com/login`

**Demo Accounts:**
- **Owner**: `owner` / `owner123`
- **Manager**: `manager` / `manager123`
- **Salesman**: `salesman` / `salesman123`

**Change passwords** by setting environment variables:
- `DEMO_OWNER_PASSWORD`
- `DEMO_MANAGER_PASSWORD`
- `DEMO_SALESMAN_PASSWORD`

## 🐛 Troubleshooting

### Build Fails
**Error**: `Permission denied: ./build.sh`
**Fix**: Files need execute permissions (already set in repo)

**Error**: `No module named 'flask'`
**Fix**: Check `requirements.txt` exists and build command is `./build.sh`

### App Won't Start
**Error**: `FLASK_SECRET_KEY must be set`
**Fix**: Add `FLASK_SECRET_KEY` environment variable

**Error**: `Connection refused` (database)
**Fix**: 
- Use **Internal Database URL** (not External)
- Both services must be in same region

### 502 Bad Gateway
**Cause**: App is still starting
**Fix**: Wait 2-3 minutes, refresh page

### App is Slow
**Cause**: Free tier spins down after 15 min
**Fix**: 
- First request takes ~30s to wake up
- Upgrade to Starter plan ($7/month) for always-on

## 💡 Pro Tips

1. **Keep it awake**: Use a service like [UptimeRobot](https://uptimerobot.com) to ping your app every 5 minutes (free)

2. **Monitor logs**: 
   - Go to your service in Render
   - Click "Logs" tab
   - See real-time application logs

3. **Custom domain**: 
   - Free tier supports custom domains
   - Add in service settings

4. **Environment variables**:
   - Can be changed anytime
   - Service auto-restarts on change

5. **Database backups**:
   - Free tier: daily backups (7 day retention)
   - Paid tier: point-in-time recovery

## 📈 Upgrade Options

**Starter Plan ($7/month per service):**
- ✅ Always on (no spin-down)
- ✅ Faster response times
- ✅ More resources
- ✅ Better for production

**Total for always-on setup:**
- Web Service: $7/month
- Database: $7/month
- **Total: $14/month**

## 🔒 Security Checklist

✅ **Already configured:**
- HTTPS enforced
- Security headers (HSTS, CSP, etc.)
- Secure session cookies
- CSRF protection
- Input validation

⚠️ **You must do:**
- [ ] Set strong `FLASK_SECRET_KEY`
- [ ] Change demo account passwords
- [ ] Never commit `.env` to GitHub
- [ ] Rotate secrets regularly

## 📚 Next Steps

1. ✅ Deploy using steps above
2. ✅ Test login and features
3. ✅ Change demo passwords
4. ✅ Add OpenRouter key for AI chatbot (optional)
5. ✅ Set up custom domain (optional)
6. ✅ Monitor logs and performance

## 🆘 Need Help?

- **Render Docs**: https://render.com/docs
- **GitHub Issues**: Open an issue in your repo
- **Render Support**: support@render.com

---

**Ready to deploy?** Start with Step 1 above! 🚀
