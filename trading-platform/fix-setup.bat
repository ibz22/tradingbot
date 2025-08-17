@echo off
echo 🔧 Fixing Solsak Trading Platform Setup...

echo 📁 Cleaning up old node_modules...
cd frontend
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json

echo 📦 Installing updated packages...
npm cache clean --force
npm install --legacy-peer-deps

echo ✅ Setup fixed! You can now run:
echo    npm run dev

pause