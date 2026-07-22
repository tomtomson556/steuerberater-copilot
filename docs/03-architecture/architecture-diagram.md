# Architecture Diagram

## Scope

This diagram describes the synthetic offline MVP plus experiment-branch demo
surfaces. It does not describe a productive Steuerberatung system.

```mermaid
flowchart TB
    user[Developer or reviewer]
    cli[Offline MVP CLI]
    evalcli[Evaluation CLI]
    api[FastAPI demo boundary]
    docker[Docker runtime]
    azure[Azure reference-cloud skeleton]

    fixtures[(Synthetic fixtures)]
    gateway[Policy and Privacy Gateway]
    risk[Risk classification]
    review[Human Review Gate]
    prompt[Versioned prompt builder]
    policy[Model Invocation Policy]
    fake[FakeModelProvider]
    parser[Structured parser and validators]
    response[Response Gateway]
    rag[RAG workflow]
    retriever[LocalDocumentRetriever]
    docs[(Synthetic source documents)]
    eval[Offline evaluation suites]
    obs[Structured logs and metrics]

    user --> cli
    user --> evalcli
    user --> api
    api --> docker
    docker -. optional portfolio deployment .-> azure

    cli --> fixtures
    api --> fixtures
    fixtures --> gateway
    gateway --> risk
    risk --> review
    review --> prompt
    prompt --> policy
    policy --> fake
    fake --> parser
    parser --> response
    response --> review

    api --> rag
    rag --> retriever
    retriever --> docs
    rag --> policy
    rag --> parser

    evalcli --> eval
    eval --> fixtures
    eval --> docs
    eval --> fake

    api --> obs
    obs -. JSON lines and counters only .-> user
```

## Dataflow

1. CLI, evaluation CLI, and FastAPI demo receive only synthetic fixture IDs or
   local synthetic evaluation cases.
2. Gateway, risk classification, and Human Review Gate run before model
   invocation.
3. Prompt text is built inside the workflow boundary and is not returned by API
   responses.
4. Standard tests and demos use `FakeModelProvider`.
5. RAG uses local synthetic source documents and local retrieval.
6. Parsers, validators, and response gateway checks run before draft material is
   exposed.
7. Observability emits structured metadata and counters, not raw prompts, raw
   model payloads, secrets, or real data.

## Threat and failure boundaries

| Boundary | Purpose | Failure handling |
| --- | --- | --- |
| Gateway | Stop disallowed or privacy-sensitive synthetic inputs before continuation. | Restrictive decision and Human Review visibility. |
| Human Review Gate | Prevent automatic continuation for elevated internal risk classes. | No productive action; draft material remains review-bound. |
| Model Invocation Policy | Enforce prompt identity, version, and size limits. | Policy errors stay separate from provider errors. |
| Parser and validators | Reject malformed or semantically invalid structured output. | Error path without raw prompt or response disclosure. |
| RAG evidence boundary | Keep source use local and synthetic with citations. | Abstention or uncertainty when evidence is missing. |
| API boundary | Adapt workflows to HTTP for demo only. | HTTP error translation without full prompt exposure. |
| Observability boundary | Emit runtime metadata for review. | No prompts, secrets, model payloads, or real data in log events. |
| Azure IaC boundary | Demonstrate one reference-cloud deployment path. | Scale-to-zero and deletion remain the cost off switches. |

## Non-goals

The architecture does not include productive data paths, DATEV, Agenda, ELSTER,
banking, email, autonomous tax decisions, automatic submissions, Multi-Cloud
support, or productive tax advice.
