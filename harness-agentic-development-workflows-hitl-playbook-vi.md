# Playbook phát triển phần mềm agentic với Codex và HITL

**Runtime mục tiêu:** Codex CLI, Codex IDE và Codex trong ChatGPT desktop  
**Harness nền:** Repository Harness  
**Nguyên tắc:** repository giữ sự thật; Codex điều phối; custom agent thực thi;
skill cung cấp procedure; con người quyết định tại H1, H2 và H3.

Thiết kế này chỉ tham khảo ý tưởng phân tách workflow/agent/skill của Claude.
Không sử dụng `.claude/`, `CLAUDE.md`, Claude workflow JavaScript hay frontmatter
agent của Claude làm runtime implementation.

### Revision snapshot — 2026-09-13

- Nâng Codex CLI lên `0.154.0` và bật project agents trong `.codex/config.toml`.
- Chuẩn hóa sáu capability custom thành namespace `sk-*` và cập nhật mọi
  frontmatter, UI metadata, agent instruction, workflow routing và validator.
- Giữ ba orchestration skill ở namespace `wf-*`; giữ nguyên bốn Harness core
  skills.
- Hoàn thiện bốn custom agent TOML với sandbox và capability skill bắt buộc.
- Loại bỏ toàn bộ Claude runtime projection; Claude chỉ còn là nguồn tham khảo
  ý tưởng phân tách workflow/agent/skill.
- Bổ sung handoff contracts, H1/H2/H3 gates, null-result safeguards và bằng
  chứng fresh-session validation.

## 1. Kiến trúc Codex đích

Codex dùng ba cơ chế repository-native:

1. `AGENTS.md` cho instruction chain và repository policy.
2. `.agents/skills/<name>/SKILL.md` cho capability và reusable workflow.
3. `.codex/agents/<name>.toml` cho project-scoped custom subagent.

Ba workflow được triển khai dưới dạng Codex orchestration skills vì skill là
format của Codex cho reusable workflow. Tổng cộng có chín project skills:

### Orchestration skills

1. `wf-discover`
2. `wf-implement`
3. `wf-verify`

### Capability skills

Prefix `sk-` phân biệt capability skill do repository tùy biến với orchestration
skill `wf-*` và Harness core skills.

1. `sk-solution-design`
2. `sk-backend-engineering`
3. `sk-ai-engineering`
4. `sk-test-engineering`
5. `sk-quality-check`
6. `sk-release-check`

### Custom agents

1. `architect`
2. `backend-dev`
3. `ai-dev`
4. `reviewer`

Bốn Harness core skills giữ nguyên:

- `onboard-repository`
- `audit-onboarding-proposal`
- `encode-invariant`
- `improve-harness`

Trạng thái hiện hành: Codex CLI đã được nâng lên `0.154.0`; `.agents/skills/`
là catalog runtime duy nhất của repository; sáu capability custom dùng prefix
`sk-`; ba orchestration workflow dùng prefix `wf-`.

## 2. Repository layout

```text
AGENTS.md
.codex/
  config.toml
  agents/
    architect.toml
    backend-dev.toml
    ai-dev.toml
    reviewer.toml
.agents/skills/
  wf-discover/
  wf-implement/
  wf-verify/
  sk-solution-design/
  sk-backend-engineering/
  sk-ai-engineering/
  sk-test-engineering/
  sk-quality-check/
  sk-release-check/
docs/
  WORKFLOW.md
  workflows/handoff-contracts.md
  product/
  architecture/
  decisions/
  plans/active/
  plans/completed/
artifacts/
  handoffs/
  evidence/
scripts/
  validate-agent-harness.ps1
```

Không tạo projection skill. `.agents/skills/` là vị trí Codex tự discovery và
là canonical source duy nhất.

## 3. Rename capability skills

