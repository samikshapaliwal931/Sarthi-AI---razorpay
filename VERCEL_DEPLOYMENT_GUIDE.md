# 🚀 Vercel Deployment Guide for Sarthi Frontend

This project is fully configured for seamless deployment on **Vercel** using **TanStack Start**, **Vite**, and the **Nitro Vercel preset**.

---

## 📋 Pre-Deployment Summary

1. **Preset Configured**: `vite.config.ts` is explicitly configured with `nitro: { preset: process.env["NITRO_PRESET"] || "vercel" }`.
2. **Build Output**: Building produces the standard `.vercel/output` (Vercel Build Output API v3) that Vercel recognizes automatically.
3. **Mock Mode & Production API Ready**: The frontend can operate standalone in demo/mock mode or connect to your deployed FastAPI backend.

---

## 🛠️ Step-by-Step Vercel Deployment

### Step 1: Push Changes to GitHub
Since you mentioned you will push to GitHub yourself, run:
```bash
git add .
git commit -m "Configure Vercel deployment with Nitro Vercel preset and build optimizations"
git push origin main
```

---

### Step 2: Import Project on Vercel Dashboard

1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **"Add New..."** ➔ **"Project"**.
3. Select your GitHub repository and click **"Import"**.

---

### Step 3: Configure Project Settings on Vercel

In the project configuration screen on Vercel:

| Setting | Value | Notes |
| :--- | :--- | :--- |
| **Project Name** | `sarthi-frontend` (or any name) | |
| **Framework Preset** | **Other** (or Vite) | Nitro automatically handles the build output |
| **Root Directory** | `Frontend` | ⚠️ **Crucial**: Click **Edit** and set to `Frontend` |
| **Build Command** | `npm run build` | Default is fine |
| **Output Directory** | *(Leave blank / default)* | Nitro automatically emits `.vercel/output` |
| **Install Command** | `npm install` | Default is fine |

---

### Step 4: Configure Environment Variables

Under **Environment Variables** on Vercel, add the following:

#### Option A: Standalone Demo Mode (No backend needed yet)
```env
VITE_USE_MOCK=true
```

#### Option B: Connected to Deployed Backend (Production)
```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=https://your-backend-api.onrender.com/api/v1
```
*(Replace `https://your-backend-api.onrender.com/api/v1` with your actual FastAPI backend URL)*

---

### Step 5: Deploy!
Click **"Deploy"**. Vercel will install dependencies, run `npm run build`, detect the `.vercel/output` folder, and deploy your site with global edge SSR and static assets.

---

## 🔍 Verification Checklist

- [x] `npx tsc --noEmit` passes with **0 errors**.
- [x] `npm run build` generates `.vercel/output/` without errors.
- [x] ESLint and Prettier configs ignore build output and large files.
- [x] `.gitignore` ignores `.vercel/` and `.output/`.
- [x] `Frontend/.env.example` is provided for reference.
