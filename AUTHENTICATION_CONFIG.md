# Authentication Configuration - JJF Survey Analytics

The application now includes a simple password-based authentication system to secure access to the dashboard and sensitive data.

## 🔐 Authentication Features

### Static Password Protection
- Single password protects all application routes
- Session-based authentication with secure cookies
- Automatic logout functionality
- Login/logout logging for security monitoring

### Configurable Security
- Enable/disable authentication via environment variable
- Customizable password via environment variable
- Session management with Flask sessions
- Health check endpoints remain accessible (for Railway monitoring)

## ⚙️ Configuration

### Environment Variables

Set these variables to configure authentication:

#### Required Variables
```bash
# Enable/disable authentication
REQUIRE_AUTH=true          # Set to 'false' to disable authentication

# Application password
APP_PASSWORD=your-secure-password-here

# Port configuration
PORT=5001                  # Default port, Railway will override this

# Session security
SECRET_KEY=your-secret-key-for-sessions
```

#### Default Values
```bash
REQUIRE_AUTH=true          # Authentication enabled by default
APP_PASSWORD=survey2025!   # Default password (CHANGE IN PRODUCTION!)
PORT=5001                  # Default port
SECRET_KEY=surveyor-data-viewer-2025-default-key  # Default secret key
```

### Railway Configuration

#### Method 1: Railway Dashboard
1. Go to your Railway project
2. Navigate to **Variables** tab
3. Add these variables:

```
REQUIRE_AUTH=true
APP_PASSWORD=your-secure-password
SECRET_KEY=your-long-random-secret-key
PORT=5001
```

#### Method 2: Railway CLI
```bash
railway variables set REQUIRE_AUTH=true
railway variables set APP_PASSWORD=your-secure-password
railway variables set SECRET_KEY=your-long-random-secret-key
railway variables set PORT=5001
```

#### Method 3: Automated Deployment
```bash
./deploy-railway.sh
# This sets default values - change APP_PASSWORD in Railway dashboard
```

## 🔑 Password Management

### Default Password
- **Default**: `survey2025!`
- **⚠️ IMPORTANT**: Change this in production!

### Setting Custom Password

#### For Railway Deployment:
```bash
railway variables set APP_PASSWORD=your-secure-password
```

#### For Local Development:
```bash
export APP_PASSWORD=your-secure-password
```

#### In .env file:
```bash
REQUIRE_AUTH=true
APP_PASSWORD=your-secure-password
SECRET_KEY=your-long-random-secret-key
```

### Password Security Best Practices
1. **Use a strong password** (12+ characters, mixed case, numbers, symbols)
2. **Don't use the default password** in production
3. **Change passwords regularly**
4. **Don't commit passwords** to version control
5. **Use environment variables** for all sensitive data

## 🚪 Authentication Flow

### Login Process
1. User visits any protected route
2. Redirected to `/login` if not authenticated
3. Enter password and submit form
4. On success: redirect to original destination
5. On failure: show error message and retry

### Session Management
- Sessions last until browser closes or explicit logout
- Session data stored securely with Flask sessions
- Automatic cleanup on logout

### Protected Routes
All main application routes require authentication:
- `/` - Dashboard
- `/spreadsheets` - Spreadsheet listing
- `/spreadsheet/<id>` - Individual spreadsheet view
- `/jobs` - Extraction jobs
- `/surveys` - Survey analytics
- `/sync` - Auto-sync dashboard
- `/health/dashboard` - Health monitoring dashboard

### Public Routes
These routes remain accessible without authentication:
- `/login` - Login page
- `/health` - Health check (for Railway monitoring)
- `/health/status` - Quick health status
- `/health/test` - System test endpoint
- `/health/metrics` - Prometheus metrics

## 🔧 Disabling Authentication

### For Development
```bash
export REQUIRE_AUTH=false
```

### For Railway
```bash
railway variables set REQUIRE_AUTH=false
```

### In Code
The authentication can be completely disabled by setting `REQUIRE_AUTH=false`. When disabled:
- All routes become publicly accessible
- Login/logout routes still exist but redirect to dashboard
- No session management overhead

## 🛡️ Security Features

### Session Security
- Secure session cookies
- Session data encrypted with SECRET_KEY
- Automatic session cleanup on logout
- Session timeout on browser close

### Login Monitoring
- Successful logins logged with IP address
- Failed login attempts logged with IP address
- All authentication events include timestamps

### CSRF Protection
- Forms include CSRF tokens (via Flask sessions)
- POST requests validated against session

## 📊 Monitoring Authentication

### Log Messages
Monitor these authentication events in Railway logs:

```bash
# Successful logins
railway logs --filter "Successful login"

# Failed login attempts
railway logs --filter "Failed login attempt"

# Logout events
railway logs --filter "User logged out"
```

### Health Check Integration
Authentication status is included in health checks:
- `/health/test` shows authentication configuration
- Login failures don't affect health check status
- Authentication is logged during health checks

## 🚀 Deployment Examples

### Production Deployment
```bash
# Set secure password
railway variables set APP_PASSWORD="MySecurePassword123!"

# Set secure secret key
railway variables set SECRET_KEY="your-very-long-random-secret-key-here"

# Enable authentication
railway variables set REQUIRE_AUTH=true

# Deploy
railway up
```

### Development Deployment
```bash
# Disable authentication for development
railway variables set REQUIRE_AUTH=false

# Deploy
railway up
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Can't Access Application
**Problem**: Redirected to login but password doesn't work
**Solutions**:
- Check `APP_PASSWORD` environment variable in Railway
- Verify password doesn't have extra spaces
- Check Railway logs for failed login attempts

#### 2. Session Issues
**Problem**: Logged out immediately after login
**Solutions**:
- Check `SECRET_KEY` is set and consistent
- Verify cookies are enabled in browser
- Check for clock synchronization issues

#### 3. Health Checks Failing
**Problem**: Railway health checks fail after adding authentication
**Solutions**:
- Health check endpoints (`/health`, `/health/status`) are public
- Check Railway logs for specific health check errors
- Verify authentication doesn't affect health endpoints

### Debug Commands

```bash
# Check authentication configuration
curl https://your-app.railway.app/health/test

# Test login endpoint
curl -X POST https://your-app.railway.app/login \
  -d "password=your-password" \
  -c cookies.txt

# Test protected endpoint with session
curl -b cookies.txt https://your-app.railway.app/

# Check Railway variables
railway variables
```

## 📋 Security Checklist

### Pre-Production
- [ ] Change default password (`APP_PASSWORD`)
- [ ] Set secure secret key (`SECRET_KEY`)
- [ ] Enable authentication (`REQUIRE_AUTH=true`)
- [ ] Test login/logout functionality
- [ ] Verify health checks still work
- [ ] Check Railway logs for authentication events

### Post-Production
- [ ] Monitor failed login attempts
- [ ] Regularly rotate passwords
- [ ] Review authentication logs
- [ ] Test disaster recovery procedures
- [ ] Document password recovery process

## 🔗 Integration with Health Checks

The authentication system is fully integrated with the health check system:

- **Health endpoints remain public** for Railway monitoring
- **Authentication status included** in health test endpoint
- **Login failures logged** but don't affect health status
- **Session management monitored** in health checks

Your application is now secured with password authentication while maintaining full Railway compatibility and health monitoring capabilities!
