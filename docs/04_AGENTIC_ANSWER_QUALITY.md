# Agentic Answer Quality

## Problems observed in earlier versions

Earlier versions sometimes:
- returned blank answers
- generated startup-style hallucinated responses
- ignored retrieved evidence
- failed to answer basic questions
- over-focused on search snippets instead of page reads

## Release approach

The system now follows this hierarchy:

1. Runtime/tool evidence
2. Full page reads
3. Notes and candidate links
4. Follow-up discussion context
5. Multi-pass synthesis
6. Answer-first evidence fallback

## Important principle

A partially grounded answer is usually better than:
- an empty answer
- a generic hallucinated answer
- "No answer produced"
- a reference dump with no answer

When Ollama returns a blank response or times out after the second pass, the CLI should still produce a useful answer from retrieved pages. The fallback must put a **Direct answer** first, then explain uncertainty and list the evidence used afterwards. References are support for the reply, not a replacement for the reply.

## Guidance for future development

The agent should:
- retrieve more evidence before giving up
- widen scope gradually
- distinguish grounded evidence from speculation
- use linked pages recursively
- remember recent discussion context
- answer first, then cite the pages and tool evidence used
