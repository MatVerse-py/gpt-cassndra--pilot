# Codex web

Codex is OpenAI's coding agent for reading, editing, running, and reviewing code. It can help users understand unfamiliar repositories, implement changes, fix bugs, run checks, and prepare pull requests.

**Codex web** refers to the browser-based Codex experience. **Codex cloud** refers to the remote execution environment Codex uses when a delegated task runs outside the user's local machine. In practice, users start and monitor tasks from Codex web, while Codex cloud provides the isolated workspace where the task can inspect the repository, run commands, and produce changes.

## Codex web setup

Go to [Codex](https://chatgpt.com/codex) and connect your GitHub account. This lets Codex work with code in selected repositories and create pull requests from its work.

Codex availability and usage limits depend on your ChatGPT plan and workspace policy. See the [Codex pricing documentation](https://developers.openai.com/codex/pricing) for current plan details. Enterprise workspaces may also require [admin setup](https://developers.openai.com/codex/enterprise/admin-setup) before users can access Codex.

---

## Work with Codex web

- [Learn about prompting](https://developers.openai.com/codex/prompting#prompts): Write clearer prompts, add constraints, and choose the right level of detail to get better results.
- [Common workflows](https://developers.openai.com/codex/workflows): Start with proven patterns for delegating tasks, reviewing changes, and turning results into pull requests.
- [Configuring environments](https://developers.openai.com/codex/cloud/environments): Choose the repository, setup steps, dependencies, and tools Codex should use when it runs tasks in the cloud.
- [Delegate work from the IDE extension](https://developers.openai.com/codex/ide/features#cloud-delegation): Start a cloud task from your editor, monitor progress, and apply resulting diffs locally.
- [Delegating from GitHub](https://developers.openai.com/codex/integrations/github): Use Codex with GitHub pull requests and reviews.
- [Control internet access](https://developers.openai.com/codex/cloud/internet-access): Decide whether Codex can reach the public internet from cloud environments and when to enable it.

## Repository documentation notes

This file uses absolute `https://developers.openai.com/codex/...` links instead of root-relative `/codex/...` links so the documentation remains usable from GitHub, local Markdown viewers, and other non-OpenAI documentation hosts.

Terminology is kept consistent with OpenAI documentation: use **Codex web** for the browser product surface and **Codex cloud** for delegated remote task execution.