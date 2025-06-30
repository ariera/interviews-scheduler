# Deploying Interview Scheduler Online (Free)

## Overview
This guide shows how to deploy your interview scheduler for free using:
- **GitHub Pages** (Frontend - Free)
- **Render** (Backend API - Free tier)

## Step 1: Prepare Your Repository

### 1.1 Create a GitHub Repository
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/interview-scheduler.git
git push -u origin main
```

### 1.2 API Backend
The API backend is already prepared in the `api/` folder with `app.py`.

## Step 2: Deploy Backend to Render

### 2.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Create a new Web Service

### 2.2 Configure Render Service
- **Name**: `interview-scheduler-api`
- **Repository**: Your GitHub repo
- **Root Directory**: `api`
- **Runtime**: Python 3
- **Build Command**: `pip install -r ../requirements.txt`
- **Start Command**: `gunicorn app:app`

### 2.3 Environment Variables
Add these in Render dashboard:
- `PORT`: `10000` (Render will override this)

## Step 3: Frontend is Ready

The frontend is already prepared in the `docs/` folder with `index.html`.

## Step 4: Configure GitHub Pages

### 4.1 Enable GitHub Pages
1. Go to your repository settings
2. Scroll down to "Pages" section
3. Select "Deploy from a branch"
4. Choose "main" branch and "/docs" folder
5. Click "Save"

### 4.2 Update API URL
In `docs/index.html`, replace `'https://your-render-app.onrender.com'` with your actual Render URL.

## Step 5: Deploy

### 5.1 Push Changes
```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### 5.2 Verify Deployment
- Frontend: `https://YOUR_USERNAME.github.io/interview-scheduler/`
- Backend: Your Render URL

## Step 6: Test Your Deployment

### 6.1 Test Health Endpoint
The easiest way to verify your backend is working is to test the health endpoint:

```bash
# Test health endpoint
curl -X GET https://YOUR_RENDER_APP.onrender.com/api/health
```

**Expected Response:**
```json
{
  "service": "interview-scheduler-api",
  "status": "healthy",
  "version": "1.0.0"
}
```

### 6.2 Test Configuration Validation
Test that the API can validate configurations:

```bash
# Test configuration validation
curl -X POST https://YOUR_RENDER_APP.onrender.com/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "num_candidates": 2,
      "panels": {"Technical": "45min", "HR": "30min"},
      "order": ["Technical", "HR"],
      "availabilities": {"Technical": "9:00-17:00", "HR": "9:00-17:00"}
    }
  }'
```

**Expected Response:**
```json
{
  "message": "Configuration is valid",
  "valid": true
}
```

### 6.3 Test Schedule Generation
Test the core scheduling functionality:

```bash
# Test single schedule generation
curl -X POST https://YOUR_RENDER_APP.onrender.com/api/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "num_candidates": 2,
      "panels": {"Technical": "45min", "HR": "30min"},
      "order": ["Technical", "HR"],
      "availabilities": {"Technical": "9:00-17:00", "HR": "9:00-17:00"},
      "max_gap_minutes": 15
    }
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "session_id": "uuid-here",
  "solution": {
    "schedules": {
      "candidate_1": [...],
      "candidate_2": [...]
    },
    "summary": {
      "status": "OPTIMAL",
      "day_ends_at": "10:30",
      "max_gap_enforced": "15 minutes"
    }
  }
}
```

### 6.4 Test Web Interface
1. Open your frontend URL: `https://YOUR_USERNAME.github.io/interview-scheduler/`
2. Upload a YAML configuration file from the `examples/` folder
3. Click "Generate Schedule" to test the full workflow

### 6.5 Troubleshooting
If the health endpoint fails:
- Check Render dashboard for deployment status
- Verify the service is running (green status)
- Check logs for any error messages
- Ensure the API URL in `docs/index.html` is correct

## Alternative: Railway Deployment

If you prefer a simpler all-in-one solution:

1. Go to [railway.app](https://railway.app)
2. Connect your GitHub account
3. Create new project from GitHub repo
4. Railway will auto-detect your Flask app in the `api/` folder
5. Deploy with one click

## Cost Comparison

| Platform | Cost | Limitations |
|----------|------|-------------|
| GitHub Pages + Render | Free | 750 hours/month on Render |
| Railway | Free | $5 credit/month |
| Vercel + Supabase | Free | Limited API calls |
| Heroku | $7/month | No free tier |

## Maintenance

- **GitHub Pages**: Updates automatically on push
- **Render**: Updates automatically on push
- **Monitoring**: Check Render dashboard for usage
- **Scaling**: Upgrade to paid plans if needed

Your interview scheduler will be live and accessible to anyone with an internet connection!