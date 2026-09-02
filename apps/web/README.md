# PRAVAH — Next.js 16 Web Application

Modern Next.js 16 (App Router + Turbopack) & React 19 Frontend for PRAVAH.

## 🚀 Quick Start (Standalone Repo)

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env.local
```

### 3. Run Development Server
```bash
npm run dev
```

Open http://localhost:3000 in your browser.

### 4. Build for Production
```bash
npm run build
npm start
```

### 5. Typecheck
```bash
npm run typecheck
```

## 🐳 Docker Deployment
```bash
docker build -t pravah-web .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 pravah-web
```
