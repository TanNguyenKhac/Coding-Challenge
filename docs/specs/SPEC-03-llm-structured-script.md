# Functional Specification: SPEC-03 — LLM Factory & Structured Script Generation

- **Module**: `app.llm_factory`, `app.schemas.script`, `app.pipeline.nodes.script_node`, `app.pipeline.nodes.validator_node`
- **Scope**: LLM provider selection factory, Pydantic structured output protocol (zero regex), Script generation node, Business validation node, Retry loop routing.
- **Related Plan**: CHG-002 (WP-01, WP-03, WP-04)
- **Status**: Approved for Implementation

---

## 1. Business Context & Objective

Để tạo ra một video giải thích hóa học chất lượng, kịch bản phải được chia thành các phân đoạn (scenes/chunks) sư phạm mạch lạc (mở đầu, bản chất phân tử/phản ứng, tổng kết).

**Yêu cầu kỹ thuật then chốt:**
1. **100% Structured Output (Tuyệt đối không dùng Regex)**: Sử dụng cơ chế native schema binding của LangChain (`with_structured_output(VideoScript)`) để ép model trả về dữ liệu đúng schema Pydantic, loại bỏ hoàn toàn các lỗi format JSON, markdown code fence hay regex parsing gãy vỡ.
2. **Provider Swapping Linh hoạt**: Hỗ trợ chạy local với Codex (OpenAI-compatible endpoint không mất phí), fallback sang Claude Haiku (Anthropic API), hoặc FakeListChatModel trong Unit Tests.
3. **Reliability under Non-determinism**: Nếu kịch bản không đạt tiêu chí sư phạm (dưới 3 phân đoạn, trường rỗng), `validator_node` sẽ kích hoạt luồng Retry tự động (tối đa 2 lần).

---

## 2. LLM Provider Factory Specification (`app/llm_factory.py`)

Hàm `build_llm()` chịu trách nhiệm tạo instance `BaseChatModel` tương ứng dựa trên cấu hình môi trường:

```python
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from app.config import settings

def build_llm(override_llm: BaseChatModel | None = None) -> BaseChatModel:
    """
    Khởi tạo Chat Model theo thứ tự ưu tiên:
    1. override_llm (nếu được truyền vào từ test fixture)
    2. Codex (OpenAI-compatible) khi CODEX_API_BASE được cấu hình
    3. Anthropic (Claude Haiku) khi ANTHROPIC_API_KEY được cấu hình
    4. Ném RuntimeError nếu không có provider nào khả dụng
    """
    if override_llm is not None:
        return override_llm

    if settings.codex_api_base:
        return ChatOpenAI(
            base_url=settings.codex_api_base,
            model=settings.codex_model or "codex-mini-latest",
            api_key=settings.codex_api_key or "not-needed",
            temperature=0,
        )

    if settings.anthropic_api_key:
        return ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=settings.anthropic_api_key,
            temperature=0,
        )

    raise RuntimeError(
        "Không tìm thấy cấu hình LLM provider. Vui lòng thiết lập biến môi trường "
        "CODEX_API_BASE (ưu tiên) hoặc ANTHROPIC_API_KEY."
    )
```

---

## 3. Structured Output Schemas (`app/schemas/script.py`)

```python
from typing import Optional
from pydantic import BaseModel, Field

class ScriptChunk(BaseModel):
    chunk_id: int = Field(description="Số thứ tự phân đoạn (0, 1, 2...)")
    heading: str = Field(min_length=2, description="Tiêu đề trực quan hiển thị trên slide của phân đoạn")
    narration: str = Field(min_length=10, description="Lời thuyết minh chi tiết cho giọng đọc TTS")
    visual_notes: str = Field(min_length=5, description="Mô tả công thức hóa học, biểu tượng hoặc cấu trúc phân tử cần vẽ")
    duration_hint_sec: Optional[int] = Field(default=None, description="Thời lượng gợi ý (giây)")

class VideoScript(BaseModel):
    title: str = Field(min_length=3, description="Tiêu đề chính của bài giảng hóa học")
    summary: str = Field(min_length=10, description="Tóm tắt 1-2 câu nội dung cốt lõi của bài học")
    chunks: list[ScriptChunk] = Field(min_length=3, description="Danh sách tối thiểu 3 phân đoạn bài học")
```

---

## 4. LangGraph Nodes Specification

### 4.1 Script Generation Node (`app/pipeline/nodes/script_node.py`)

```python
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from app.pipeline.state import VideoGenerationState
from app.schemas.script import VideoScript

logger = logging.getLogger(__name__)

CHEMISTRY_SYSTEM_PROMPT = """You are an expert chemistry educator creating structured, high-impact video scripts for students.
Your explanation must be clear, accurate, engaging, and visually descriptive.
Always return structured data matching the VideoScript schema with at least 3 distinct pedagogical chunks:
1. Introduction & Hook: Real-world chemistry context and core question.
2. Molecular / Concept Mechanism: How molecules, electrons, bonds, or reactions work at the molecular level.
3. Summary & Takeaway: Key principle and practical application.
"""

async def script_node(state: VideoGenerationState, llm: BaseChatModel) -> dict:
    """
    Sinh kịch bản bằng Cơ chế Structured Output (Pydantic schema).
    KHÔNG dùng bất kỳ regex hay parse chuỗi thủ công nào.
    """
    logger.info(f"Generating script for concept: {state['concept']} (retry: {state.get('retry_count', 0)})")

    structured_llm = llm.with_structured_output(VideoScript)

    config = state.get("config")
    duration_target = config.target_duration_sec if config else 60
    audience = config.target_audience if config else "high_school"
    lang = config.language if config else "vi"

    user_prompt = (
        f"Explain the following chemistry concept:\n{state['concept']}\n\n"
        f"Parameters:\n"
        f"- Target duration: ~{duration_target} seconds\n"
        f"- Target audience: {audience}\n"
        f"- Language: {lang}\n"
        f"Break down into at least 3 cohesive, clear visual scenes."
    )

    try:
        script_output: VideoScript = await structured_llm.ainvoke([
            SystemMessage(content=CHEMISTRY_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        return {"script": script_output}
    except Exception as exc:
        logger.warning(f"Structured output invocation error: {exc}")
        return {"script": None, "error_reason": f"LLM Generation Error: {str(exc)}"}
```

