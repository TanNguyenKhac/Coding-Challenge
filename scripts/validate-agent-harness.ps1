[CmdletBinding()]
param(
    [string]$Root
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Root)) {
    $scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
    $Root = Split-Path -Parent $scriptDirectory
}
$rootPath = [IO.Path]::GetFullPath($Root)
$failures = [Collections.Generic.List[string]]::new()

function Add-Failure([string]$Message) {
    $script:failures.Add($Message)
}

function Read-Text([string]$RelativePath) {
    $path = Join-Path $rootPath $RelativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Add-Failure "Missing required file '$RelativePath'. See harness-agentic-development-workflows-hitl-playbook-vi.md."
        return ''
    }
    return [IO.File]::ReadAllText($path)
}

function Get-FrontmatterField([string]$Content, [string]$Field) {
    $frontmatter = [regex]::Match(
        $Content,
        '\A---\r?\n(?<body>.*?)\r?\n---',
        [Text.RegularExpressions.RegexOptions]::Singleline
    )
    if (-not $frontmatter.Success) { return $null }
    $match = [regex]::Match(
        $frontmatter.Groups['body'].Value,
        "(?m)^$([regex]::Escape($Field)):\s*(?<value>.+?)\s*$"
    )
    if (-not $match.Success) { return $null }
    return $match.Groups['value'].Value.Trim().Trim('"').Trim("'")
}

function Assert-InvocationPolicy(
    [string]$SkillName,
    [bool]$ExpectedImplicit
) {
    $relative = ".agents/skills/$SkillName/agents/openai.yaml"
    $content = Read-Text $relative
    $expectedText = if ($ExpectedImplicit) { 'true' } else { 'false' }
    $pattern = "(?m)^\s*allow_implicit_invocation:\s*$expectedText\s*$"
    if ($content -notmatch $pattern) {
        Add-Failure "Skill '$SkillName' must set allow_implicit_invocation: $expectedText (wf-implement-v2-optimization-vi.md section 12/15). Update '$relative' to the accepted invocation policy."
    }
}

function Assert-ExactDirectories(
    [string]$RelativeRoot,
    [string[]]$Expected,
    [string]$Kind
) {
    $path = Join-Path $rootPath $RelativeRoot
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        Add-Failure "Missing $Kind directory '$RelativeRoot'."
        return
    }
    $actual = @(
        Get-ChildItem -LiteralPath $path -Directory |
            ForEach-Object Name |
            Sort-Object
    )
    $expectedSorted = @($Expected | Sort-Object)
    if (($actual -join '|') -ne ($expectedSorted -join '|')) {
        Add-Failure "Unexpected $Kind directories under '$RelativeRoot'. Expected [$($expectedSorted -join ', ')], found [$($actual -join ', ')]."
    }
}

$capabilitySkills = @(
    'git-add-commit',
    'sk-solution-design',
    'sk-backend-engineering',
    'sk-ai-engineering',
    'sk-test-engineering',
    'sk-quality-check',
    'sk-release-check'
)
$workflowSkills = @('wf-discover', 'wf-implement', 'wf-verify')
$projectSkills = $capabilitySkills + $workflowSkills
$coreSkills = @(
    'onboard-repository',
    'audit-onboarding-proposal',
    'encode-invariant',
    'improve-harness'
)
$agents = @('architect', 'backend-dev', 'ai-dev', 'reviewer')

Assert-ExactDirectories '.agents/skills' ($projectSkills + $coreSkills) 'canonical skill'

