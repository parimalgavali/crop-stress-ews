# ADR 0085: Explicit offline visit packs

Status: accepted, 2026-11-27. Story #181, after #180.

Offer field checkboxes and an explicit save action. A pack freezes selected monitored field
boundaries, personal names, bilingual warning/evidence text, actual warning/image dates,
bilingual inspection checklist, Live as_of, saved_at and source attribution. Warning text uses
existing speechText, including low-risk limits; unavailable forecasts remain unavailable.
A snapshot never recalculates forecasts. Relative ages are explicitly relative to Live as_of.

Store at most five packs / 4 MiB total in cropews.visit-packs.v1, separately from the atomic
local-work snapshot (ADR 0080). Validate reads and preserve unreadable data. One setItem commits
a pack list; quota/read/write failures preserve existing packs. Pack deletion only deletes the
pack; visits continue in the original observation store and normal backup. Packs are excluded
from backup just like other offline caches. Storage eviction remains possible and is explained.

Before persisting a pack, use a bounded service-worker message/acknowledgement to cache the
scope root and loaded same-origin /assets/*.js and *.css. Report app-download failure separately
from data-storage failure; neither claims success. The worker validates the asset list, replies
only after cache.addAll finishes and cached JS/CSS content types are verified, and uses CACHE=cropews-v2 because caching rules changed.
No cross-origin request, OSM tile, satellite photo or alert service is prefetched.

Saved packs can open without Live data, even from the root Replay screen. They have their own
frozen warning, evidence dates, shared checklist, read-aloud, local visit form and static SVG
boundary outline. No street map, fresh forecast, remote photo or alert link is offered. Read
controls identify the saved visit, stay in its card on phones and cancel the preceding queue.

Validation uses an actual production service worker: prepare once, disable networking, reopen
from root, record a visit and remove the pack while retaining the visit. A download-failure test
checks that no pack is persisted. EN/DE phone axe checks cover open saved-visit forms.
