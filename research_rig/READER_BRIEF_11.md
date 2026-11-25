# Reader brief for draft plan 11

The lead pastes the text between the lines into one helper's first message. The only thing to change is FOLDER, the full path of one reader folder, for example `~/workspace/rig/data/edgar_11/reading/design/kimi_k3/b007`. Spawn the helper on the model named in the folder path (the part of the folder path before bNNN, also `reader` in its `manifest.json`).

After the helper says it is done, run `python3 check_11_answers.py FOLDER` from `research_rig/`. If it refuses, send the same helper its fault list once and ask it to rewrite `answers.jsonl`. If the second file still has faults, run `python3 check_11_answers.py FOLDER --second-try`; each answer still missing or bad becomes score 0 and is flagged. Do not send a third time.

Gap, stated plainly: a helper has tools. That it uses no tool other than reading its own folder and writing one file is an instruction, not something this set-up can enforce. The checker sees only the answers file. It cannot see whether the helper searched the web or opened another folder. The lead should spawn each reader with no other context, never in a thread that has seen prices, results or another reader's answers, and should look at the helper's tool calls afterwards where the platform shows them.

---

You are a reader for a research test. Your folder is FOLDER.

1. Read FOLDER/INSTRUCTION.txt. It tells you the task and the answer format.
2. Read FOLDER/manifest.json. It lists your releases under "events", each with its file.
3. Read each release file in FOLDER/events/, in the order the manifest lists them, and score it as INSTRUCTION.txt says.
4. Write your answers to FOLDER/answers.jsonl: one JSON line per release, exactly the four keys event_id, input_sha256, score and reason, and nothing else in the file.

Rules:
- Use only the files in FOLDER. Do not open any other file or folder, including other readers' folders.
- Do not search the web, fetch a page, run code, look up a price or a news story, or ask another agent. The only tools you may use are reading the files in FOLDER and writing FOLDER/answers.jsonl.
- Do not try to remember how any of these stocks moved after its filing time.
- When answers.jsonl is written, reply with one line: "done, N answers", where N is the number of lines. Nothing else.

---
