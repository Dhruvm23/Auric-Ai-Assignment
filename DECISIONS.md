# DECISIONS.md

## Decisions Made Where the Brief Was Silent

1. **REST API over CLI.** The brief mentions a facilities dashboard calling `GET /rooms` and a reporting job parsing response timestamps — these are HTTP consumers. A CLI would break both integrations. FastAPI was chosen for built-in request validation (Pydantic), auto-generated OpenAPI docs, and minimal boilerplate.

2. **SQLite + SQLAlchemy.** ~200 employees and sequential room IDs make SQLite more than sufficient. SQLAlchemy ORM means switching to Postgres later is a connection-string change, not a rewrite. No infrastructure to manage, and the repo is fully self-contained.

3. **Soft delete for cancellations.** Bookings are marked `status: "cancelled"` rather than deleted. This preserves an audit trail (who booked what, when) and avoids data loss. The cancelled-booking slot is immediately freed for new bookings since conflict checks filter on `status = "active"`.

4. **Timezone stored on the Series record, not on individual bookings.** The series owns the recurrence rule and the timezone context. Individual bookings store only naive local timestamps (required by C1). This keeps the data model clean and avoids timezone info scattering across thousands of booking rows.

5. **"All-or-nothing" (R1) + "skip conflicts" (R2) interpretation.** These requirements sound contradictory at first. The interpretation: within a single DB transaction, generate all occurrences, skip the conflicting ones, and atomically insert the non-conflicting set. If *every* occurrence conflicts, the transaction rolls back and returns an error. If the DB fails mid-insert for any other reason, everything rolls back.

6. **`zoneinfo` (stdlib) for DST — no third-party dependency.** Python 3.9+ includes `zoneinfo` backed by the system's IANA tz database. This avoids pulling in `pytz` and its non-standard API. The system tz database is updated by the OS, which is the correct place to manage tz data for a server-side app.

## Questions I Would Ask the PM Before Shipping

- **What "local" means for timestamps.** C1 says naive local ISO strings. Local to *which* timezone? If a Berlin user books Denver room 3, is the stored time Berlin-local or Denver-local? Current implementation treats the first occurrence's wall-clock time as the reference and generates from there. We need a clear rule.

- **Maximum series length.** The office manager's complaint about 6-month ghost bookings suggests we should cap `repeat_until` (e.g., 6 months max) or add an expiry/review mechanism. No cap is enforced today.

- **Who can cancel a series?** Currently anyone can cancel any booking or series. Before shipping, we need auth and ownership rules — can only the creator cancel, or any admin?

- **What happens when a room is decommissioned?** If facilities removes a room, do we cascade-cancel its bookings? Notify users? The current API has no room management endpoints beyond the seeded list.

- **Multi-day or variable-length recurring bookings.** The brief says "weekly repeat." Are bi-weekly, daily, or monthly recurrences coming? The current architecture supports weekly only; extending to other intervals is straightforward but changes the API contract.

## Where AI Helped, and What It Got Wrong

- **AI wrote the initial project scaffold, models, schemas, and routing boilerplate.** This saved significant time on the mechanical parts of FastAPI + SQLAlchemy setup.

- **AI drafted the recurrence generator.** The core `zoneinfo` approach was correct, but the initial version constructed aware datetimes and then converted — this was unnecessarily complex. I simplified it: construct naive datetimes at the target wall-clock time, attach the tz for validation, then strip it. The wall-clock time is the invariant, not the UTC offset.

- **AI initially missed the `StaticPool` requirement for in-memory SQLite in tests.** In-memory SQLite databases are per-connection; without `StaticPool`, the test session and the table-creation call used different connections, so tables appeared missing. This is a well-known SQLAlchemy + SQLite testing pitfall.

- **Conflict detection SQL was correct on the first pass** — the strict-inequality approach for back-to-back handling is textbook interval overlap logic.

## What Was Deliberately Left Out

- **Authentication and authorization.** No auth layer. Every endpoint is open. In production, this would integrate with the company's SSO/OAuth system, and cancellation would check ownership.

- **Pagination.** `GET /bookings` returns all matching results. At ~200 employees this is fine; at scale, cursor-based pagination would be needed.

- **Room management endpoints.** Rooms are seeded on startup. There's no `POST /rooms` or `DELETE /rooms`. The facilities team would need these eventually.

- **Concurrency control.** SQLite's write lock is sufficient for ~200 users. Under heavy load, the conflict check + insert is not protected by a row-level lock, so two simultaneous requests could theoretically both pass the conflict check. Switching to Postgres with `SELECT ... FOR UPDATE` or an advisory lock would fix this.

- **Logging, monitoring, health checks.** No structured logging, no `/health` endpoint, no metrics. These are table stakes for a production service.

- **Booking modification (update).** You can cancel and re-create, but there's no `PUT /bookings/{id}` to change times in place.
