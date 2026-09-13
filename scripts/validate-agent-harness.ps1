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
        '(?is)(missing|failed|malformed|null)[\s\S]{0,160}(blocked|failed|success)'
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
Write-Output 'Validated: 6 capability skills, 3 workflow skills, 4 custom agents, generic boundaries, HITL routing, and null-result safeguards.'
