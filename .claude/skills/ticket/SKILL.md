---
name: ticket
description: Start or continue a Countersign ticket through the spec, plan and tasks loop. Writes specs/<ticket>/spec.md from specs/TEMPLATE/ if it is missing, writes the plan and tasks in the chat (they go in the pull request description, not the repo), stops for Paul's approval, then works the tasks one at a time.
argument-hint: "[ticket-id, e.g. C-103]"
disable-model-invocation: true
allowed-tools: Bash(git status *) Bash(git branch --show-current) Bash(git switch -c *)
---

# Ticket $ARGUMENTS

Repo state when this ran:

!`git status --short --branch`

Where things live: `specs/$ARGUMENTS/spec.md` is committed. The plan and the tasks are written
in the chat from `specs/TEMPLATE/plan.md` and `tasks.md`, and end up in the pull request
description; they are never committed. `specs/C-102/` is the one exception: its committed
`plan.md` and `tasks.md` are the worked example.

## 1. Find where we are

- If the current branch is `main`, propose `git switch -c` with the ticket id in lower case
  (`c-103`) and wait for Paul to agree.
- **No `specs/$ARGUMENTS/` folder:** go to step 2 and start with the spec.
- **`plan.md` and `tasks.md` exist in the folder** (only `specs/C-102/`): read all three and
  resume at the first unchecked task.
- **`spec.md` exists, and the plan and tasks are already in this conversation:** resume at the
  first unchecked task. Before trusting a checkmark, confirm the work is on disk and its check
  passes.
- **`spec.md` exists, no plan or tasks in this conversation** (a fresh session; the usual case):
  look for them in the pull request with `gh pr view --json body`. If it shows a plan and
  tasks, read them and resume as above. If there is no pull request, or its body has no plan,
  go to step 2: the spec stays as it is, and you write the plan and tasks.

## 2. Write the spec, then the plan and tasks (no code yet)

1. Ask Paul for the ticket's text if it isn't in the conversation: the guide page's "ships",
   "facts" and "done when". Don't guess a ticket's contents from its title.
2. Read `AGENTS.md`, the `.claude/rules/` file for each area the ticket touches, and the code
   those areas already have.
3. If `specs/$ARGUMENTS/spec.md` is missing, copy `specs/TEMPLATE/spec.md` there and fill it
   in: the behavior and acceptance criteria, each one checkable by a command or a test. If it
   exists and Paul has approved it, don't rewrite it; raise a question instead.
4. Write the plan and the tasks **here in the chat**, from `specs/TEMPLATE/plan.md` and
   `tasks.md` (`specs/C-102/` is the worked example). Don't create `plan.md` or `tasks.md`.
   - plan: the files, the functions with their signatures, the tests written first, the risks,
     and the questions Paul should be able to answer at the end.
   - tasks: small steps (about 10 minutes each), each with the command that proves it.
   - Some of the ticket may already be on disk (a fresh session, or Paul started by hand):
     compare each task with `git status`, `git log --oneline -5` and the files, and tick only
     the ones whose check passes now, with the evidence.
5. Mark anything you inferred rather than read as an open question.
6. **Stop.** Show Paul the spec (if you wrote it), the plan and the tasks, and wait. Do not edit
   code until he approves the plan. When he does, set the spec's `Status:` line to
   `approved by Paul`.

## 3. Work the tasks (after approval)

For each task, in order:

1. Write the test first when the task adds behavior. Run it and see it fail for the right
   reason.
2. Make the smallest change that passes. Stay inside the files the plan names; anything else
   is a question for Paul.
3. Run `/verify` for the projects you touched.
4. Tick the task in the chat's task list and add the check's summary line next to it.
5. Explain the diff to Paul in a few plain sentences, then propose a commit
   (`C-NNN: <what this adds>`). Commit only when he says so.

## 4. Finish

1. Delegate to the `reviewer` subagent with the ticket id, the spec path and the approved plan
   (paste it: the reviewer hasn't seen this chat), and to `security-reviewer` too if the diff
   touches SQL, settings, dependencies, `.claude/` or `.github/`. Fix critical findings, list
   the rest.
2. Update `AGENTS.md` and the matching rule file if a command, folder or convention changed.
3. Draft the pull request body from `.github/pull_request_template.md`: the plan and the ticked
   tasks go in its Plan and Tasks sections, and the AI assistance section is filled in
   honestly: what you generated, what Paul still has to verify.
