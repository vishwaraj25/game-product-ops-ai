# Project Eclipse Simulation

Project Eclipse is a fictional live-service multiplayer game used as the MVP
data world for Product Ops AI.

## Game Concept

Project Eclipse is a squad-based sci-fi arena game where players pilot exosuits
called Frames. The core loop is:

1. Queue into short multiplayer matches.
2. Earn XP, upgrade materials, and premium currency offers.
3. Upgrade Frame modules and unlock cosmetics.
4. Return for ranked progression, LiveOps events, and limited store bundles.

## Modes

- `ranked`: Competitive 3v3 arena with MMR, placement matches, and seasonal rank
  rewards.
- `casual`: Lower-pressure arena queue used by new and engaged players.
- `rift_raid`: Co-op boss encounters used for weekend events and upgrade
  materials.
- `training`: Tutorial and warm-up mode.

## Economy

- Soft progression materials come from matches and events.
- Premium currency is called `Lumen`.
- Event currencies include `Bloom Shards` and `Nebula Cores`.
- Monetization focuses on battle passes, cosmetic bundles, event bundles, and
  premium currency packs.

## Player Segments

- `new`: recently acquired players learning the core loop.
- `engaged`: regular players who play several modes.
- `competitive`: ranked-focused players sensitive to matchmaking quality.
- `spender`: monetizing players who buy cosmetics and event bundles.
- `lapsed_returning`: players returning during events or after patches.

## Timeline

### Patch 1.2.0: Aurora Arsenal

Released on 2026-05-07.

This patch adds two weapons, improves mobile stability, and increases upgrade
material drop rates. It is intended to create a healthy content bump with mild
economy risk.

### Void Bloom Festival

Runs from 2026-05-10 through 2026-05-17.

This casual-focused collection event increases casual sessions and cosmetic
bundle revenue without creating major stability or retention issues.

### Patch 1.3.0: Ranked Integrity Update

Released on 2026-05-28.

This patch tightens ranked matchmaking bands, increases MMR confidence
weighting, and reduces party skill-delta tolerance. The design intent is fairer
ranked matches, but the simulated outcome is a queue-time spike for ranked
players, especially competitive and returning segments.

Expected observable effects:

- ranked average queue time rises after 2026-05-29
- ranked matchmaking failure rate rises
- ranked D1 and D7 retention drop
- competitive ranked DAU declines
- reviews increasingly mention matchmaking and MMR
- revenue from competitive players softens because ranked sessions become
  shorter and less frequent

### Nebula Siege Weekend

Runs from 2026-06-05 through 2026-06-08.

This Rift Raid event offers strong rewards and an event bundle. The event also
ships an experimental Android shader variant that causes reward-screen crashes
on mid-tier Android devices.

Expected observable effects:

- Rift Raid sessions increase during the event
- Android crash reports spike for `android_shader_cache_reward_screen`
- crash-related reviews increase
- Android store purchases underperform despite elevated event intent
- Patch 1.3.1 on 2026-06-09 reduces the crash issue

### Patch 1.3.1: Nebula Hotfix

Released on 2026-06-09.

This hotfix relaxes ranked search expansion after 90 seconds and fixes the
Android shader cache crash. Queue times and crash rates improve, but do not
fully return to pre-1.3 levels immediately.

## Future Investigation Scenarios

### Scenario 1: Why did ranked retention drop?

Likely answer to uncover:

Patch 1.3.0 tightened matchmaking too aggressively. Ranked queue times and
failure rates increased, competitive players played fewer sessions, and reviews
started mentioning MMR and long queues.

Relevant sources:

- `patch_notes`
- `session_analytics`
- `telemetry_metrics`
- `player_reviews`
- `revenue_metrics`

### Scenario 2: Did Nebula Siege perform as expected?

Likely answer to uncover:

The event increased Rift Raid demand, but Android crashes suppressed player
experience and store purchases. Revenue impact was mixed: PC and iOS performed
well, while Android underperformed during the crash window.

Relevant sources:

- `liveops_events`
- `crash_reports`
- `session_analytics`
- `store_purchases`
- `revenue_metrics`
- `player_reviews`

### Scenario 3: Why did revenue soften after Patch 1.3?

Likely answer to uncover:

Competitive player revenue softened because ranked friction reduced session
frequency and retention. Nebula Siege temporarily lifted event spending, but
Android instability limited upside.

Relevant sources:

- `revenue_metrics`
- `store_purchases`
- `session_analytics`
- `patch_notes`
- `crash_reports`

### Scenario 4: Was Patch 1.3.1 enough?

Likely answer to uncover:

Patch 1.3.1 improved Android crash reports and reduced ranked queue times, but
ranked retention remained below the pre-1.3 baseline, suggesting further
matchmaking tuning may be needed.

Relevant sources:

- `patch_notes`
- `crash_reports`
- `session_analytics`
- `player_reviews`
