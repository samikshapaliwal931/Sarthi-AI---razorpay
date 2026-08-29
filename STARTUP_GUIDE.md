# Sarthi AI Revenue Agent - Startup Guide

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed and running
- Node.js 18+ installed
- Python 3.14 installed

### Step 1: Start Database Services

```bash
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Backend

# Start PostgreSQL and Redis
docker compose up -d db redis

# Verify services are running
docker ps | grep backend
```

Expected output:
```
backend-db-1     (PostgreSQL on port 5433)
backend-redis-1  (Redis on port 6380)
```

### Step 2: Start Backend

```bash
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Backend

# Activate Python virtual environment
source .venv/bin/activate

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: **http://localhost:8000**

Verify:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","service":"sarthi"}
```

### Step 3: Start Frontend

Open a **new terminal** and run:

```bash
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:8080**

**Note**: If port 8080 is in use, either:
- Stop the conflicting service: `docker stop <container-name>`
- Or use a different port: `npm run dev -- --port 3000`

### Step 4: Access the Application

1. **Merchant Dashboard**: http://localhost:8080
   - Login: `demo@strideathletics.com`
   - Password: `demo123456`

2. **API Documentation**: http://localhost:8000/docs

3. **Shopper Storefront**: http://localhost:8080/shop

## 🔧 Troubleshooting

### Port Already in Use

If you see "Port 8080 already in use":

```bash
# Find what's using the port
lsof -i :8080

# Stop Docker container if it's the issue
docker stop <container-name>

# Or use a different port for frontend
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Frontend
npm run dev -- --port 3000
```

### Backend Not Starting

If backend fails to start:

```bash
# Check if database is running
docker ps | grep backend

# Restart database if needed
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Backend
docker compose down
docker compose up -d db redis

# Check backend logs
tail -50 backend.log
```

### Database Connection Issues

If you see "Connection refused" errors:

```bash
# Verify PostgreSQL is running
docker ps | grep backend-db

# Check PostgreSQL logs
docker logs backend-db-1

# Restart PostgreSQL
docker restart backend-db-1
```

### Frontend Build Errors

If frontend fails to build:

```bash
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Try building again
npm run dev
```

## 📊 Verify Everything is Working

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@strideathletics.com","password":"demo123456"}'

# Get dashboard
TOKEN="<paste-token-from-login>"
curl http://localhost:8000/api/v1/analytics/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

### Test Frontend

1. Open http://localhost:8080
2. Login with demo credentials
3. Check dashboard shows real data
4. Try AI chat: "I need running shoes under 5000 rupees"

### Test Complete Flow

```bash
# 1. Get products
curl http://localhost:8000/api/v1/storefront/products | head -20

# 2. Create order
PRODUCT_ID="<paste-product-id>"
curl -X POST http://localhost:8000/api/v1/storefront/checkout \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"product_id\":\"$PRODUCT_ID\",\"quantity\":2}]}"

# 3. Confirm payment (test mode)
ORDER_ID="<paste-order-id>"
curl -X POST "http://localhost:8000/api/v1/storefront/order/$ORDER_ID/confirm"
```

## 🛑 Stop Services

### Stop Frontend
Press `Ctrl+C` in the frontend terminal

### Stop Backend
Press `Ctrl+C` in the backend terminal

### Stop Database Services

```bash
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Backend
docker compose down
```

### Stop All Docker Containers

```bash
# Stop all Sarthi containers
docker stop backend-db-1 backend-redis-1

# Or stop all Docker containers (be careful!)
docker stop $(docker ps -q)
```

## 📝 Common Commands

### Backend Development

```bash
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Backend
source .venv/bin/activate

# Start with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# View logs
tail -f backend.log

# Run tests
pytest app/tests/ -v

# Seed demo data (if needed)
python -m app.demo.seed
```

### Frontend Development

```bash
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Frontend

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Database Management

```bash
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Backend

# View database logs
docker logs backend-db-1

# Connect to database
docker exec -it backend-db-1 psql -U sarthi -d sarthi

# Reset database (WARNING: deletes all data)
docker compose down -v
docker compose up -d db
python -m app.demo.seed
```

## 🎯 Demo Credentials

- **Merchant Email**: demo@strideathletics.com
- **Password**: demo123456
- **Store**: Stride Athletics

## 📞 Support

If you encounter issues:

1. Check the logs: `tail -50 backend.log` or `tail -50 frontend.log`
2. Verify all services are running: `docker ps`
3. Check port conflicts: `lsof -i :8000` and `lsof -i :8080`
4. Restart services if needed

## 🔄 Complete Restart

If everything is stuck:

```bash
# Stop everything
pkill -f "uvicorn app.main:app"
pkill -f "vite"
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Backend
docker compose down

# Start everything
docker compose up -d db redis
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# In new terminal:
cd /Users/tikeshvinodbarapatre/Projects/Razoroay/Frontend
npm run dev
```

## ✅ Success Checklist

- [ ] Docker Desktop is running
- [ ] PostgreSQL container is running (port 5433)
- [ ] Redis container is running (port 6380)
- [ ] Backend is running (port 8000)
- [ ] Frontend is running (port 8080)
- [ ] Can login at http://localhost:8080
- [ ] Dashboard shows real data
- [ ] AI chat responds to queries
- [ ] Can create orders through checkout

---

**Happy coding! 🚀**
