import asyncio

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.schemas.job import VideoConfig
from app.schemas.script import ScriptChunk, VideoScript


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_config() -> dict:
    return VideoConfig().model_dump()


@pytest.fixture
def valid_script() -> VideoScript:
    return VideoScript(
        title="Understanding the pH Scale",
        summary="This lesson explains how the pH scale describes acids and bases.",
        chunks=[
            ScriptChunk(
                chunk_id=0,
                heading="Introduction",
                narration="The pH scale describes whether a solution is acidic or basic.",
                visual_notes="A colored pH scale from zero to fourteen",
            ),
            ScriptChunk(
                chunk_id=1,
                heading="Mechanism",
                narration="The pH value relates to the concentration of hydrogen ions in solution.",
                visual_notes="The pH formula and hydrogen ions",
            ),
            ScriptChunk(
                chunk_id=2,
                heading="Summary",
                narration="Seven is neutral, lower values are acidic, and higher values are basic.",
                visual_notes="Everyday examples arranged on the pH scale",
            ),
        ],
    )


@pytest.fixture
def invalid_script_few_chunks() -> VideoScript:
    # Bypass schema construction deliberately to exercise validator defense in depth.
    return VideoScript.model_construct(
        title="Incomplete chemistry lesson",
        summary="This deliberately violates the approved three-scene business rule.",
        chunks=[
            ScriptChunk(
                chunk_id=0,
                heading="First scene",
                narration="This narration is long enough but the lesson has too few scenes.",
                visual_notes="A first chemistry illustration",
            ),
            ScriptChunk(
                chunk_id=1,
                heading="Second scene",
                narration="This narration is also valid but the scene count remains too low.",
                visual_notes="A second chemistry illustration",
            ),
        ],
    )


class _DeterministicStructuredRunnable:
    def __init__(self, responses: list[object]):
        self._responses = responses
        self.invocations: list[object] = []
        self.sync_invocation_attempts = 0

    async def ainvoke(self, messages):
        self.invocations.append(messages)
        await asyncio.sleep(0)
        index = min(len(self.invocations) - 1, len(self._responses) - 1)
        response = self._responses[index]
        if isinstance(response, Exception):
            raise response
        return response

    def invoke(self, messages):
        self.sync_invocation_attempts += 1
        raise AssertionError("Structured LLM must be invoked asynchronously")


class DeterministicStructuredLLM:
    def __init__(self, responses: list[object]):
        if not responses:
            raise ValueError("At least one deterministic response is required")
        self.structured = _DeterministicStructuredRunnable(responses)
        self.bound_schemas: list[type] = []

    def with_structured_output(self, schema):
        self.bound_schemas.append(schema)
        return self.structured

    @property
    def invocation_count(self) -> int:
        return len(self.structured.invocations)


def make_mock_structured_llm(responses: list[object]) -> DeterministicStructuredLLM:
    """Create a deterministic async fake for the structured-output boundary."""
    return DeterministicStructuredLLM(responses)
