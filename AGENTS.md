# Agent Working Guidelines

- Use GPT-6-luna with high reasoning effort for all sub-agents.
- Make extensive use of sub-agents whenever useful.
- The primary agent should handle complex work directly. Delegate simple and repetitive work to sub-agents.
- Keep code simple, clear, concise, and easy to understand. Avoid unnecessary complexity.
- Activate Green and Red agent teams when needed for intermediate reviews and other checkpoints. The Green team should assess correctness and readiness; the Red team should challenge assumptions and look for defects and risks.

## Project Knowledge Management

- Use the kg and Graphify skills to maintain project knowledge. Start each session with `/kg-orient`, reading `wiki/hot.md` and `wiki/overview.md` before consulting the graph.
- Use the graph to find relationships, the wiki to recover context, and the original source files to verify claims. Wiki pages and graph edges are derived views, not primary evidence.
- Record current work, blockers, validation results, and the next bounded action in `wiki/hot.md`. Keep decisions and procedures linked to their source evidence and maintain indexes and the append-only `wiki/log.md`.
- Ingest new source material with `/kg-ingest`. Refresh changed code with `/kg-update`; refresh document semantics with the Graphify skill. Track extraction scope and source hashes so freshness is explicit.
- Preserve source material during knowledge-management operations. Do not scan raw ERA5 arrays, credentials, local runtime outputs, or generated wiki/graph artifacts as project source inputs.
- Validate the pinned wiki schema and links with `/kg-lint` after knowledge changes. Use `/kg-reflect` after multiple ingests or at a substantive checkpoint.
- Preserve unresolved failures and scientific limitations. Inventory checks, toy tests, and graph structure do not establish real weather skill or operational readiness.
