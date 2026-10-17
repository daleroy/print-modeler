---
description: Start or continue a 3D print modeling job with the print-modeler agent
argument-hint: <what to make, or jobs/<slug> plus changes>
---
Use the print-modeler subagent for this request: $ARGUMENTS

When it returns:
- Show me its summary and display each preview image it lists (read the PNG files).
- If it returned NEEDS INPUT or questions, ask me those questions (AskUserQuestion is fine), then pass
  my answers back to the same agent with SendMessage so it keeps its context, instead of answering them yourself.
- Do not approve a draft or finalize on my behalf.
