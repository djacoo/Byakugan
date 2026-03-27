# Mobile App — Working Standards

## What This Project Type Demands
Mobile apps run on hardware the developer does not control, under memory pressure, with intermittent networks, in the background, and across OS versions. Every assumption about resources, connectivity, and lifecycle must be tested. The main thread is sacred — blocking it is always a bug.

## Before Starting Any Feature
- Define the offline behavior: what works without a network? What shows stale data? What is disabled?
- Define the loading, error, and empty state for every screen that fetches data.
- Identify all required permissions. Each must be requested at the moment of use, not at startup.
- Confirm the minimum supported OS version and test the feature against it.
- Identify all deep links and navigation entry points and validate that parameters are sanitized.

## Architecture Standards
- Use a strict layered architecture: UI → ViewModel → UseCase → Repository → DataSource.
- ViewModels expose observable state (not raw data). UI observes and renders — nothing else.
- Repositories are the single source of truth. They decide whether to serve from cache or network.
- The domain layer (UseCases) has no platform or framework dependencies. It is pure logic.
- Use dependency injection for all non-trivial dependencies. Never instantiate services inside ViewModels.

## How to Approach Any Task
1. Identify which layer the task belongs to. Write code in the right layer, not the convenient layer.
2. If adding a new screen: define the state model first (loading / success / error / empty), then the ViewModel, then the UI.
3. If adding a network call: implement in DataSource → Repository → UseCase order. Never call the network from the UI.
4. Write unit tests for the ViewModel and UseCase before considering the logic done.
5. Test on a real device (or a device farm) for the target OS version, not just the simulator.

## Non-Negotiable Rules
- No I/O of any kind on the main thread. No file reads, no DB queries, no network calls, no heavy computation.
- All user-facing strings in a localization file. No hardcoded English strings in the UI layer.
- All images appropriately compressed and sized. No loading a 4K image for a 64pt thumbnail.
- State must survive a process death and be restored correctly (screen rotation, background kill).
- Every network error mapped to a user-visible message with a retry action. Never a silent failure.
- Accessibility: all interactive elements labeled, tap targets ≥ 44pt, color is not the sole information carrier.

## Performance Standards
- 60fps target for all scrolling and animations. Any animation that drops frames is a bug.
- App launch time measured. Cold start under 2 seconds is the target.
- Image loading handled by a caching library (Coil, Glide, Kingfisher). No manual image decoding on the main thread.
- Memory profiled for long sessions. A growing memory footprint is a bug.
- Lists with more than 20 items use lazy/virtual rendering.

## Security Standards
- Sensitive data (tokens, credentials, PII) stored in Keychain (iOS) or EncryptedSharedPreferences / Keystore (Android).
- No sensitive data in logs, crash reports, or analytics events.
- Deep link parameters treated as untrusted user input. Validate everything.
- Certificate pinning for apps that handle financial or health data.
- ProGuard/R8 enabled on Android release builds.

## Definition of Done
- [ ] Feature works on minimum supported OS version.
- [ ] Feature works on a real device, not just a simulator.
- [ ] No main thread I/O (verified with StrictMode on Android / Main Thread Checker on iOS).
- [ ] Loading, error, and empty states all implemented and tested.
- [ ] Offline behavior defined and implemented.
- [ ] All strings localized.
- [ ] Accessibility labels and tap targets verified.
- [ ] Unit tests cover ViewModel and UseCase logic.
- [ ] No sensitive data in logs.
- [ ] State survives process death and is correctly restored.
