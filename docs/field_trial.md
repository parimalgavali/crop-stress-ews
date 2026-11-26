# A small field trial: do warnings help visits?

**Status: proposed plan, not a completed trial.** Story #171. The app is a research/portfolio
project. Its warnings predict satellite-observed changes, not a diagnosed cause or harvest loss.
Ask a crop adviser to review the inspection wording and this plan before inviting participants.

## Start small

Invite a few willing NRW winter-wheat farmers and one crop adviser for one spring season.
Agree the fields, visit budget and dates before starting. Get permission to access each field.
Explain what is recorded, who can see it, how long shared copies are kept, and how participants
can withdraw. Set a deletion date and name the person responsible for shared records before
collection. Do not upload names, precise locations or photos without explicit agreement.
Participation and record sharing are optional; do not contact or recruit anyone automatically.

## Compare fair visits

1. Save forecasts before outcomes are known using the existing forecast log. Keep field id,
   issue date, forecast window, model version and evidence quality with each visit assignment.
2. Each week reserve the same agreed inspection budget. Use the scouting queue for some visits
   and randomly choose other eligible fields for comparison, including fields without warnings.
   Record selection rules and fields not visited. Do not visit only red fields.
3. Visit within the forecast window where practical. Record the actual visit date; do not
   rewrite it to the alert date. If safe, use repeat visits near the end of the window.
4. Use the same observation checklist for both groups: uneven growth, standing water, leaf
   changes, no visible problem, or uncertain. Record severity, a suspected cause only if known,
   and inspection minutes. Keep alert information hidden from the reviewing adviser where
   practical to reduce the chance that the warning influences their judgement.
5. A crop adviser reviews findings independently. Keep uncertain or unvisited cases separate;
   they are not evidence that the warning was wrong or that the crop was healthy.

## Use the existing app

Select a monitored field in **Live → More things you can do → Field visit record**. Record
what was seen, when, who visited, severity and suspected cause ("not sure" is allowed).
These records stay in that browser on that device. **Export all records (JSON)** downloads a
copy; clearing browser storage can remove records. Arrange exports with participants before
collection and transfer them only by an agreed private route.

The current form does not have dedicated fields for visit duration, selection group, alert
issue date or reviewer decisions. Keep those in a separate agreed study sheet linked by field
id and visit date. The exported `review_status` starts as `unreviewed`; review decisions belong
in that sheet. A thumbs-up/down check is not a confirmed diagnosis or a training label.

## Decide whether it helped

Report counts and uncertainty, with unknown cases visible:

- **Useful visits:** visits where a reviewer confirms an observation worth following up,
  divided by completed visits, separately for queue and comparison visits.
- **Unconfirmed warnings:** warned field-windows checked through the window without a relevant
  finding. A single early visit with nothing visible does not prove a false alarm.
- **Missed problems:** confirmed findings in sampled non-warned field-windows. This estimates
  misses only in the sampled population; it is not sensitivity across all fields.
- **Time and burden:** travel/inspection minutes, repeated alerts per field episode, useful
  findings per inspection hour, and participants' willingness to keep using the system.
- **Satellite outcomes:** score the original canopy target separately using the forecast log.
  A visible field symptom and a satellite canopy event are different outcomes.

Before starting, agree the minimum worthwhile improvement in useful findings per inspection
hour and the maximum acceptable alert burden with participants. Record these targets and the
analysis plan before seeing results. Compare within the same season and account for repeat
visits to a field. A small pilot tests feasibility; it does not establish yield savings.
If there is no useful advantage, revise the workflow or stop expansion. Use later seasons for
confirmation before changing model claims or adopting new alert thresholds.
