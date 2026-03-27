# Desktop Application — Working Standards

## What This Project Type Demands
Desktop apps run on hardware and OS environments you do not control, alongside hundreds of other applications competing for the same resources. Users expect native behavior — your app must feel like it belongs on the platform, respond instantly to input, recover from crashes, and never lose their work. The main thread runs the UI; blocking it for any reason is always a bug.

## Before Starting Any Feature
- Confirm the target platforms and minimum OS versions. Every API choice must be compatible.
- Identify all I/O the feature requires: file system, network, database, hardware. Every one of these runs off the main thread.
- Define the persistence strategy: where does user data live, what format, and how does it survive process death?
- Determine the update behavior: is this a feature that requires a new app version? Does it need migration logic for existing data?
- Identify platform conventions that apply to this feature: keyboard shortcuts, context menus, drag-and-drop, system dialogs.

## Architecture Standards
- Strict separation of the UI layer from business logic. UI code is not testable; keep it thin.
- All heavy work (file I/O, network, computation, database queries) runs on background threads/queues.
- A message-passing or observable-state pattern connects the background work to UI updates.
- Data persistence uses the platform's canonical locations: documents folder for user documents, app data folder for application state, cache folder for derived/deletable data.
- The application must handle all lifecycle states: launch, background, foreground, low memory, crash recovery, and update.

## How to Approach Any Task
1. Identify the thread model for the feature: which operations happen on which threads? Plan this before writing.
2. Implement the business logic layer first, independently of the UI. Test it independently.
3. Build the UI layer on top, using the observable state pattern to receive results from background work.
4. Test state persistence: does the feature survive a forced quit and relaunch with the correct state?
5. Test on a real machine with the minimum supported OS version, not just the latest.

## Non-Negotiable Rules
- No file I/O, no network calls, no database queries, no heavy computation on the main thread.
- No loss of user work. Auto-save unsaved state. Recover from unexpected quit.
- Platform keyboard shortcuts must work: Cmd+Z/Ctrl+Z for undo, Cmd+W/Ctrl+W for close, etc.
- Use system dialogs for file open/save, color picking, font selection. Never re-implement them.
- App must handle system sleep/wake, network connect/disconnect, and window resize/move gracefully.
- Never write to the application bundle directory at runtime.
- Memory must not grow unboundedly in long sessions. Profile after several hours of use.

## Platform Behavior Standards
The app must follow the platform's human interface guidelines:
- **macOS**: menu bar with standard menus, Dock badge for background activity, system appearance (light/dark), Accessibility APIs (VoiceOver).
- **Windows**: taskbar integration, high-DPI awareness (per-monitor), Windows theme support, system tray for background apps.
- **Linux**: XDG Base Directories, system theme integration, keyboard shortcut consistency with the desktop environment.

## Persistence Standards
- Use a robust local database (SQLite) for structured data. Raw file parsing is acceptable only for standard formats.
- Database schema migrations handle version upgrades correctly — test the migration from every previous shipped version.
- Backup and export are user-accessible. Users own their data.
- Never store credentials in plain text. Use the platform keychain.

## Testing Standards
- Unit test all business logic independently of the UI framework.
- Integration test data persistence: write data, quit, relaunch, verify data is intact.
- Test crash recovery: force-quit mid-operation, relaunch, verify no data loss.
- UI automation tests for critical flows using the platform's accessibility APIs.
- Test on the minimum supported OS version before every release.

## Definition of Done
- [ ] No blocking operations on the main thread (verified with thread profiler).
- [ ] User data is not lost on crash or force-quit.
- [ ] State is correctly restored after relaunch.
- [ ] Platform keyboard shortcuts work correctly.
- [ ] System dialogs used for file operations.
- [ ] Memory does not grow unboundedly in a 1-hour session.
- [ ] Feature tested on minimum supported OS version.
- [ ] Accessibility: all interactive elements are reachable via keyboard and labeled for screen readers.
- [ ] Database migration tested from the previous released version.
