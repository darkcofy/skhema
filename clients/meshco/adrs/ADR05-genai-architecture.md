# ADR05: LLM Gateway + MCP server for GenAI surfaces

<!-- skhema:elements genai, semantic, catalog -->
<!-- gnosis:concepts DataProduct, SemanticModel -->

**Status:** Accepted
**Date:** 2026-04-19
**Deciders:** Alice Chen (Head of Platform), Bob Murphy, ML Engineering Lead

## Context

MeshCo wants to expose data products to natural-language querying (a retail
assistant for merchandising, an ops copilot for platform SREs) without
letting LLMs hallucinate numbers. Three architectural options were
considered: (a) point-solution LLM per use case, (b) unified gateway +
tool-calling, (c) full agent framework (LangChain/LangGraph end-to-end).

## Decision

Adopt a **unified GenAI gateway** combining:

1. **LLM Gateway (LiteLLM)** — unified proxy over Bedrock Claude, Titan,
   and local Llama. Model choice is a config change, not code.
2. **MCP Server** (Model Context Protocol) — exposes MeshCo data products
   and semantic-layer queries as tools to any MCP-speaking agent.
3. **RAG pipeline + Vector Store** (pgvector on RDS) — retrieves product
   copy, concept definitions, and gnosis ontology to ground responses.
4. **Guardrails Engine** — PII detection, prompt-injection defence,
   retail-brand-safety policy.
5. **Prompt Registry + Evaluation Framework** — versioned prompts, offline
   and online evals via Braintrust.

Agents never hit the LLM directly; they go through MCP → Guardrails → LLM
Gateway.

## Alternatives considered

### Per-use-case LLM integration

- Pros: Each team moves fast, no shared infra to maintain.
- Cons: Prompts drift, governance is impossible, cost is unattributable,
  guardrails get re-invented per team. The failure mode we're trying to
  avoid in every other layer of the mesh.

### Full agent framework (LangChain / LangGraph)

- Pros: Batteries-included, large community, reference implementations.
- Cons: Framework churn (LangChain has had three major API rewrites),
  heavy abstractions over a fundamentally simple request→response model,
  lock-in. We keep LangChain as an option inside the RAG pipeline only.

## Consequences

- **Trust posture:** LLMs never invent numbers. Every metric in an answer
  is sourced from the semantic layer and cited back to the catalog.
- **Governance:** one Prompt Registry, one Guardrails Engine, one eval
  harness. Platform team owns them.
- **Model flexibility:** switching Bedrock Claude to Azure OpenAI or
  local Llama is a LiteLLM config change. Application code is untouched.
- **MCP bet:** MCP is a young protocol. We're betting on it as the
  standard agent-to-tool interface. Risk: MCP is superseded by something
  else; mitigation: the LLM Gateway layer is the stable surface, MCP is
  one adapter on top.
- **Cost:** Bedrock Claude at expected volume is ~$2–4k/month initially.
  Prompt caching is enabled on the gateway.
- **Compliance:** every request flows through guardrails; every response
  is logged with redaction. Meets EY's data-protection requirements.

## Links

- [Model Context Protocol](https://modelcontextprotocol.io)
- [LiteLLM](https://www.litellm.ai/)
- Related: ADR03 (Contracts-first), ADR04 (Unity Catalog)
