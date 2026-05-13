# Multi-Program OpenEvolve Framework — Requirements (Draft)

## Goal

Build a framework that allows running OpenEvolve experiments across multiple test programs, not just cavitydetection. Users should be able to easily add new programs and run the same prompt variants across all of them.

## Current State

- OpenEvolve is hard-coded for `cavitydetection`
- Prompt variants are manually managed in `openevolve/prompts/`
- Adding a new program requires manual setup (new initial_program.c, config, evaluator)
- Only one program can be tested per experiment run

## Desired State

- Define multiple test programs in a single config
- Run one experiment variant across all registered programs
- Easy registration of new programs (what would "easy" look like?)
- Automated prompt discovery/management (or explicit config?)

## Open Questions

1. **Program registration:** How should new programs be added? What metadata is needed?
2. **Experiment grouping:** Should one experiment run across all programs, or can you select a subset?
3. **Results comparison:** How do you want to view/compare results across programs?
4. **Prompt variants:** Should these be shared globally or per-program?
5. **Evaluation metrics:** Are baseline access counts program-specific or standardized?

## Success Criteria (To Define)

- [ ] Can add a new test program with minimal manual work
- [ ] One `make` command runs a prompt variant across multiple programs
- [ ] Results dashboard/report compares performance across programs
- (More to be defined...)

---

**Next step:** Refine these questions and clarify the architecture before coding.
