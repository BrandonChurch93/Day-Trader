# Practice picks

AI traders on the practice desk write their decisions here, one file per decision:
`picks/<TRADER ID>/<pick id>.json`, for example `picks/A01/20261125T1530Z.json`.

The form of a pick is in `practice/picks.py` on the main branch. The practice desk (a plain program on a timer) reads
this branch, checks each pick against the trader's pretend budget and limits, places the order and keeps the records
on the `practice-records` branch. Pretend money only.

A pick is fixed the first time the desk sees it. To change your mind, write a new pick. Do not edit an old one.
