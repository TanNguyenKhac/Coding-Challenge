# Harness Improvement: Giao tiếp bằng tiếng Việt

Date: 2026-09-13

## Status

Completed

## Representative Job

Agent làm việc trong repository này cần phản hồi người dùng và viết phần diễn
giải trong skill hoặc tài liệu mới hay được chỉnh sửa đáng kể. Kết quả được chấp
nhận là phần văn xuôi bằng tiếng Việt, trong khi code, identifier, command,
API/schema field và technical term đã được thiết lập vẫn bằng English.

Worker class cố định là repository-aware Codex agent tại revision
`2cf89b0e20c3d8bfd2e7ed884770fb24b4643c72`, branch `develop`, sử dụng
repository filesystem và shell tools. Không có external state. Yêu cầu của người
dùng trong session này là authority. Điều kiện dừng là instruction xung đột,
không được truy xuất hoặc validation không cung cấp đủ bằng chứng.

## Baseline

Trong tác vụ chào hỏi đại diện, agent đã trả lời prompt `hi` bằng tiếng Anh:
`Hi! What would you like to work on?`. Người dùng phải can thiệp và yêu cầu thêm
repository instruction để tiếng Việt trở thành mặc định cho phản hồi, skill và
tài liệu, đồng thời giữ technical term và code bằng English. Trước can thiệp
không có retry hoặc repository proof nào cho hành vi này.

Giới hạn đã biết: baseline trực tiếp chứng minh friction về ngôn ngữ phản hồi;
nó không chứng minh độc lập một skill hoặc tài liệu từng được viết sai ngôn ngữ.

## Earliest Gap

Context: canonical agent instructions của repository chưa quy định ngôn ngữ mặc
định cho giao tiếp với người dùng hoặc explanatory prose.

## Correct Owner

`repository-harness`, cụ thể là root `AGENTS.md`. Codex đọc trực tiếp file này;
`CLAUDE.md` hiện chỉ tham chiếu nó qua `@AGENTS.md` và không được chỉnh sửa trong
can thiệp.

## Intervention

Nếu một section ngắn về language default được thêm vào root `AGENTS.md`, một
fresh agent sẽ trả lời prompt chào hỏi tương đương bằng tiếng Việt và giữ phần
kỹ thuật bằng English, vì repository-aware agent tải file này làm canonical
instruction source.

Bằng chứng làm suy yếu giả thuyết là fresh agent không truy xuất section, trả
lời bằng tiếng Anh, dịch code/identifier, hoặc phát hiện requirement có authority
cao hơn bị xung đột.

Repository maintainers sở hữu instruction. Cần sửa hoặc loại bỏ nếu yêu cầu giao
tiếp của project thay đổi, instruction xung đột với artifact requirement, hoặc
fresh agents nhiều lần không truy xuất được nó.

## Native Validation

Structural inspection đạt cả bốn assertion:

- `AGENTS.md` có heading `## Language`;
- có default dùng Vietnamese cho user-facing responses;
- có yêu cầu giữ source code, code snippet, identifier và command bằng English;
- `CLAUDE.md` vẫn tham chiếu canonical `AGENTS.md` qua `@AGENTS.md`.

Lệnh native `scripts/validate-agent-harness.ps1` ban đầu bị Windows execution
policy chặn. Chạy lại cùng script bằng
`powershell -NoProfile -ExecutionPolicy Bypass -File` đã thực thi được nhưng
không đạt vì sáu reference bị thiếu và vì validator không chấp nhận
`CLAUDE.md`/`.claude`.

Cả sáu reference đã `missing-at-HEAD`, còn `CLAUDE.md` đã `present-at-HEAD` tại
revision ban đầu. Vì vậy các failure này là pre-existing và không do can thiệp
language instruction gây ra. Repository-wide native validation vẫn chưa xanh.

## Fresh Rerun

Fresh read-only agent `/root/fresh_language_rerun` chạy với cùng branch và
revision. Agent báo không tạo hoặc sửa file, và scoped candidate surfaces không
drift trong phép thử. Sau rerun, final workspace status xuất hiện thêm các
untracked path không liên quan (`.claude/worktrees/` và
`docs/plans/active/CHG-001-chemistry-video-mvp.md`); nguồn tạo không xác định,
chúng không overlap với intervention và được giữ nguyên. Agent báo:

- instruction available và được retrieved trực tiếp từ root `AGENTS.md`;
- instruction relevant với cả greeting và prompt giải thích `async def`;
- greeting được trả lời bằng tiếng Việt;
- explanatory prose được viết bằng tiếng Việt;
- `async def`, `coroutine function`, `await`, `I/O`, `event loop`, module,
  identifier và code Python được giữ bằng English.

Rerun đạt accepted outcome mà không cần human retry.

## Decision

Keep

Fresh agent đã truy xuất và thực thi đúng intervention trên representative job.
Chi phí bảo trì là một section ngắn trong canonical instruction owner.

## Result

Giữ language instruction trong `AGENTS.md`. Bounded outcome đã được chứng minh
bằng structural assertions và fresh-agent behavior. Giới hạn còn lại là native
harness validator đang fail vì các baseline inconsistency không thuộc phạm vi
thay đổi này, và validator chưa có mechanical check riêng cho language rule.