| Tên cũ | Tên Codex hiện hành | Phạm vi |
|---|---|---|
| `solution-discovery` | `sk-solution-design` | Discovery, impact, option, plan |
| `backend-workflow-engineering` | `sk-backend-engineering` | Server-side engineering |
| `ai-video-generation` | `sk-ai-engineering` | AI integration dùng chung |
| `test-engineering` | `sk-test-engineering` | Test design và implementation |
| `verification-and-evaluation` | `sk-quality-check` | Verification/evaluation read-only |
| `release-assurance` | `sk-release-check` | Security và release readiness |

Rename là một migration thống nhất: đổi directory, frontmatter, UI metadata,
agent instructions, workflow routing, docs và validation. Không giữ đồng thời
bản cũ nếu không có consumer tương thích đã được xác nhận.

## 4. Boundary của capability skill

| Skill | Trách nhiệm chính | Tài liệu chi tiết |
|---|---|---|
| `$sk-solution-design` | Discovery, impact analysis, option và implementation plan trước H1 | `SKILL.md` |
| `$sk-backend-engineering` | Interface, persistence, async execution, state, recovery và workflow backend | `references/*` theo mode |
| `$sk-ai-engineering` | Provider adapter, structured I/O, prompt/model, retrieval/tool, evaluation, cache và cost | `references/*` theo mode |
| `$sk-test-engineering` | Testcase traceability và automated tests từ requirement đã duyệt | `SKILL.md` |
| `$sk-quality-check` | Verification read-only theo command, acceptance criteria và rubric | `references/*` theo mode |
| `$sk-release-check` | Security và delivery-readiness review trước demo/submission/release | `SKILL.md` |

- `sk-solution-design` phân tích và đề xuất; không implement hoặc tự approve.
- `sk-backend-engineering` không hard-code framework. Chi tiết stack nằm trong
  repository hoặc reference riêng.
- `sk-ai-engineering` không hard-code video, audio, TTS, chemistry hay provider cụ
  thể trong capability entrypoint. Procedure đặc thù dự án nằm trong
  `references/project-extension.md`.
- `sk-test-engineering` không tự đặt expected behavior và không sửa production code
  chỉ để test pass.
- `sk-quality-check` luôn read-only; rubric domain được truyền qua task hoặc đọc từ
  repository.
- `sk-release-check` review readiness; không tự sửa finding hoặc hạ tiêu chuẩn.

Mỗi skill có `agents/openai.yaml` để Codex/ChatGPT hiển thị metadata và default
prompt. `name` trong frontmatter phải trùng directory.

## 5. Custom agent theo chuẩn Codex

Custom agent là file TOML độc lập trong `.codex/agents/`. Trường bắt buộc:
`name`, `description`, `developer_instructions`. Không pin model nếu muốn agent
kế thừa lựa chọn model/effort của session.

| Agent | Sandbox | Skill bắt buộc | Trách nhiệm |
|---|---|---|---|
| `architect` | `workspace-write` | `$sk-solution-design` | Chỉ sửa docs/design/plan được phép |
| `backend-dev` | `workspace-write` | `$sk-backend-engineering`, `$sk-test-engineering` | Backend và matching tests |
| `ai-dev` | `workspace-write` | `$sk-ai-engineering`, `$sk-test-engineering` | AI integration và matching tests |
| `reviewer` | `read-only` | `$sk-quality-check`; `$sk-release-check` khi được yêu cầu | Independent verification |

`workspace-write` chỉ là sandbox kỹ thuật. Allowed paths và product authority
vẫn do `AGENTS.md`, approved plan và task handoff giới hạn. Reviewer phải dùng
`sandbox_mode = "read-only"`.

`.codex/config.toml` bật agent và đặt concurrency cap. Subagent kế thừa permission
mode của parent turn; do đó sandbox/approval của session không được xem là một
HITL decision về product scope.

Cấu hình hiện tại:

```toml
[agents]
enabled = true
max_concurrent_threads_per_session = 4
```

## 6. Mapping workflow → agent → skill

