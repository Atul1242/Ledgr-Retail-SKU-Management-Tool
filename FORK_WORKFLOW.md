# 🔱 Fork Workflow Guide

## ✅ Current Setup

Your local repository is now configured to work with your fork:

```
origin   → https://github.com/Atul1242/Ledgr-Retail-SKU-Management-Tool.git (YOUR FORK)
upstream → https://github.com/HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool.git (ORIGINAL)
```

## 📋 Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FORK WORKFLOW                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  UPSTREAM (Original)                                         │
│  HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool          │
│         │                                                    │
│         │ (1) Fork                                          │
│         ↓                                                    │
│  ORIGIN (Your Fork)                                         │
│  Atul1242/Ledgr-Retail-SKU-Management-Tool                 │
│         │                                                    │
│         │ (2) Clone                                         │
│         ↓                                                    │
│  LOCAL (Your Machine)                                       │
│  D:\Ledgr-Retail-SKU-Management-Tool                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Daily Workflow

### 1. Start Your Work

Before making changes, sync with upstream:

```bash
# Fetch latest changes from upstream
git fetch upstream

# Merge upstream changes into your main branch
git merge upstream/main

# Push updates to your fork
git push origin main
```

### 2. Make Changes

Work directly on main branch (as you requested):

```bash
# Make your changes to files
# Edit code, test locally, etc.

# Check what changed
git status

# Stage your changes
git add .

# Commit with descriptive message
git commit -m "Description of your changes"
```

### 3. Push to Your Fork

```bash
# Push to your fork (origin)
git push origin main
```

### 4. Test on Railway

Deploy from your fork:
- Railway → Connect to `Atul1242/Ledgr-Retail-SKU-Management-Tool`
- Test thoroughly
- Make sure everything works

### 5. Merge Back to Original (When Ready)

Once everything works on your fork:

**Option A: Pull Request (Recommended)**
1. Go to your fork on GitHub: https://github.com/Atul1242/Ledgr-Retail-SKU-Management-Tool
2. Click "Contribute" → "Open pull request"
3. Add description of changes
4. Submit PR to original repo
5. Original owner reviews and merges

**Option B: Direct Push to Upstream (If you have access)**
```bash
# Push directly to upstream
git push upstream main
```

## 📝 Common Commands

### Check Remote Configuration
```bash
git remote -v
```

### Sync with Upstream
```bash
# Fetch upstream changes
git fetch upstream

# Merge into your main
git merge upstream/main

# Or rebase (cleaner history)
git rebase upstream/main
```

### Push to Your Fork
```bash
git push origin main
```

### Push to Original (after testing)
```bash
git push upstream main
```

### Check Current Branch
```bash
git branch
```

### View Commit History
```bash
git log --oneline -10
```

### Undo Last Commit (keep changes)
```bash
git reset --soft HEAD~1
```

### Discard All Local Changes
```bash
git reset --hard HEAD
```

## 🔄 Keeping Your Fork Updated

### Method 1: Via Git (Recommended)
```bash
# Fetch from upstream
git fetch upstream

# Merge upstream/main into your main
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

### Method 2: Via GitHub UI
1. Go to your fork: https://github.com/Atul1242/Ledgr-Retail-SKU-Management-Tool
2. Click "Sync fork" button
3. Click "Update branch"
4. Pull locally: `git pull origin main`

## 🧪 Testing Workflow

### 1. Test Locally First
```bash
# Run the app locally
python app.py

# Or with Docker
docker build -t ledgr-test .
docker run -p 5000:5000 ledgr-test
```

### 2. Test on Railway (Your Fork)
- Deploy from `Atul1242/Ledgr-Retail-SKU-Management-Tool`
- Test all features
- Check logs for errors
- Verify database connections

### 3. Merge to Original (When Stable)
- Create PR or push to upstream
- Original repo gets tested version

## 🎯 Current Status

✅ **Completed:**
- Fork created: `Atul1242/Ledgr-Retail-SKU-Management-Tool`
- Local repo configured with origin (your fork) and upstream (original)
- All Railway deployment fixes pushed to your fork
- Ready for testing

📋 **Next Steps:**
1. Deploy your fork to Railway
2. Test thoroughly
3. Make any needed changes
4. Push changes to your fork
5. Test again
6. When stable, merge back to original

## 🔧 Troubleshooting

### "Permission denied" when pushing to upstream
- You need write access to original repo
- Use Pull Request instead

### Merge conflicts
```bash
# Fetch upstream
git fetch upstream

# Try merge
git merge upstream/main

# If conflicts, resolve manually
# Edit conflicted files
git add .
git commit -m "Resolve merge conflicts"
```

### Reset to upstream state
```bash
# Discard all local changes
git fetch upstream
git reset --hard upstream/main
git push -f origin main
```

### Check if fork is behind upstream
```bash
git fetch upstream
git log HEAD..upstream/main --oneline
```

## 📚 Git Cheat Sheet

| Command | Description |
|---------|-------------|
| `git status` | Check current state |
| `git add .` | Stage all changes |
| `git commit -m "msg"` | Commit changes |
| `git push origin main` | Push to your fork |
| `git push upstream main` | Push to original |
| `git fetch upstream` | Get upstream changes |
| `git merge upstream/main` | Merge upstream into local |
| `git pull origin main` | Pull from your fork |
| `git log --oneline -10` | View recent commits |
| `git remote -v` | View remotes |

## 🎓 Best Practices

1. **Always sync before starting work**
   ```bash
   git fetch upstream
   git merge upstream/main
   ```

2. **Commit often with clear messages**
   ```bash
   git commit -m "Fix: Railway PORT variable issue"
   ```

3. **Test before pushing**
   - Run locally
   - Check for errors
   - Verify functionality

4. **Keep commits atomic**
   - One feature/fix per commit
   - Makes rollback easier

5. **Use descriptive commit messages**
   - Bad: "fix stuff"
   - Good: "Fix DATABASE_URL parsing for Railway deployment"

## 🚨 Important Notes

- **Work on main branch** (as requested)
- **Test on your fork first** before merging to original
- **Your fork**: `Atul1242/Ledgr-Retail-SKU-Management-Tool`
- **Original**: `HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool`
- **Railway should deploy from your fork** for testing

## 📞 Quick Reference

**Your Fork URL:**
```
https://github.com/Atul1242/Ledgr-Retail-SKU-Management-Tool
```

**Original Repo URL:**
```
https://github.com/HoneyBadger-010/Ledgr-Retail-SKU-Management-Tool
```

**Local Path:**
```
D:\Ledgr-Retail-SKU-Management-Tool
```

---

**Ready to start?** Make your changes, test on Railway with your fork, then merge back when stable! 🚀
