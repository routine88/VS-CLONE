# Git Setup Guide

Follow these steps to ensure the project is ready for pushing and pulling via Git on your machine.

## 1. Install Git
- [Download Git](https://git-scm.com/downloads) if it is not already installed.
- Configure your name and email so commits are attributed correctly:
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "you@example.com"
  ```

## 2. Clone the Repository
If you have access to the hosted repository, clone it directly:
```bash
git clone https://github.com/routine88/VS-CLONE.git
cd VS-CLONE
```
This will automatically configure the `origin` remote so you can pull new changes and push updates.

## 3. Initialize from Local Files (Optional)
If you received the project as a zip or folder without Git metadata, initialize it manually:
```bash
git init -b main
git remote add origin <your-remote-url>
git add .
git commit -m "Initial commit"
```
Replace `<your-remote-url>` with the actual repository location (e.g., `git@github.com:yourname/vs-clone.git`).

## 4. Push and Pull
Once your repository is configured, you can synchronize changes with the remote:
```bash
# Fetch and merge remote updates
git pull origin main

# Push your local commits to the remote
git push origin main
```
If this is your first push, you may need to set the upstream branch:
```bash
git push -u origin main
```

## 5. Verify Remote Configuration
Double-check that `origin` points to the correct remote URL:
```bash
git remote -v
```
This should list both fetch and push URLs for your repository.

With these steps completed, the project will be fully set up for command-line Git workflows.
