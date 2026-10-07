# Progress and setup checkpoints

## Working agreement

- Implement the supplied plan one phase at a time.
- Report each phase's delivered behavior and verification before advancing.
- Tell the user when browser-based account setup is needed.
- Keep all project work in this repository.
- Do not provision cloud resources before the local vertical slice works.

## Current status

- [x] Save project requirements in `PROJECT_PLAN.md`.
- [x] Authenticate GitHub CLI as `arthurlemon`.
- [x] Create private `arthurlemon/hydro-agentic` repository.
- [ ] Push planning documents through the personal SSH alias.
- [ ] Phase 0: Python bootstrap, tooling, configuration, and sample data.
- [ ] Phase 1: fully local vertical slice.
- [ ] Phase 2: MCP tool layer.
- [ ] Phase 3: Microsoft Foundry.
- [ ] Phase 4: Azure AI Search.
- [ ] Phase 5: persistent workflow state.
- [ ] Phase 6: human-in-the-loop workflow.
- [ ] Phase 7: observability.
- [ ] Phase 8: automated evaluations.
- [ ] Phase 9: Databricks adapter/simulation.

## Dependencies to resolve during implementation

The phase list describes delivery milestones; section 26 gives dependency order. Minimal state, backend approval enforcement, and idempotency must exist before enabling work-order creation, even though their fuller milestones appear after MCP/Foundry in the phase list.

For local development, internal incident persistence and draft preparation must be distinguished from the approval-gated operational action of work-order creation. The detailed tool contracts will make that distinction explicit.

A deterministic test double can validate orchestration plumbing, but it does not prove autonomous LLM tool selection. Choose the local model/provider when implementing the agent loop and report which mode was tested.

An old oil-degradation finding alone must not silently become a claim of currently confirmed degradation. Fixtures and procedure conditions must support the actual recommendation.

## Browser/account checkpoints

| When | Setup |
|---|---|
| Repository creation | GitHub CLI browser/device authorization as `arthurlemon`; SSH is already verified through `github.com-perso` |
| Phase 0 and deterministic local services | No cloud account required |
| Local model-backed agent loop | Confirm available local model or provider credentials before selecting the adapter |
| Phase 3 | Azure account/subscription, Foundry access, suitable region/model availability, project and model deployment |
| Phase 4 | Azure AI Search availability and permissions; verify Free Tier availability before provisioning |
| Optional Cosmos DB / Application Insights | Reuse Azure subscription and verify resource permissions/configuration |
| Optional real Databricks integration | Databricks workspace and model-serving credentials; not required for the mock |

Cloud offerings, SDKs, authentication, and free-tier availability must be checked against current documentation when those phases begin.
