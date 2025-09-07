# Scripts Directory

This directory contains consolidated scripts for managing the Personal Finance Tracker project.

## Script Organization

### 🛠️ Main Interface
- **`make.sh`** - Main command interface that dispatches to other scripts
  - Provides simple, Make-style commands
  - Use this for quick access to common tasks

### 📦 Core Scripts

#### `build.sh` - Build Management
- Build specific services or all services
- Selective building for faster development
- Docker image management

#### `deploy.sh` - Deployment Management  
- **setup** - Initial project setup (first time)
- **quick** - Quick deployment after code changes
- **full** - Full deployment (rebuild everything)
- **start/restart** - Service management
- **health** - Application health checks

#### `dev.sh` - Development Tools
- **watch** - File watching for auto-rebuild
- **reset** - Reset entire application (destroys data)
- **lint/format** - Code quality tools
- **backup-db/restore-db** - Database operations
- **test-imports** - CSV import testing
- **benchmark** - Performance testing

#### `manage.sh` - System Management
- **logs** - View service logs
- **stop** - Stop services  
- **backup** - Create backups (db, files, full)
- **monitor** - Real-time system monitoring
- **clean** - Docker cleanup
- **export/import** - Data management

#### `data.sh` - Data Management
- Generate sample data for testing
- Data import/export utilities

## Quick Start

```bash
# First time setup
./scripts/make.sh setup

# Development workflow
./scripts/make.sh watch      # Start development mode
./scripts/make.sh deploy     # Quick deployment
./scripts/make.sh logs api   # View API logs

# Direct script usage (for more options)
./scripts/dev.sh --help
./scripts/deploy.sh --help
./scripts/manage.sh --help
```

## Migration from Old Scripts

The following old scripts have been consolidated:

| Old Script | New Location |
|------------|-------------|
| `dev_utils.sh` | `dev.sh` |
| `dev_watch.sh` | `dev.sh watch` |
| `reset.sh` | `dev.sh reset` |
| `setup.sh` | `deploy.sh setup` |
| `quick_deploy.sh` | `deploy.sh quick` |
| `logs.sh` | `manage.sh logs` |
| `stop.sh` | `manage.sh stop` |
| `backup.sh` | `manage.sh backup` |
| `generate_sample_data.sh` | `data.sh` |

## Command Examples

```bash
# Build commands
./scripts/make.sh build api          # Build only API
./scripts/make.sh build              # Build all services

# Deployment
./scripts/make.sh setup              # Initial setup
./scripts/make.sh deploy             # Quick deploy
./scripts/make.sh restart api        # Restart API service

# Development
./scripts/make.sh watch              # Watch all services
./scripts/make.sh watch api          # Watch only API
./scripts/make.sh reset              # Reset everything

# Management
./scripts/make.sh logs               # All logs
./scripts/make.sh logs dashboard     # Dashboard logs only
./scripts/make.sh backup db          # Database backup
./scripts/make.sh monitor            # Real-time monitoring

# Data
./scripts/make.sh data               # Generate sample data
```

## Benefits of Consolidation

✅ **Reduced clutter** - From 11 scripts to 6 focused scripts  
✅ **Better organization** - Related functionality grouped together  
✅ **Consistent interface** - All scripts follow same pattern  
✅ **Easy discovery** - `make.sh` provides unified entry point  
✅ **Maintainable** - Less duplication, shared utilities  
✅ **Comprehensive** - Each script has full help documentation