foreach ($skillName in $projectSkills) {
    $relative = ".agents/skills/$skillName/SKILL.md"
    $content = Read-Text $relative
    $name = Get-FrontmatterField $content 'name'
    $description = Get-FrontmatterField $content 'description'
    if ($name -ne $skillName) {
        Add-Failure "Skill directory '$skillName' does not match frontmatter name '$name'."
    }
    if ([string]::IsNullOrWhiteSpace($description) -or $description -match '\[TODO') {
        Add-Failure "Skill '$skillName' has no final trigger description."
    }

    $metadata = Read-Text ".agents/skills/$skillName/agents/openai.yaml"
    $promptPattern = '(?m)^\s*default_prompt:\s*.+\$' +
        [regex]::Escape($skillName) + '\b'
    if ($metadata -notmatch $promptPattern) {
        Add-Failure "Skill '$skillName' metadata must contain a default prompt that mentions `$$skillName."
    }

    $referenceMatches = [regex]::Matches($content, '`(?<path>(?:\.\./)*[^`]+\.md)`')
    foreach ($referenceMatch in $referenceMatches) {
        $reference = $referenceMatch.Groups['path'].Value
        if ($reference -match '^(AGENTS\.md|docs/WORKFLOW\.md)$') { continue }
        $skillDirectory = Join-Path $rootPath ".agents/skills/$skillName"
        $referencePath = [IO.Path]::GetFullPath((Join-Path $skillDirectory $reference))
        if (-not (Test-Path -LiteralPath $referencePath -PathType Leaf)) {
            Add-Failure "Skill '$skillName' routes to missing reference '$reference'."
        }
    }
}

Assert-InvocationPolicy 'wf-implement' $false
foreach ($skillName in @(
    'sk-backend-engineering',
    'sk-ai-engineering',
    'sk-test-engineering'
)) {
    Assert-InvocationPolicy $skillName $true
}

$requiredV2References = @(
    '.agents/skills/wf-implement/references/task-contract.md',
    '.agents/skills/wf-implement/references/execution-and-resume.md',
    '.agents/skills/wf-implement/references/parallel-safety.md',
    '.agents/skills/sk-backend-engineering/references/state-and-recovery.md',
    '.agents/skills/sk-backend-engineering/references/data-change.md',
    '.agents/skills/sk-ai-engineering/references/provider-and-cost.md',
    '.agents/skills/sk-ai-engineering/references/structured-output-and-evaluation.md',
    '.agents/skills/sk-test-engineering/references/test-modes.md'
)
foreach ($relative in $requiredV2References) {
    if (-not (Test-Path -LiteralPath (Join-Path $rootPath $relative) -PathType Leaf)) {
        Add-Failure "Missing v2 procedure '$relative' required by wf-implement-v2-optimization-vi.md section 13. Add the focused reference and route to it from its skill entrypoint."
    }
}

$contracts = Read-Text 'docs/workflows/handoff-contracts.md'
$requiredSchemas = @(
    'work-package/v2',
    'agent-task-result/v2',
    'implementation-preflight/v1',
    'implementation-progress/v2',
    'candidate-manifest/v1',
    'implementation-handoff/v2'
)
$schemaSectionPatterns = @{
    'work-package/v2' = '(?s)## Implementation work package v2.*?```yaml\s*schema:\s*work-package/v2\b'
    'agent-task-result/v2' = '(?s)## Agent task result v2.*?```yaml\s*schema:\s*agent-task-result/v2\b'
    'implementation-preflight/v1' = '(?s)## Implementation progress v2.*?```yaml\s*schema:\s*implementation-preflight/v1\b'
    'implementation-progress/v2' = '(?s)## Implementation progress v2.*?```json\s*\{\s*"schema":\s*"implementation-progress/v2"'
    'candidate-manifest/v1' = '(?s)## Candidate identity.*?```yaml\s*schema:\s*candidate-manifest/v1\b'
    'implementation-handoff/v2' = '(?s)## Implementation handoff v2.*?```yaml\s*schema:\s*implementation-handoff/v2\b'
}
foreach ($schema in $requiredSchemas) {
    if ($contracts -notmatch $schemaSectionPatterns[$schema]) {
        Add-Failure "Canonical contract identifier '$schema' is missing from its owned section in 'docs/workflows/handoff-contracts.md' (wf-implement-v2-optimization-vi.md sections 6-13). Restore the schema identifier there; this static check does not validate instance structure."
    }
}
foreach ($candidateType in @('git-commit', 'content-manifest')) {
    if ($contracts -notmatch "\b$([regex]::Escape($candidateType))\b") {
        Add-Failure "Candidate identity type '$candidateType' is undocumented (wf-implement-v2-optimization-vi.md section 9). Restore the accepted candidate form in 'docs/workflows/handoff-contracts.md'."
    }
}
$h2Section = [regex]::Match(
    $contracts,
    '(?s)An H2 record.*?```yaml\s*(?<body>.*?)```'
)
if (-not $h2Section.Success) {
    Add-Failure "Cannot locate the canonical H2 approval record in 'docs/workflows/handoff-contracts.md'. Restore the action-scoped record required by wf-implement-v2-optimization-vi.md section 6 Phase G."
}
foreach ($field in @(
    'gate', 'change_id', 'implementation_run_id', 'action', 'target', 'limits',
    'rollback', 'idempotency_key', 'expires_at', 'decision'
)) {
    $fieldPattern = '(?m)^\s*' + [regex]::Escape($field) + '\s*:'
    if ($h2Section.Success -and
        $h2Section.Groups['body'].Value -notmatch $fieldPattern) {
        Add-Failure "The canonical H2 record is missing '$field' (wf-implement-v2-optimization-vi.md section 6 Phase G). Add the action-scoped field to 'docs/workflows/handoff-contracts.md'."
    }
}

