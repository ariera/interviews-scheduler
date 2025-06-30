#!/bin/bash

# Interview Scheduler Deployment Script
# This script helps you deploy your interview scheduler online

set -e

echo "🚀 Interview Scheduler Deployment Script"
echo "========================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git add .
    git commit -e "Initial commit"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if remote origin exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo "🔗 Please set up your GitHub repository:"
    echo "1. Create a new repository on GitHub"
    echo "2. Run: git remote add origin https://github.com/YOUR_USERNAME/interview-scheduler.git"
    echo "3. Run: git push -u origin main"
    echo ""
    read -p "Have you created the GitHub repository? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Please run the git commands above to connect to your repository."
    fi
else
    echo "✅ GitHub remote already configured"
fi

echo ""
echo "📋 Deployment Options:"
echo "1. GitHub Pages + Render (Recommended - Free)"
echo "2. Railway (All-in-one - Free tier)"
echo "3. Manual deployment guide"

read -p "Choose deployment option (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        echo ""
        echo "🎯 GitHub Pages + Render Deployment"
        echo "=================================="
        echo ""
        echo "Step 1: Deploy Backend to Render"
        echo "1. Go to https://render.com"
        echo "2. Sign up with your GitHub account"
        echo "3. Click 'New Web Service'"
        echo "4. Connect your GitHub repository"
        echo "5. Configure:"
        echo "   - Name: interview-scheduler-api"
        echo "   - Root Directory: api"
        echo "   - Runtime: Python 3"
        echo "   - Build Command: pip install -r requirements.txt"
        echo "   - Start Command: gunicorn app:app"
        echo ""
        echo "Step 2: Update API URL"
        echo "After Render deployment, update the API_URL in docs/index.html"
        echo ""
        echo "Step 3: Enable GitHub Pages"
        echo "1. Go to your repository settings"
        echo "2. Scroll to 'Pages' section"
        echo "3. Source: Deploy from a branch"
        echo "4. Branch: main, Folder: /docs"
        echo ""
        echo "Step 4: Push Changes"
        echo "git add ."
        echo "git commit -m 'Add deployment configuration'"
        echo "git push origin main"
        ;;
    2)
        echo ""
        echo "🚂 Railway Deployment"
        echo "===================="
        echo ""
        echo "1. Go to https://railway.app"
        echo "2. Sign up with your GitHub account"
        echo "3. Click 'New Project'"
        echo "4. Select 'Deploy from GitHub repo'"
        echo "5. Select your interview-scheduler repository"
        echo "6. Railway will auto-detect your Flask app"
        echo "7. Deploy with one click!"
        echo ""
        echo "Your app will be available at: https://your-app-name.railway.app"
        ;;
    3)
        echo ""
        echo "📖 Manual Deployment Guide"
        echo "========================="
        echo ""
        echo "See deploy_github_pages.md for detailed instructions"
        ;;
    *)
        echo "Invalid option. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment instructions completed!"
echo ""
echo "Next steps:"
echo "1. Follow the deployment instructions above"
echo "2. Test your deployed application"
echo "3. Share the URL with others!"
echo ""
echo "For help, check the documentation in deploy_github_pages.md"