| Workflow skill | Custom agent | Capability skill | Điều kiện |
|---|---|---|---|
| `$wf-discover` | `architect` | `$sk-solution-design` | Luôn dùng |
| `$wf-implement` | `backend-dev` | `$sk-backend-engineering`, `$sk-test-engineering` | Khi có backend scope |
| `$wf-implement` | `ai-dev` | `$sk-ai-engineering`, `$sk-test-engineering` | Khi có AI scope |
| `$wf-verify` | `reviewer` | `$sk-quality-check` | Luôn dùng |
| `$wf-verify` | `reviewer` | `$sk-release-check` | Chỉ khi `release_required=true` |

Codex main thread là coordinator. Workflow skill yêu cầu delegation; custom
agent thực hiện task và trả kết quả cho parent. Không tạo một coordinator agent
riêng khi main thread đã giữ vai trò đó.

## 7. Workflow `$wf-discover`

Mục đích: biến yêu cầu mới hoặc chưa rõ thành solution package đủ để con người
duyệt.

1. Main thread đọc repository authority cần thiết.
2. Delegate đúng một task cho `architect`.
3. `architect` dùng `$sk-solution-design` để tạo requirements, acceptance criteria,
   affected areas, options, decisions, plan, risks và unknowns.
4. Main thread kiểm tra schema và authority.
5. Null, interrupted, failed hoặc malformed result trở thành `blocked`.
6. Xuất `discovery-handoff/v1`.
7. Dừng tại H1; không nối thẳng sang implementation trong cùng turn.

H1 choices: `approve`, `approve-with-conditions`, `revise`, `reject`.

## 8. Workflow `$wf-implement`

Preconditions:

- có H1 approval còn hiệu lực cho scope và revision;
- requirements và decisions đã được approve;
- allowed paths và required checks rõ;
- external effect mặc định chưa được phép.

Quy trình:

1. Kiểm tra H1 và base revision.
2. Chia plan thành bounded work packages.
3. Gán đúng một owner cho mỗi mutable surface.
4. Route backend package cho `backend-dev`; route AI package cho `ai-dev`.
5. Mỗi agent dùng capability skill và `$sk-test-engineering` tương ứng.
6. Chạy focused checks và required repository checks.
7. Tổng hợp `implementation-handoff/v1`.

Không bắt buộc gọi cả hai agents. Chỉ chạy song song khi contract đã rõ,
allowed paths không chồng lấn, không sửa shared file, và có integration owner.
Nếu cùng sửa contract, workflow state hoặc dependency chung thì chạy tuần tự.

H2 bắt buộc trước:

- destructive migration;
- production mutation;
- paid external call;
- public-contract change ngoài H1;
- security-boundary change;
- significant scope expansion;
- action khó rollback.

H2 chỉ có hiệu lực cho action, target, limit và rollback được ghi rõ. Null,
interrupted, failed hoặc malformed agent result không bao giờ được tính là pass.
Chỉ trả `ready-for-verification` khi tất cả package và required checks đã pass.

## 9. Workflow `$wf-verify`

Mục đích: kiểm tra độc lập một candidate cố định.

1. Xác nhận candidate revision, handoff, required checks và rubric.
2. Delegate đúng một task cho `reviewer`.
3. Reviewer dùng `$sk-quality-check`; chỉ dùng `$sk-release-check` khi
   `release_required=true`.
4. Reviewer chụp repository state trước/sau và không sửa candidate.
5. Null, interrupted, failed hoặc malformed result trở thành `blocked`.
6. Xuất `verification-handoff/v1` và dừng tại H3.

Nếu failed, tạo bounded fix task quay lại `$wf-implement`; candidate mới phải
được verify lại. Reviewer không sửa code trực tiếp.

H3 choices: `accept`, `accept-with-conditions`, `return-for-fix`, `release`,
`reject`. H3 luôn gắn với đúng candidate revision.

## 10. State ownership và handoff

- Codex conversation/session giữ runtime orchestration state.
- `.codex/agents/` giữ custom role configuration.
- `.agents/skills/` giữ workflow và capability procedure.
- `docs/` giữ product, architecture, decisions và plans.
- `artifacts/handoffs/` giữ durable handoff khi task yêu cầu.
- `artifacts/evidence/` giữ command/evaluation evidence.
- `.harness-core/` không giữ task hoặc workflow runtime state.