$implementRoot = Join-Path $rootPath '.agents/skills/wf-implement'
$implementText = ''
if (Test-Path -LiteralPath $implementRoot -PathType Container) {
    $implementText = @(
        Get-ChildItem -LiteralPath $implementRoot -File -Recurse |
            ForEach-Object { [IO.File]::ReadAllText($_.FullName) }
    ) -join "`n"
}
foreach ($mode in @('apply', 'resume', 'fix')) {
    if ($implementText -notmatch "\b$mode\b") {
        Add-Failure "wf-implement is missing '$mode' mode (wf-implement-v2-optimization-vi.md section 4). Document the mode and its required inputs under '.agents/skills/wf-implement/'."
    }
}
foreach ($schema in $requiredSchemas) {
    if ($implementText -notmatch [regex]::Escape($schema)) {
        Add-Failure "wf-implement does not consume '$schema' (wf-implement-v2-optimization-vi.md sections 6-9). Reference the canonical contract from its entrypoint or procedure files."
    }
}
if ($implementText -match '\$sk-quality-check\b|\$sk-release-check\b' -or
    $implementText -match '(?im)^\s*\d+\..*\b(delegate|dispatch|invoke)\b.*\breviewer\b') {
    Add-Failure "wf-implement routes to verification ownership (wf-implement-v2-optimization-vi.md sections 3/15). Remove reviewer and quality/release skill dispatch; hand the fixed candidate to wf-verify."
}
if ($implementText -notmatch 'Never call `reviewer`') {
    Add-Failure "wf-implement must explicitly forbid calling reviewer (wf-implement-v2-optimization-vi.md section 10). Restore the WF2/WF3 separation safeguard in its entrypoint."
}
if ($implementText -notmatch 'fork_turns:\s*"none"') {
    Add-Failure 'wf-implement does not suppress inherited conversation history for bounded agent tasks (wf-implement-v2-optimization-vi.md sections 1/6 Phase D). Use fork_turns: "none" or an equivalent no-history spawn and supply only the task brief.'
}

