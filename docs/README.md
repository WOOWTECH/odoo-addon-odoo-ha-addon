# Odoo HA Addon Documentation

Welcome to the Odoo HA Addon documentation. This addon integrates Home Assistant with Odoo, providing a dashboard to display and control IoT devices within the Odoo interface.

## Quick Navigation

| I want to... | Start here |
|--------------|------------|
| **Get started quickly** | [Getting Started Guide](getting-started/quick-start.md) |
| **Understand the architecture** | [Architecture Overview](architecture/overview.md) |
| **Develop new features** | [Development Guide](guides/development.md) |
| **Troubleshoot issues** | [Troubleshooting Guide](guides/troubleshooting.md) |
| **Review implementation details** | [Implementation](implementation/) |

## Documentation Structure

### 📚 Getting Started
**New to the addon?** Start here.
- **[Quick Start](getting-started/quick-start.md)** - Get up and running in 5 minutes
- **[Architecture Overview](getting-started/architecture-overview.md)** - High-level system design

### 🏗️ Architecture
**Deep dive into system design.**
- **[Overview](architecture/overview.md)** - Complete backend/frontend architecture
- **[Security](architecture/security.md)** - Two-tier permission system
- **[Session Instance](architecture/session-instance.md)** - Session-based instance management
- **[Instance Helper](architecture/instance-helper.md)** - HAInstanceHelper refactoring
- **[Instance Switching](architecture/instance-switching.md)** - Multi-instance switching mechanism
- **[WebSocket Subscription](architecture/websocket-subscription.md)** - Real-time data subscription
- **[Bidirectional Sync](architecture/bidirectional-sync.md)** - Area & Entity bidirectional sync mechanism
- **[Internationalization](architecture/i18n.md)** - Multi-language support

### 📖 Guides
**Practical development guides.**
- **[Development Guide](guides/development.md)** - Common patterns and best practices
- **[Device Control](guides/device-control.md)** - Device control flow and patterns
- **[Bus Mechanisms](guides/bus-mechanisms.md)** - useBus() vs bus_service comparison
- **[Custom Views](guides/custom-views.md)** - HAHistory view implementation
- **[i18n Development](guides/i18n-development.md)** - How to write translatable code
- **[Portal Sharing URLs](guides/portal-sharing-urls.md)** - ha_user portal test URLs
- **[Troubleshooting](guides/troubleshooting.md)** - Common issues and solutions

### 📋 Reference
**Technical references and API docs.**
- **[Odoo Model Types](reference/odoo-model-types.md)** - Odoo model type guide
- **[Home Assistant API](reference/home-assistant-api/)** - HA WebSocket and REST API docs

### 🚀 Implementation
**Feature implementation details.**
- **[Multi-Instance](implementation/multi-instance/)** - Multi-instance support implementation
- **[i18n](implementation/i18n/)** - Internationalization implementation
- **[Features](implementation/features/)** - Individual feature implementations

### 📦 Archive
**Historical documentation and old code reviews.**
- **[Code Reviews](archive/code-reviews/)** - Past code review reports
- **[Issues](archive/issues/)** - Resolved issue investigations
- **[Migration](archive/migration/)** - Migration guides and reports

### 📝 Changelog
**Recent changes and updates.**
- **[2025-11 Changelog](changelog/2025-11.md)** - November 2025 changes

## Role-Based Quick Start

### I'm a Backend Developer
1. Read [Architecture Overview](architecture/overview.md)
2. Understand [Session Instance](architecture/session-instance.md)
3. Review [Development Guide](guides/development.md)
4. Check [Security Architecture](architecture/security.md)

### I'm a Frontend Developer
1. Read [Architecture Overview](architecture/overview.md)
2. Understand [Instance Switching](architecture/instance-switching.md)
3. Review [Bus Mechanisms](guides/bus-mechanisms.md)
4. Check [Development Guide](guides/development.md)

### I'm New to the Project
1. Start with [Quick Start](getting-started/quick-start.md)
2. Read [Architecture Overview](getting-started/architecture-overview.md)
3. Review [Multi-Instance Implementation](implementation/multi-instance/overview.md)
4. Explore [Development Guide](guides/development.md)

### I'm Debugging an Issue
1. Check [Troubleshooting Guide](guides/troubleshooting.md)
2. Session issues → [Instance Helper](architecture/instance-helper.md)
3. Bus issues → [Bus Mechanisms](guides/bus-mechanisms.md)
4. WebSocket issues → [WebSocket Subscription](architecture/websocket-subscription.md)

## Key Concepts

### Multi-Instance Support
The addon supports multiple Home Assistant instances with:
- Session-based instance selection
- Permission-based access control
- Real-time instance switching
- Multi-tab synchronization

See: [Session Instance Architecture](architecture/session-instance.md)

### Security Model
Two-tier permission system:
- `group_ha_user` - Basic access to authorized data
- `group_ha_manager` - Full management capabilities

See: [Security Architecture](architecture/security.md)

### Real-Time Communication
Bus notification system for backend-to-frontend communication:
- WebSocket status updates
- Entity state changes
- Instance switching notifications

See: [Bus Mechanisms](guides/bus-mechanisms.md)

## Development Quick Reference

### API Response Format
```javascript
{
  success: bool,
  data: object,
  error: string
}
```

### Instance Selection Priority
```
1. Session → 2. User Preference → 3. First Accessible Instance
```

### Key Patterns
- **Service-First**: Use `useService("ha_data")`, never direct RPC
- **Bus Notifications**: Use `bus_service.subscribe()`, NOT `useBus()`
- **Reactive State**: Use `useState()` + service callbacks
- **Chart Component**: Use `UnifiedChart` for all new charts

## Contributing

When adding new documentation:
1. Place in appropriate directory based on content type
2. Update this README.md with links
3. Update `/CLAUDE.md` if it affects development workflow
4. Keep cross-references updated
5. Use English for technical content

## Need Help?

- **Project Issues**: Check [Troubleshooting Guide](guides/troubleshooting.md)
- **Development Questions**: Review [Development Guide](guides/development.md)
- **Architecture Questions**: See [Architecture Overview](architecture/overview.md)
- **API Questions**: Check [Reference](reference/) section

## Documentation Versions

- **Current Version**: 1.1 (2025-11-26)
- **Last Major Update**: 2025-11-25 (Removed `is_default` field, 3-level fallback)
- **Documentation Reorganization**: 2025-11-26

---

**Note**: This documentation reflects the current state of the `feature/refine_docs` branch. For production documentation, refer to the `main` branch.
