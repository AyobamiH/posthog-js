# PostHog PR #4822: review corrections

Verified on 7 September 2026. The existing upstream PR remains open for maintainer re-review; this record is not an upstream approval or release.

PR: https://github.com/PostHog/posthog-js/pull/4822

## Exact source

- Reviewed head: `f1c3a289dfe75f546193c5e3985971551e9cbc5d`.
- Original upstream base: `6e9f93123007a549142dac183f55ab648140005f`.
- Corrected candidate: `90cbef84095826363b356d5687d1ab30a70d80df`.
- Final signed PR head: `df820ebb9cad671ba444bbde4d88661bf7f290c0`.
- Identical candidate/final source tree: `eecff7a3d53ea83e8a7788b86f89ee05679fac2a`.
- Existing contribution branch: `fix/3162-react-native-survey-shuffling`.
- Original unsigned history retained at `backup/4822-before-review-f1c3a289`.

GitHub's commit API reports `verified: true`, `reason: valid` for the final commit. Author: Ayobami Haastrup, `47716486+AyobamiH@users.noreply.github.com`; committer: GitHub. The commit has exactly one parent, the original upstream base. The contribution now consists of one verified signed commit, not a signed tip above unsigned contribution commits.

Signing was performed through a fork-only staging squash into `signing/4822-consolidated` using fork PR #3. Neither fork main nor upstream main was a merge target. Before updating the existing contribution ref, its old head was rechecked and matched the backed-up reviewed SHA. The final PR commit list was read back and confirmed the signed head.

## Corrections

`packages/react-native/src/surveys/components/Surveys.tsx` now derives configured question indices on copies at the event-serialization boundary. Both `sendSurveyEvent` and `dismissedSurveyEvent` call that same adapter before invoking the unchanged shared serializer. Legacy positional fields (`$survey_response`, `$survey_response_1`, etc.), modern question-ID response fields and the configured `$survey_questions` array remain available independently of display ordering or a prior render.

The source survey remains unchanged. Shuffling and the existing branching engine are not broadened by this correction. Branches that skip a question retain the configured response index instead of renumbering answered questions.

`.changeset/rn-survey-shuffling.md` now requests `minor` for `posthog-react-native`. No other package release is requested. The changeset was edited via the GitHub API; this record does not claim that the interactive changeset command ran.

The review delta consists of the event adapter, the minor changeset and one new test file. The full contribution has seven files; fork-only workflows and this evidence record are excluded.

## Final verification

Run: https://github.com/AyobamiH/posthog-js/actions/runs/34123368621

Job: https://github.com/AyobamiH/posthog-js/actions/runs/34123368621/job/101746276405

Workflow definition commit: `12fa54a0efc3ba6ed3bc62bafc18b51d19d4c2ea`.

The workflow checks out the exact signed PR source `df820ebb9cad671ba444bbde4d88661bf7f290c0`, verifies its signature/author/tree/parent, and runs with read-only repository permissions and explicit Bash pipefail. Each check contributes its actual outcome to a fail-closed aggregate.

| Check | Observed result |
| --- | --- |
| Commit identity and cryptographic signature | Verified, valid; expected author, tree and parent |
| Frozen-lockfile workspace installation | Passed |
| React Native/dependency build | 5 build tasks passed; React Native Babel compilation passed |
| Eight new tests on the reviewed event source | Exactly 7 expected response-payload assertions fail, 1 unanswered-dismissal control passes |
| Full React Native suite on the corrected signed source | 717 passed, 0 failed, 0 pending; 46 test files |
| React Native lint | 0 warnings, 0 errors |
| Formatting of the review-changed source/test files | Passed |
| Minor changeset assertion | Passed |
| Aggregate workflow | Success |

New regression/control coverage: shuffled and ordinary submissions, shuffled and ordinary dismissals, skipped-question branching attribution, direct sent/dismissed event serialization without prior rendering, and unanswered dismissal. Tests also assert falsy/array values, iteration/language metadata and non-mutation of frozen, unannotated survey definitions.

The stateful component tests use real navigation and the shared serializer, with native views and capture replaced by test doubles. No native-device smoke test or full-monorepo test run was performed. Fork results do not imply upstream CI approval.

Evidence artifact: `pr-4822-review-evidence`, ID `10019149510`, retained for 30 days by the final run. Contains source/signature proofs, red and green Vitest JSON reports, compact summaries, build/lint/format logs and aggregate outcomes.

The preceding run `34122732994` built and passed all 717 tests but failed its diagnostic checker: Vitest 1's JSON failureMessages omit assertion diffs, and the checker incorrectly searched them for a diff-only property name. The final workflow checks the exact seven expected test titles/counts and payload-assertion headings instead. The regression tests and production source were not relaxed or changed to fix that diagnostic failure.

## Maintainer follow-up

The upstream PR description was updated with the corrected implementation, minor release level and exact signed-source verification. Replies were posted to the blocking response-attribution review and minor changeset review. The blocking reply also confirms the signed consolidation. Review threads were left open for the maintainer; upstream PR #4822 was not merged or approved.

Blocking-thread reply: https://github.com/PostHog/posthog-js/pull/4822#discussion_r3949868087

Minor-changeset reply: https://github.com/PostHog/posthog-js/pull/4822#discussion_r3949869269
