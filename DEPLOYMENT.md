# Deployment Guide

## Option 1: Render (Recommended - Free)

1. Create a GitHub account if you don't have one
2. Create a new repository and push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

3. Go to https://render.com and sign up
4. Click "New +" → "Web Service"
5. Connect your GitHub repository
6. Configure:
   - Name: ai-lost-found
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
7. Click "Create Web Service"
8. Wait 5-10 minutes for deployment
9. Your app will be live at: `https://ai-lost-found.onrender.com`

## Option 2: PythonAnywhere (Free)

1. Sign up at https://www.pythonanywhere.com
2. Go to "Files" and upload your project files
3. Go to "Web" tab → "Add a new web app"
4. Choose Flask and Python 3.10
5. Set working directory to your project folder
6. Edit WSGI configuration file:
   ```python
   import sys
   path = '/home/YOUR_USERNAME/AI_Lost_Found_Project'
   if path not in sys.path:
       sys.path.append(path)
   
   from app import app as application
   ```
7. Reload the web app
8. Your app will be at: `https://YOUR_USERNAME.pythonanywhere.com`

## Option 3: Heroku

1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Create a Procfile:
   ```
   web: gunicorn app:app
   ```
3. Login and deploy:
   ```bash
   heroku login
   heroku create ai-lost-found
   git push heroku main
   heroku open
   ```

## Option 4: Vercel (Serverless)

1. Install Vercel CLI: `npm i -g vercel`
2. Create `vercel.json`:
   ```json
   {
     "builds": [{"src": "app.py", "use": "@vercel/python"}],
     "routes": [{"src": "/(.*)", "dest": "app.py"}]
   }
   ```
3. Deploy:
   ```bash
   vercel
   ```

## Important Notes

- The free tier of most platforms has limitations
- Database will reset on Render free tier after inactivity
- For production, consider using PostgreSQL instead of SQLite
- Update the secret_key in app.py before deploying
- Images are stored in database as base64 (works on all platforms)

## Custom Domain

After deployment, you can add a custom domain:
- Render: Settings → Custom Domains
- PythonAnywhere: Web tab → Add custom domain (paid feature)
- Heroku: Settings → Domains