---

### 4.2 Validator Node & Routing Logic (`app/pipeline/nodes/validator_node.py`)

```python
import logging
from typing import Literal
from app.pipeline.state import VideoGenerationState
from app.config import settings

logger = logging.getLogger(__name__)

def validate_script_node(state: VideoGenerationState) -> dict:
    """
    Kiểm tra tính toàn vẹn nghiệp vụ của kịch bản đã sinh:
    - script có tồn tại không
    - len(chunks) >= 3
    - tiêu đề và các trường không bị rỗng
    """
    script = state.get("script")
    if not script:
        return {
            "error_reason": state.get("error_reason") or "No script generated by LLM",
            "retry_count": state.get("retry_count", 0) + 1
        }

    # Business validation checks:
    if len(script.chunks) < 3:
        return {
            "error_reason": f"Script has only {len(script.chunks)} chunks; required minimum is 3",
            "retry_count": state.get("retry_count", 0) + 1
        }

    for i, chunk in enumerate(script.chunks):
        if not chunk.heading.strip() or not chunk.narration.strip():
            return {
                "error_reason": f"Chunk {i} has empty heading or narration",
                "retry_count": state.get("retry_count", 0) + 1
            }

    # Passed validation
    return {"error_reason": None}

def script_router(state: VideoGenerationState) -> Literal["pass", "retry", "failed"]:
    """
    Conditional edge router sau khi validate:
    - pass -> chuyển sang generate_audio
    - retry -> quay lại generate_script nếu retry_count <= MAX_RETRIES
    - failed -> kết thúc tiến trình thất bại
    """
    if state.get("error_reason") is None and state.get("script") is not None:
        return "pass"

    if state.get("retry_count", 0) <= settings.max_retries:
        logger.info(f"Script validation failed. Retrying... ({state['retry_count']}/{settings.max_retries})")
        return "retry"

    logger.error(f"Script validation failed and exceeded max retries. Failing job.")
    return "failed"
```

---

## 5. StateGraph Integration Blueprint

```python
# app/pipeline/graph.py
graph = StateGraph(VideoGenerationState)

graph.add_node("generate_script", partial(script_node, llm=llm))
graph.add_node("validate_script", validate_script_node)
graph.add_node("mark_failed", mark_failed_node)

graph.add_edge(START, "generate_script")
graph.add_edge("generate_script", "validate_script")

graph.add_conditional_edges(
    "validate_script",
    script_router,
    {
        "pass": "generate_audio",
        "retry": "generate_script",
        "failed": "mark_failed"
    }
)
```

---

## 6. Definition of Done (DoD)

1. [x] `build_llm()` trả về đúng provider theo cấu hình môi trường; ném ngoại lệ rõ ràng khi thiếu cấu hình.
2. [x] 100% sử dụng LangChain Structured Output với `VideoScript` Pydantic model (không có bất kỳ dòng lệnh regex parse nào).
3. [x] Kịch bản sinh ra luôn có tối thiểu 3 chunks với đầy đủ `heading`, `narration`, `visual_notes`.
4. [x] Nếu kịch bản không đạt, hệ thống tự động retry tối đa `settings.max_retries` (mặc định = 2).
5. [x] Khi vượt quá số lần retry, job chuyển sang nhánh `mark_failed` với `error_reason` tường minh.

---

## 7. Verification Checklist & Unit Test Matrix

| ID | Test Case | Kịch bản kiểm thử | Kết quả mong đợi |
|---|---|---|---|
| TC-03-01 | Build LLM Codex Provider | Set `CODEX_API_BASE=http://localhost:11434/v1` | `build_llm()` trả về instance `ChatOpenAI` |
| TC-03-02 | Build LLM Anthropic Provider | Set `ANTHROPIC_API_KEY=sk-ant-test` (không có base URL) | `build_llm()` trả về instance `ChatAnthropic` |
| TC-03-03 | Build LLM No Provider Configured | Không set cả 2 biến môi trường | `build_llm()` ném `RuntimeError` |
| TC-03-04 | Structured Output Thành công | Gọi `script_node` với Mock LLM trả về `VideoScript` hợp lệ | State chứa `script: VideoScript` với đầy đủ 3 chunks |
| TC-03-05 | Validator Pass | Chạy `validate_script_node` với script có 3 chunks hợp lệ | `error_reason == None`, router trả về `"pass"` |
| TC-03-06 | Validator Retry khi ít hơn 3 chunks | Script có 2 chunks, `retry_count == 0` | Router trả về `"retry"`, `retry_count == 1` |
| TC-03-07 | Validator Failed khi vượt max retry | Script lỗi, `retry_count == 2` | Router trả về `"failed"`, kết thúc tại `mark_failed` |