Schema chi tiết nằm ở `docs/workflows/handoff-contracts.md`. Không lưu
chain-of-thought, credential hoặc raw sensitive payload.

## 11. Cách dùng trong Codex

### Feature mới hoặc còn ambiguity

```text
$wf-discover phân tích yêu cầu <...> và chuẩn bị H1.
```

Sau khi người dùng approve H1:

```text
$wf-implement triển khai change <CHG-ID> theo approval <HITL-ID>.
```

Sau khi có candidate:

```text
$wf-verify kiểm tra candidate <revision>, release_required=false.
```

Trước release:

```text
$wf-verify kiểm tra candidate <revision>, release_required=true.
```

Task nhỏ có approved scope có thể gọi trực tiếp custom agent/capability skill;
không bắt buộc dùng cả lifecycle.

## 12. Validation checklist

### Naming và discovery

- [x] Có đúng 3 workflow skills `wf-*`.
- [x] Có đúng 6 capability skills tên mới `sk-*`.
- [x] Có đúng 4 custom agent TOML.
- [x] Directory skill khớp frontmatter `name`.
- [x] Mỗi skill có metadata `agents/openai.yaml` phù hợp.
- [x] Không còn runtime file `.claude/*` hoặc `CLAUDE.md`.
- [x] Không còn tên cũ trong operational files; tên cũ chỉ còn ở migration table.

### Boundaries

- [x] Capability dùng chung không hard-code stack/domain/provider cụ thể.
- [x] `architect` không sửa application code hoặc tự accept decision.
- [x] Implementation agent không mở rộng approved scope.
- [x] `reviewer` dùng `sandbox_mode = "read-only"`.

### Workflow và HITL

- [x] `$wf-discover` chỉ delegate `architect` và dừng H1; đã smoke-test fresh session.
- [x] `$wf-implement` yêu cầu H1 và route theo scope; thiếu H1 đã trả `blocked`.
- [x] H2 được định nghĩa trước high-risk action; full high-risk action chưa chạy.
- [x] `$wf-verify` chỉ delegate `reviewer` và dừng H3; thiếu candidate đã trả `blocked`.
- [x] `$sk-release-check` chỉ chạy khi được yêu cầu.
- [x] Null/failed agent result không trở thành pass.

Chạy static validator:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/validate-agent-harness.ps1
```

Chạy `quick_validate.py` cho cả chín project skills, sau đó mở fresh Codex
session để kiểm tra discovery, explicit invocation, routing, reviewer read-only,
H1/H2/H3 và null/failure behavior. Static checks không thay thế runtime proof.

### Kết quả đã quan sát

- `quick_validate.py`: 9/9 skills pass.
- `scripts/validate-agent-harness.ps1`: pass với 6 capability skills, 3
  workflow skills, 4 custom agents, naming, routing, boundaries, HITL và null
  safeguards.
- TOML/YAML parse: pass.
- Negative proof: validator từ chối agent dùng `$solution-design` cũ và chấp
  nhận lại sau khi khôi phục `$sk-solution-design`.
- Fresh Codex `0.154.0`: discovery nhận đủ sáu `sk-*`; sáu entrypoint không
  prefix không tồn tại.
- `$wf-discover`: delegate đúng một `architect`, trả
  `discovery-handoff/v1`, dừng H1.
- `$wf-implement` thiếu H1 và `$wf-verify` thiếu candidate/handoff đều trả
  `blocked`, không delegate và không ghi file.

Không có CI hoặc checked-in hook đang gọi validator; branch protection chưa
được xác minh. Đây là local validation evidence, không phải tuyên bố merge
blocking.

## 13. Nguồn chuẩn Codex

- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Subagents và project custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Long-running work](https://learn.chatgpt.com/docs/long-running-work)

Nếu format Codex thay đổi, cập nhật implementation theo tài liệu Codex hiện hành;
không port nguyên format của Claude chỉ vì có cùng khái niệm.