$corePath = Join-Path $rootPath '.harness-core'
if (Test-Path -LiteralPath $corePath -PathType Container) {
    $runtimeState = @(
        Get-ChildItem -LiteralPath $corePath -File -Recurse |
            Where-Object {
                $_.Name -match '^(progress|implementation-handoff|agent-task-result|work-package).*\.(json|ya?ml)$' -or
                $_.FullName.Substring($corePath.Length).TrimStart('\', '/') -match '(^|[\\/])artifacts[\\/](handoffs|evidence)([\\/]|$)'
            }
    )
    foreach ($file in $runtimeState) {
        $relative = $file.FullName.Substring($rootPath.Length).TrimStart('\', '/')
        Add-Failure "Runtime state '$relative' is inside managed Harness core (wf-implement-v2-optimization-vi.md sections 2/8/15). Move the run artifact to 'artifacts/handoffs/' or 'artifacts/evidence/'."
    }
}

$genericBoundaries = @(
    @{
        Skill = 'sk-backend-engineering'
        Pattern = '(?i)\b(FastAPI|SQLAlchemy|Celery|RabbitMQ|LangGraph)\b'
        Rule = 'sk-backend-engineering must remain framework-neutral'
    },
    @{
        Skill = 'sk-ai-engineering'
        Pattern = '(?i)\b(video|audio|TTS|text-to-speech|chemistry|Gemini|Anthropic)\b'
        Rule = 'sk-ai-engineering must keep domain and specific-provider procedures in references'
    },
    @{
        Skill = 'sk-quality-check'
        Pattern = '(?i)\b(chemistry|video|audio|media)\b'
        Rule = 'sk-quality-check must receive domain rubrics from the task or repository'
    }
)
foreach ($boundary in $genericBoundaries) {
    $relative = ".agents/skills/$($boundary.Skill)/SKILL.md"
    $content = Read-Text $relative
    if ($content -match $boundary.Pattern) {
        Add-Failure "$($boundary.Rule): '$relative' contains '$($Matches[0])'."
    }
}

$claudeFiles = @()
$claudePath = Join-Path $rootPath '.claude'
if (Test-Path -LiteralPath $claudePath -PathType Container) {
    $claudeFiles = @(Get-ChildItem -LiteralPath $claudePath -File -Recurse)
}
if ($claudeFiles.Count -gt 0 -or (Test-Path -LiteralPath (Join-Path $rootPath 'CLAUDE.md'))) {
    Add-Failure 'Claude runtime definitions are not part of this Codex harness; remove .claude files and CLAUDE.md.'
}

$config = Read-Text '.codex/config.toml'
if ($config -notmatch '(?m)^\[agents\]\s*$' -or
    $config -notmatch '(?m)^enabled\s*=\s*true\s*$' -or
    $config -notmatch '(?m)^max_concurrent_threads_per_session\s*=\s*[1-9][0-9]*\s*$') {
    Add-Failure "'.codex/config.toml' must enable agents and set a positive concurrency cap."
}

$agentRoot = Join-Path $rootPath '.codex/agents'
if (-not (Test-Path -LiteralPath $agentRoot -PathType Container)) {
    Add-Failure "Missing Codex custom agent directory '.codex/agents'."
} else {
    $actualAgents = @(
        Get-ChildItem -LiteralPath $agentRoot -File -Filter '*.toml' |
            ForEach-Object BaseName |
            Sort-Object
    )
    $expectedAgents = @($agents | Sort-Object)
    if (($actualAgents -join '|') -ne ($expectedAgents -join '|')) {
        Add-Failure "Expected Codex agents [$($expectedAgents -join ', ')], found [$($actualAgents -join ', ')]."
    }
}

$agentExpectations = @{
    'architect' = @('sk-solution-design')
    'backend-dev' = @('sk-backend-engineering', 'sk-test-engineering')
    'ai-dev' = @('sk-ai-engineering', 'sk-test-engineering')
    'reviewer' = @('sk-quality-check', 'sk-release-check')
}
foreach ($agentName in $agents) {
    $relative = ".codex/agents/$agentName.toml"
    $content = Read-Text $relative
    $namePattern = '(?m)^name\s*=\s*["'']' +
        [regex]::Escape($agentName) + '["'']\s*$'
    if ($content -notmatch $namePattern) {
        Add-Failure "Codex agent '$agentName' has a mismatched name."
    }
    foreach ($skillName in $agentExpectations[$agentName]) {
        $skillPattern = '\$' + [regex]::Escape($skillName) + '\b'
        if ($content -notmatch $skillPattern) {
            Add-Failure "Codex agent '$agentName' does not require skill '$skillName'."
        }
    }
}

foreach ($agentName in @('backend-dev', 'ai-dev')) {
    $relative = ".codex/agents/$agentName.toml"
    $content = Read-Text $relative
    foreach ($pattern in @(
        '(?i)exactly one supplied work-package/v2',
        '(?i)modify only allowed paths',
        '\bagent-task-result/v2\b'
    )) {
        if ($content -notmatch $pattern) {
            Add-Failure "Implementation agent '$agentName' is missing its bounded v2 task/result guard matching '$pattern' (wf-implement-v2-optimization-vi.md section 11). Update '$relative' without expanding the role."
        }
    }
}

$reviewer = Read-Text '.codex/agents/reviewer.toml'
if ($reviewer -notmatch '(?m)^sandbox_mode\s*=\s*["'']read-only["'']\s*$') {
    Add-Failure "Reviewer must set sandbox_mode = 'read-only'."
}
foreach ($writer in @('architect', 'backend-dev', 'ai-dev')) {
    $content = Read-Text ".codex/agents/$writer.toml"
    if ($content -notmatch '(?m)^sandbox_mode\s*=\s*["'']workspace-write["'']\s*$') {
        Add-Failure "Agent '$writer' must use workspace-write; finer write boundaries remain in instructions."
    }
}

$workflowRules = @{
    'wf-discover' = @(
        '\barchitect\b', '\$sk-solution-design\b', '\bH1\b',
        '(?is)(missing|failed|malformed)[\s\S]{0,160}(blocked|failure)'
    )
    'wf-implement' = @(
        '\bbackend-dev\b', '\bai-dev\b', '\$sk-backend-engineering\b',
        '\$sk-ai-engineering\b', '\$sk-test-engineering\b', '\bH1\b', '\bH2\b',
        '(?is)(missing|interrupted|failed|malformed|null)[\s\S]{0,180}(never|not)[\s\S]{0,40}(success|done|pass)'
    )
    'wf-verify' = @(
        '\breviewer\b', '\$sk-quality-check\b', '\$sk-release-check\b', '\bH3\b',
        'release_required=true',
        '(?is)(missing|failed|malformed|null)[\s\S]{0,160}(blocked|passed)'
    )
}
foreach ($workflowName in $workflowSkills) {
    $relative = ".agents/skills/$workflowName/SKILL.md"
    $content = Read-Text $relative
    foreach ($pattern in $workflowRules[$workflowName]) {
        if ($content -notmatch $pattern) {
            Add-Failure "Workflow skill '$workflowName' is missing required safeguard matching '$pattern'."
        }
    }
}

$discover = Read-Text '.agents/skills/wf-discover/SKILL.md'
if ($discover -match '\b(backend-dev|ai-dev|reviewer)\b') {
    Add-Failure 'wf-discover may delegate only to architect.'
}
$verify = Read-Text '.agents/skills/wf-verify/SKILL.md'
if ($verify -match '\b(architect|backend-dev|ai-dev)\b') {
    Add-Failure 'wf-verify may delegate only to reviewer.'
}

$legacyNames = @(
    'solution-design',
    'backend-engineering',
    'ai-engineering',
    'test-engineering',
    'quality-check',
    'release-check',
    'solution-discovery',
    'backend-workflow-engineering',
    'ai-video-generation',
    'verification-and-evaluation',
    'release-assurance',
    'solution-architect',
    'backend-engineer',
    'ai-video-engineer',
    'quality-reviewer',
    'solution-discovery-and-approval',
    'approved-change-implementation',
    'verification-and-release-gate'
)
$operationalFiles = @(
    Get-ChildItem -LiteralPath (Join-Path $rootPath '.agents') -File -Recurse
    Get-ChildItem -LiteralPath (Join-Path $rootPath '.codex') -File -Recurse
    Get-Item -LiteralPath (Join-Path $rootPath 'AGENTS.md')
    Get-Item -LiteralPath (Join-Path $rootPath 'docs/WORKFLOW.md')
    Get-Item -LiteralPath (Join-Path $rootPath 'docs/workflows/handoff-contracts.md')
)
foreach ($file in $operationalFiles) {
    $content = [IO.File]::ReadAllText($file.FullName)
    foreach ($legacyName in $legacyNames) {
        $pattern = "(?<![a-z0-9-])$([regex]::Escape($legacyName))(?![a-z0-9-])"
        if ($content -match $pattern) {
            $relative = $file.FullName.Substring($rootPath.Length).TrimStart('\', '/')
            Add-Failure "Legacy name '$legacyName' remains in operational file '$relative'."
        }
    }
}

if ($failures.Count -gt 0) {
    Write-Error ("Codex agent harness validation failed:`n- " + ($failures -join "`n- "))
    exit 1
}

Write-Output 'Codex agent harness validation passed.'
Write-Output 'Validated: 6 capability skills, 3 workflow skills, 4 custom agents, WF2 v2 contract identifiers/modes, bounded task routing, invocation policy, HITL separation, generic boundaries, and null-result safeguards.'
