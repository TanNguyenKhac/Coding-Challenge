---
name: git-add-commit
description: Dùng khi người dùng yêu cầu stage và commit thay đổi trong Git repository. Skill bảo vệ thay đổi ngoài phạm vi, dùng exact staged diff để tạo commit message bằng English, rồi xác minh commit; không dùng cho push, amend, reset, rebase hoặc thay đổi history.
---

# Git Add and Commit

Tạo một commit có phạm vi chính xác, message phản ánh đúng diff và không cuốn
theo thay đổi không liên quan.

## Authorization Boundary

- Chỉ chạy `git add` hoặc `git commit` khi yêu cầu hiện tại của người dùng nói
  rõ cần stage/commit. Việc skill được discover tự động không phải authorization
  để mutate Git state.
- Runtime sandbox vẫn kiểm soát quyền ghi `.git`. Nếu lệnh hợp lệ bị chặn, yêu
  cầu approval cho đúng lệnh cần chạy; không tuyên bố rằng skill file tự cấp
  permission.
- Project-local execpolicy tại `.codex/rules/git-add-commit.rules` cấp `allow`
  cho exact prefixes `git add --` và `git commit -m` khi project `.codex` layer
  được trusted và đã load. Dùng đúng command shape này; một rule có authority
  cao hơn vẫn có thể yêu cầu prompt hoặc forbid.
- Authorization chỉ bao gồm read-only inspection, `git add -- <exact-paths>` và
  `git commit` cho phạm vi đã duyệt. Không suy rộng sang `push`, `amend`,
  `reset`, `rebase`, `merge`, force operation, history rewrite, Git config,
  hook installation hoặc bỏ qua hook bằng `--no-verify`.

## Resolve The Commit Scope

1. Đọc applicable `AGENTS.md` và repository workflow. Xác nhận đang ở đúng Git
   worktree; kiểm tra branch, `HEAD`, `git status --short`, staged diff và
   unstaged diff. Dừng khi repository đang merge/rebase/cherry-pick hoặc có
   conflict chưa xử lý.
2. Nếu người dùng chỉ định path, dùng đúng path đó. Nếu không, chỉ chọn các path
   thuộc tác vụ hiện tại và do agent tạo hoặc sửa. Không stage thay đổi unrelated
   hoặc pre-existing chỉ vì chúng đang có trong working tree.
3. Nếu phạm vi, ownership hoặc intent không rõ, hỏi người dùng trước mutation.
   Nếu index đã chứa staged change ngoài phạm vi được duyệt, dừng và báo danh
   sách đó; không tự unstage hay commit chúng.
4. Kiểm tra `git diff -- <exact-paths>` và nội dung của untracked file trước khi
   stage. Không stage credential, private key, secret-bearing environment file,
   build output hoặc generated artifact ngoài repository policy.

## Stage And Derive The Message

1. Chạy `git add -- <exact-paths>` với danh sách file cụ thể. Không dùng
   `git add .`, `git add -A`, wildcard hoặc directory-wide pathspec trừ khi người
   dùng đã yêu cầu rõ toàn bộ phạm vi và tất cả file đã được review.
2. Sau khi stage, chạy `git diff --cached --check`,
   `git diff --cached --name-status`, `git diff --cached --stat` và đọc exact
   `git diff --cached`. Xác nhận staged path set khớp hoàn toàn với phạm vi được
   duyệt. Nếu diff rỗng hoặc sai phạm vi, không commit.
3. Dùng exact staged diff làm source of truth để tạo commit message. Có thể đọc
   recent commit subjects bằng `git log` để theo convention đã có; không biến
   convention quan sát được thành repository policy.
4. Viết subject bằng English, mô tả primary intent của diff ở imperative mood
   và giữ ngắn gọn, ưu tiên tối đa 72 characters. Chỉ thêm body khi cần giải
   thích motivation, behavior change hoặc non-obvious tradeoff. Không nhắc tới
   agent/tool và không liệt kê file thay cho intent.

## Commit And Verify

1. Chạy `git commit` với message đã suy ra. Không bỏ qua repository hooks. Nếu
   hook hoặc commit thất bại, giữ nguyên bằng chứng và báo lỗi; chỉ sửa nguyên
   nhân khi yêu cầu hiện tại đã cho phép thay đổi đó.
2. Xác minh bằng `git log -1 --oneline --decorate`,
   `git show --stat --oneline --summary HEAD` và `git status --short`.
3. Báo commit hash, exact subject, các path đã commit, validation/hook result và
   mọi staged hoặc unstaged change còn lại. Không claim `push` hoặc remote state.
