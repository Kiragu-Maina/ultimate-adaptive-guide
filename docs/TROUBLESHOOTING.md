# Troubleshooting Guide

Common issues and solutions for AlkenaCode Adaptive Learning Platform.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Database Issues](#database-issues)
- [Redis/Caching Issues](#rediscaching-issues)
- [Backend API Issues](#backend-api-issues)
- [Frontend Issues](#frontend-issues)
- [LLM/AI Agent Issues](#llmai-agent-issues)
- [Performance Issues](#performance-issues)
- [Docker Issues](#docker-issues)
- [Network Issues](#network-issues)
- [Production Issues](#production-issues)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

### Health Check Command

```bash
# Run this first to check system health
cd multiagential

# Check all services
docker compose ps

# Check backend health
curl http://localhost:4465/

# Check frontend
curl http://localhost:4464/

# Check logs for errors
docker compose logs --tail=50 backend | grep -i error
docker compose logs --tail=50 frontend | grep -i error
```

### Expected Healthy Output

```bash
# docker compose ps
NAME                      STATUS         PORTS
multiagential-backend-1   Up (healthy)   0.0.0.0:8007->8000/tcp
multiagential-frontend-1  Up             0.0.0.0:3007->3000/tcp
multiagential-postgres-1  Up (healthy)   5432/tcp
multiagential-redis-1     Up (healthy)   6379/tcp

# curl http://localhost:4465/
{"status":"ok","adaptive_agents":"online","redis":"healthy",...}
```

---

## Installation Issues

### Issue: Docker Compose Command Not Found

**Symptom**:
```
bash: docker compose: command not found
```

**Cause**: Old Docker version or Docker Compose not installed

**Solution**:

```bash
# Check Docker version
docker --version
# Should be 20.10+ for docker compose v2

# If using old docker-compose (with hyphen)
docker-compose --version

# Update Docker Desktop (Mac/Windows)
# Download latest from: https://www.docker.com/products/docker-desktop

# Linux: Install Docker Compose plugin
sudo apt update
sudo apt install docker-compose-plugin

# Or use docker-compose (legacy)
pip install docker-compose
```

---

### Issue: Permission Denied When Running Docker

**Symptom**:
```
Got permission denied while trying to connect to the Docker daemon socket
```

**Cause**: User not in docker group

**Solution**:

```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker

# Verify
docker ps
```

---

### Issue: Port Already in Use

**Symptom**:
```
Error: bind: address already in use
```

**Cause**: Port 8007 or 3007 already occupied

**Solution**:

```bash
# Find process using port
sudo lsof -i :8007
sudo lsof -i :3007

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
services:
  backend:
    ports:
      - "8008:8000"  # Change from 8007 to 8008
```

---

## Database Issues

### Issue: Database Connection Refused

**Symptom**:
```
sqlalchemy.exc.OperationalError: could not connect to server: Connection refused
```

**Cause**: PostgreSQL not running or not ready

**Solution**:

```bash
# Check if PostgreSQL is healthy
docker compose ps postgres
# Should show: Up (healthy)

# If not healthy, check logs
docker compose logs postgres

# Wait for health check (up to 30 seconds)
# Or restart
docker compose restart postgres

# Verify connection manually
docker compose exec postgres psql -U adaptive_user -d adaptive_learning -c "\dt"
```

---

### Issue: Database Not Initialized

**Symptom**:
```
relation "users" does not exist
```

**Cause**: Database tables not created

**Solution**:

```bash
# Initialize database
docker compose exec backend python init_db.py

# Verify tables exist
docker compose exec postgres psql -U adaptive_user -d adaptive_learning -c "\dt"

# Should see: users, user_profiles, topic_mastery, etc.
```

---

### Issue: Database Schema Mismatch

**Symptom**:
```
column "description" does not exist in table "learning_journeys"
```

**Cause**: Database schema outdated after code update

**Solution**:

```bash
# Option 1: Drop and recreate (DEVELOPMENT ONLY - LOSES DATA)
docker compose down -v
docker compose up -d
docker compose exec backend python init_db.py

# Option 2: Run migration (PRODUCTION - SAFE)
docker compose exec backend python migrate_add_journey_fields.py

# Option 3: Manual SQL
docker compose exec postgres psql -U adaptive_user -d adaptive_learning
ALTER TABLE learning_journeys ADD COLUMN description TEXT;
ALTER TABLE learning_journeys ADD COLUMN estimated_hours INTEGER;
ALTER TABLE learning_journeys ADD COLUMN prerequisites JSON;
\q
```

---

### Issue: Database Locked

**Symptom**:
```
database is locked
```

**Cause**: Using SQLite (development fallback) with concurrent access

**Solution**:

```bash
# Switch to PostgreSQL (recommended)
# Ensure DATABASE_URL is set correctly
echo $DATABASE_URL
# Should be: postgresql://...

# If using SQLite, restart backend
docker compose restart backend
```

---

## Redis/Caching Issues

### Issue: Redis Connection Error

**Symptom**:
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Cause**: Redis not running or connection string incorrect

**Solution**:

```bash
# Check if Redis is healthy
docker compose ps redis
# Should show: Up (healthy)

# Test connection
docker compose exec redis redis-cli ping
# Should return: PONG

# Check logs
docker compose logs redis

# Restart Redis
docker compose restart redis

# Verify REDIS_URL in backend/.env
cat backend/.env | grep REDIS_URL
# Should be: redis://redis:6379
```

---

### Issue: Cache Not Working (Low Hit Rate)

**Symptom**: Slow performance, high database load

**Cause**: Redis not caching or cache keys incorrect

**Solution**:

```bash
# Check Redis keys
docker compose exec redis redis-cli KEYS "*"

# Check cache stats
docker compose exec redis redis-cli INFO stats

# Look for:
# - keyspace_hits (should be high)
# - keyspace_misses (should be low)

# Clear cache and rebuild
docker compose exec redis redis-cli FLUSHALL

# Restart backend to reinitialize cache
docker compose restart backend

# Monitor cache operations in backend logs
docker compose logs -f backend | grep -i cache
```

---

## Backend API Issues

### Issue: 500 Internal Server Error

**Symptom**: API returns 500 status code

**Cause**: Various - check logs

**Solution**:

```bash
# Check backend logs
docker compose logs backend --tail=100

# Look for stack traces
docker compose logs backend | grep -A 20 "Traceback"

# Common causes:
# 1. Missing environment variable
docker compose exec backend env | grep OPENROUTER_API_KEY

# 2. Database connection error
docker compose exec backend python -c "from db_postgres import get_db; list(get_db())"

# 3. LLM API error
# Check OpenRouter API status: https://openrouter.ai/status

# Restart backend
docker compose restart backend
```

---

### Issue: OpenRouter API Key Error

**Symptom**:
```
401 Unauthorized: Invalid API key
```

**Cause**: API key missing or incorrect

**Solution**:

```bash
# Check if API key is set
docker compose exec backend printenv OPENROUTER_API_KEY

# If empty, update backend/.env
nano multiagential/backend/.env
# Add: OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Restart backend
docker compose restart backend

# Test API key directly
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer sk-or-v1-your-key-here"
```

---

### Issue: User Not Found

**Symptom**:
```
{"error": "User has no learning journey. Complete onboarding first."}
```

**Cause**: User hasn't completed onboarding or session lost

**Solution**:

```bash
# Check user exists in database
docker compose exec postgres psql -U adaptive_user -d adaptive_learning \
  -c "SELECT id FROM users LIMIT 10;"

# Check user has profile
docker compose exec postgres psql -U adaptive_user -d adaptive_learning \
  -c "SELECT user_id FROM user_profiles LIMIT 10;"

# Frontend: Clear cookies and retry onboarding
# Browser DevTools → Application → Cookies → Delete alkenacode_*

# Backend: Create test user
docker compose exec backend python -c "
from db_postgres import create_user
create_user('test_user_123')
print('User created')
"
```

---

## Frontend Issues

### Issue: Frontend Won't Start

**Symptom**:
```
Error: Cannot find module 'next'
```

**Cause**: Dependencies not installed

**Solution**:

```bash
# Rebuild frontend
cd multiagential/frontend
npm install
npm run build

# Or rebuild Docker image
cd multiagential
docker compose up --build frontend
```

---

### Issue: API Connection Error (CORS)

**Symptom**:
```
Access to fetch at 'http://localhost:4465' from origin 'http://localhost:4464'
has been blocked by CORS policy
```

**Cause**: CORS headers not configured

**Solution**:

```python
# Add to main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4464"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

```bash
# Restart backend
docker compose restart backend
```

---

### Issue: Session Not Persisting

**Symptom**: User progress lost on page reload

**Cause**: Cookies not being set or cleared

**Solution**:

```javascript
// Check if cookies are set (Browser DevTools → Application → Cookies)
// Should see: alkenacode_user_id, alkenacode_onboarding_complete

// If missing, check SessionManager (src/lib/session.ts)
import { SessionManager } from '@/lib/session';
const userId = SessionManager.getUserId();
console.log('User ID:', userId);

// Clear cookies and retry
document.cookie.split(";").forEach(c => {
  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
});

// Restart onboarding
window.location.href = '/adaptive';
```

---

### Issue: Markdown Not Rendering

**Symptom**: Content shows as plain text

**Cause**: MarkdownRenderer component issue

**Solution**:

```bash
# Check MarkdownRenderer component exists
ls multiagential/frontend/src/components/MarkdownRenderer.tsx

# Verify import in content page
grep -r "MarkdownRenderer" multiagential/frontend/src/app/

# Check react-markdown is installed
cd multiagential/frontend
npm list react-markdown remark-gfm remark-math rehype-katex

# Reinstall if missing
npm install react-markdown remark-gfm remark-math rehype-katex
```

---

## LLM/AI Agent Issues

### Issue: Quiz Generation Returns 0 Questions

**Symptom**:
```
{"quiz_id": "...", "questions": []}
```

**Cause**: LLM returning empty or malformed response

**Solution**:

```bash
# Check backend logs for LLM errors
docker compose logs backend | grep -i "llm\|openrouter\|quiz"

# Verify multi-model fallback is working
# Should see attempts with different models:
# - openai/gpt-oss-120b
# - nousresearch/deephermes-3-mistral-24b-preview
# - google/gemini-2.5-flash-lite

# Check OpenRouter API status
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Try different model
nano multiagential/backend/.env
# Change: DEFAULT_MODEL=google/gemini-2.5-flash-lite

docker compose restart backend
```

---

### Issue: Onboarding Takes Too Long

**Symptom**: Onboarding hangs for 5+ minutes

**Cause**: LLM API slow or timing out

**Solution**:

```bash
# Check logs for timeouts
docker compose logs backend | grep -i "timeout\|llm"

# Monitor in real-time
docker compose logs -f backend

# Causes:
# 1. OpenRouter API slow - check status page
# 2. DuckDuckGo API rate limited - wait 60 seconds
# 3. Network issues - check internet connection

# Restart and retry
docker compose restart backend

# If persistent, use faster model
# Edit backend/.env: DEFAULT_MODEL=google/gemini-2.5-flash-lite
```

---

### Issue: Agent Decisions Not Logged

**Symptom**: `/adaptive/agent-decisions` returns empty array

**Cause**: Decision logging disabled or database issue

**Solution**:

```bash
# Check agent_decisions table exists
docker compose exec postgres psql -U adaptive_user -d adaptive_learning \
  -c "SELECT COUNT(*) FROM agent_decisions;"

# If table missing, reinitialize
docker compose exec backend python init_db.py

# Check if logging is enabled in code
docker compose exec backend grep -r "log_agent_decision" .

# Test manual logging
docker compose exec backend python -c "
from db_postgres import log_agent_decision
log_agent_decision(
    user_id='test_user',
    agent_name='test_agent',
    decision_type='test',
    input_data={},
    output_data={},
    reasoning='Test decision'
)
print('Logged')
"

# Query to verify
docker compose exec postgres psql -U adaptive_user -d adaptive_learning \
  -c "SELECT agent_name, decision_type FROM agent_decisions LIMIT 5;"
```

---

## Performance Issues

### Issue: Slow API Responses

**Symptom**: Requests take 10+ seconds

**Cause**: Various - profiling needed

**Solution**:

```bash
# 1. Check cache hit rate
curl http://localhost:4465/health/cache

# Should show hit_rate > 0.70

# 2. Check database query performance
docker compose exec postgres psql -U adaptive_user -d adaptive_learning
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
\q

# 3. Monitor resource usage
docker stats

# Look for:
# - High CPU: May need more workers
# - High memory: May need caching
# - High I/O: Database optimization needed

# 4. Enable query logging
docker compose exec backend python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
"

# 5. Add indexes to frequently queried columns
docker compose exec postgres psql -U adaptive_user -d adaptive_learning
CREATE INDEX IF NOT EXISTS idx_user_mastery ON topic_mastery(user_id, topic);
CREATE INDEX IF NOT EXISTS idx_quiz_history_user_date ON quiz_history(user_id, completed_at DESC);
\q
```

---

### Issue: High Memory Usage

**Symptom**: Docker containers using excessive RAM

**Cause**: Memory leaks or inefficient caching

**Solution**:

```bash
# Check memory usage
docker stats --no-stream

# If backend > 2GB:
# 1. Restart to clear memory
docker compose restart backend

# 2. Adjust Redis max memory
docker compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 3. Reduce cache TTLs in backend/.env
# CACHE_TTL_PROFILE=1800  # Down from 3600
# CACHE_TTL_JOURNEY=900   # Down from 1800

# 4. Limit number of workers
# In Dockerfile: CMD ["uvicorn", "main:app", "--workers", "2"]  # Down from 4
```

---

### Issue: Database Slow Queries

**Symptom**: Queries taking seconds to execute

**Solution**:

```bash
# Enable slow query logging
docker compose exec postgres psql -U adaptive_user -d adaptive_learning
ALTER SYSTEM SET log_min_duration_statement = 1000;  # Log queries > 1 second
SELECT pg_reload_conf();
\q

# Check logs for slow queries
docker compose logs postgres | grep "duration:"

# Add missing indexes
docker compose exec postgres psql -U adaptive_user -d adaptive_learning
\d+ topic_mastery  # Show indexes

# Create indexes if missing
CREATE INDEX idx_user_position ON learning_journeys(user_id, position);
CREATE INDEX idx_user_topic ON topic_mastery(user_id, topic);
\q

# Analyze tables
docker compose exec postgres psql -U adaptive_user -d adaptive_learning
ANALYZE topic_mastery;
ANALYZE learning_journeys;
ANALYZE quiz_history;
\q
```

---

## Docker Issues

### Issue: Docker Compose Version Conflict

**Symptom**:
```
ERROR: The Compose file is invalid
```

**Cause**: Using old docker-compose.yml format

**Solution**:

```bash
# Check version in docker-compose.yml
head -n 1 multiagential/docker-compose.yml
# Should be: version: '3.8'

# Use docker compose (v2, no hyphen)
docker compose version

# Or use docker-compose (v1, with hyphen)
docker-compose version

# Update to match your version
```

---

### Issue: Build Cache Issues

**Symptom**: Changes not reflected after rebuild

**Solution**:

```bash
# Force rebuild without cache
docker compose build --no-cache

# Or remove all images and rebuild
docker compose down
docker system prune -a
docker compose up --build
```

---

### Issue: Volume Permission Errors

**Symptom**:
```
permission denied: /var/lib/postgresql/data
```

**Solution**:

```bash
# Fix volume permissions
docker compose down
docker volume rm multiagential_postgres_data
docker volume rm multiagential_redis_data
docker compose up -d

# Or manually fix
docker run --rm -v multiagential_postgres_data:/data alpine \
  sh -c "chown -R 999:999 /data"
```

---

## Network Issues

### Issue: Cannot Access Frontend from Other Devices

**Symptom**: Works on localhost but not from phone/tablet

**Solution**:

```bash
# Check firewall
sudo ufw allow 3007
sudo ufw allow 8007

# Bind to 0.0.0.0 instead of localhost
# In docker-compose.yml:
services:
  frontend:
    ports:
      - "0.0.0.0:3007:3000"

# Find your local IP
ip addr show | grep "inet "

# Access from other device
http://192.168.x.x:3007
```

---

### Issue: DuckDuckGo API Rate Limited

**Symptom**: Journey Architect fails with timeout

**Solution**:

```bash
# Wait 60 seconds between requests
# DuckDuckGo Instant Answer API has rate limits

# Add retry delay in journey_architect_agent.py
import time
time.sleep(2)  # 2 second delay between API calls

# Or use fallback journey generation
# Already implemented in code - check logs for:
# "⚠️  Warning: Using fallback journey generation"
```

---

## Production Issues

### Issue: SSL Certificate Errors

**Symptom**:
```
ERR_CERT_AUTHORITY_INVALID
```

**Solution**:

```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Check certificate expiry
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Restart nginx to load new certificate
docker compose restart nginx
```

---

### Issue: High Load / Out of Memory

**Symptom**: Service crashes under load

**Solution**:

```bash
# Scale up backend replicas
docker compose up -d --scale backend=5

# Increase container memory limits
# In docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G

# Add swap space (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

### Issue: Database Connection Pool Exhausted

**Symptom**:
```
QueuePool limit of size X overflow Y reached
```

**Solution**:

```bash
# Increase pool size in backend/.env
DB_POOL_SIZE=50  # Up from 20

# Or in db_postgres.py:
engine = create_engine(
    DATABASE_URL,
    pool_size=50,
    max_overflow=100
)

# Restart backend
docker compose restart backend

# Monitor connections
docker compose exec postgres psql -U adaptive_user -d adaptive_learning \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Getting Help

### Debug Information to Collect

When asking for help, provide:

```bash
# 1. System information
uname -a
docker --version
docker compose version

# 2. Service status
docker compose ps

# 3. Recent logs
docker compose logs --tail=100 backend > backend.log
docker compose logs --tail=100 frontend > frontend.log
docker compose logs --tail=100 postgres > postgres.log

# 4. Environment (sanitized)
docker compose exec backend env | grep -v "API_KEY\|PASSWORD"

# 5. Database state
docker compose exec postgres psql -U adaptive_user -d adaptive_learning -c "\dt"

# 6. Error message (exact copy)
# Include full stack trace
```

### Self-Service Resources

1. **Documentation**: Check `/docs` folder
   - [Getting Started](GETTING_STARTED.md)
   - [API Reference](API_REFERENCE.md)
   - [Deployment Guide](DEPLOYMENT.md)

2. **Logs Analysis**: Enable debug logging
   ```python
   # In main.py
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Interactive Debugging**:
   ```bash
   # Enter backend container
   docker compose exec backend bash

   # Test database
   python -c "from db_postgres import get_db; list(get_db())"

   # Test Redis
   python -c "from cache_redis import CacheManager; print(CacheManager().redis.ping())"

   # Test LLM
   python -c "from quiz_generator_agent import generate_quiz; print(generate_quiz('Python', 'easy', 2))"
   ```

### Community Support

- **GitHub Issues**: https://github.com/yourusername/alkenacode-adaptive-learning/issues
- **Discussions**: GitHub Discussions tab
- **Documentation**: https://docs.alkenacode.com (if published)

### Commercial Support

For production deployments or custom implementations, contact:
- Email: support@alkenacode.com (if applicable)
- Enterprise support packages available

---

## Common Error Messages Reference

| Error Message | Location | Solution Reference |
|---------------|----------|-------------------|
| `Connection refused` | Database | [Database Connection Refused](#issue-database-connection-refused) |
| `Invalid API key` | Backend | [OpenRouter API Key Error](#issue-openrouter-api-key-error) |
| `Port already in use` | Docker | [Port Already in Use](#issue-port-already-in-use) |
| `Permission denied` | Docker | [Volume Permission Errors](#issue-volume-permission-errors) |
| `500 Internal Server Error` | Backend | [500 Internal Server Error](#issue-500-internal-server-error) |
| `CORS policy` | Frontend | [API Connection Error (CORS)](#issue-api-connection-error-cors) |
| `relation does not exist` | Database | [Database Not Initialized](#issue-database-not-initialized) |
| `command not found` | System | [Docker Compose Command Not Found](#issue-docker-compose-command-not-found) |

---

**Last Updated**: October 19, 2025

**Need more help?** Check the [Getting Started Guide](GETTING_STARTED.md) or open an issue on GitHub.
