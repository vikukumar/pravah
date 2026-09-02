"""
PRAVAH Workflow Node Registry
================================
Metadata-driven catalog of all workflow nodes per PRD §13-14 and §104.

Every node in this registry MUST have a real execution handler before being
listed as `status: "active"`. Nodes with `status: "planned"` are visible in
the UI but rendered as unavailable/coming-soon.

Structure:
    NODE_REGISTRY: Dict[node_type -> NodeDefinition]

NodeDefinition exposes:
    id, name, category, description, icon, version, inputs, outputs,
    config_schema, permissions, plan_requirements, status
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeIOSpec:
    """Definition of a node input or output port."""
    name: str
    label: str
    data_type: str  # "any" | "text" | "json" | "boolean" | "number" | "array"
    required: bool = False
    description: str = ""


@dataclass
class ConfigField:
    """Definition of a single node configuration field."""
    key: str
    label: str
    field_type: str   # "text" | "textarea" | "select" | "number" | "boolean" | "secret_ref" | "json" | "expression"
    required: bool = False
    default: Any = None
    options: Optional[List[Dict[str, str]]] = None  # For select fields
    placeholder: str = ""
    description: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None


@dataclass
class NodeDefinition:
    """Full metadata definition for a workflow node."""
    id: str                         # Unique type identifier, e.g. "ai_generate_text"
    name: str                       # Display name
    category: str                   # "trigger" | "ai" | "social" | "logic" | "data" | "utility" | "time" | "content"
    description: str
    icon: str                       # Lucide icon name, e.g. "Bot", "Clock", "GitBranch"
    version: str = "1.0.0"
    inputs: List[NodeIOSpec] = field(default_factory=list)
    outputs: List[NodeIOSpec] = field(default_factory=list)
    config_schema: List[ConfigField] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)   # Required permissions
    plan_requirements: List[str] = field(default_factory=list)  # Required plan features
    status: str = "active"          # "active" | "planned" | "deprecated"
    color: str = "#6366f1"          # Node accent color for canvas rendering


# ---------------------------------------------------------------------------
# TRIGGER NODES
# ---------------------------------------------------------------------------

_TRIGGER_NODES: List[NodeDefinition] = [
    NodeDefinition(
        id="trigger_manual",
        name="Manual Trigger",
        category="trigger",
        description="Starts the workflow manually by user action or API call.",
        icon="Play",
        color="#10b981",
        inputs=[],
        outputs=[NodeIOSpec("output", "Output", "json")],
        config_schema=[
            ConfigField("label", "Trigger Label", "text", default="Run Now", placeholder="Run Now"),
        ],
    ),
    NodeDefinition(
        id="trigger_schedule",
        name="Schedule Trigger",
        category="trigger",
        description="Automatically triggers the workflow on a configurable schedule.",
        icon="Clock",
        color="#10b981",
        inputs=[],
        outputs=[NodeIOSpec("output", "Output", "json")],
        config_schema=[
            ConfigField("cron_expression", "Cron Expression", "text", required=True,
                        placeholder="0 9 * * 1-5", description="Standard 5-field cron expression (minute hour day month weekday)"),
            ConfigField("timezone", "Timezone", "text", default="UTC", placeholder="Asia/Kolkata"),
            ConfigField("max_runs", "Max Executions (0 = unlimited)", "number", default=0, min_value=0),
        ],
    ),
    NodeDefinition(
        id="trigger_webhook",
        name="Webhook Trigger",
        category="trigger",
        description="Triggers the workflow when a webhook request is received at the workflow-specific endpoint.",
        icon="Webhook",
        color="#10b981",
        inputs=[],
        outputs=[NodeIOSpec("output", "Webhook Payload", "json")],
        config_schema=[
            ConfigField("http_method", "Allowed Method", "select", default="POST",
                        options=[{"value": "POST", "label": "POST"}, {"value": "GET", "label": "GET"}]),
            ConfigField("require_auth", "Require Bearer Token", "boolean", default=True),
        ],
    ),
    NodeDefinition(
        id="trigger_content_created",
        name="Content Created",
        category="trigger",
        description="Triggers when a new content item is created in the organisation.",
        icon="FilePlus",
        color="#10b981",
        inputs=[],
        outputs=[NodeIOSpec("output", "Content Data", "json")],
        config_schema=[
            ConfigField("platform_filter", "Filter by Platform", "select", default="any",
                        options=[{"value": "any", "label": "Any Platform"},
                                 {"value": "x", "label": "X"}, {"value": "instagram", "label": "Instagram"},
                                 {"value": "linkedin", "label": "LinkedIn"}, {"value": "facebook", "label": "Facebook"}]),
        ],
    ),
    NodeDefinition(
        id="trigger_content_approved",
        name="Content Approved",
        category="trigger",
        description="Triggers when content receives an approval decision.",
        icon="CheckCircle",
        color="#10b981",
        inputs=[],
        outputs=[NodeIOSpec("output", "Approval Data", "json")],
        config_schema=[],
    ),
]

# ---------------------------------------------------------------------------
# AI NODES
# ---------------------------------------------------------------------------

_AI_NODES: List[NodeDefinition] = [
    NodeDefinition(
        id="ai_generate_text",
        name="Generate Text",
        category="ai",
        description="Generates AI-optimised social media text using the configured provider.",
        icon="Bot",
        color="#8b5cf6",
        inputs=[NodeIOSpec("input", "Context", "json")],
        outputs=[
            NodeIOSpec("text", "Generated Text", "text"),
            NodeIOSpec("hashtags", "Hashtags", "array"),
            NodeIOSpec("output", "Full Output", "json"),
        ],
        config_schema=[
            ConfigField("topic", "Topic / Brief", "textarea", required=True, placeholder="Weekly product highlights for SaaS customers"),
            ConfigField("platform", "Target Platform", "select", required=True, default="x",
                        options=[{"value": "x", "label": "X (Twitter)"}, {"value": "linkedin", "label": "LinkedIn"},
                                 {"value": "instagram", "label": "Instagram"}, {"value": "facebook", "label": "Facebook"}]),
            ConfigField("tone", "Tone", "select", default="professional",
                        options=[{"value": "professional", "label": "Professional"},
                                 {"value": "casual", "label": "Casual"}, {"value": "humorous", "label": "Humorous"},
                                 {"value": "educational", "label": "Educational"}, {"value": "inspirational", "label": "Inspirational"}]),
            ConfigField("content_type", "Content Type", "select", default="educational",
                        options=[{"value": "educational", "label": "Educational"},
                                 {"value": "promotional", "label": "Promotional"},
                                 {"value": "engagement", "label": "Engagement"},
                                 {"value": "announcement", "label": "Announcement"},
                                 {"value": "thought_leadership", "label": "Thought Leadership"}]),
            ConfigField("language", "Language", "text", default="English"),
            ConfigField("temperature", "Creativity (0-1)", "number", default=0.7, min_value=0.0, max_value=1.0),
            ConfigField("max_tokens", "Max Tokens", "number", default=600, min_value=50, max_value=4000),
            ConfigField("model_override", "Model Override (optional)", "text", placeholder="Leave blank to use platform default"),
            ConfigField("system_instructions", "Extra System Instructions", "textarea", placeholder="Additional brand guidelines..."),
        ],
        permissions=["content.create"],
    ),
    NodeDefinition(
        id="ai_rewrite",
        name="Rewrite / Refine",
        category="ai",
        description="Rewrites or refines existing text content for a different tone or platform.",
        icon="RefreshCw",
        color="#8b5cf6",
        inputs=[NodeIOSpec("text", "Input Text", "text", required=True)],
        outputs=[NodeIOSpec("text", "Rewritten Text", "text"), NodeIOSpec("output", "Full Output", "json")],
        config_schema=[
            ConfigField("instruction", "Rewrite Instruction", "textarea", required=True,
                        placeholder="Make this more concise and professional for LinkedIn"),
            ConfigField("platform", "Target Platform", "select", default="linkedin",
                        options=[{"value": "x", "label": "X"}, {"value": "linkedin", "label": "LinkedIn"},
                                 {"value": "instagram", "label": "Instagram"}, {"value": "facebook", "label": "Facebook"}]),
        ],
        permissions=["content.create"],
    ),
    NodeDefinition(
        id="ai_summarize",
        name="Summarize",
        category="ai",
        description="Summarizes long-form content into a concise version.",
        icon="AlignLeft",
        color="#8b5cf6",
        inputs=[NodeIOSpec("text", "Input Text", "text", required=True)],
        outputs=[NodeIOSpec("summary", "Summary", "text"), NodeIOSpec("output", "Full Output", "json")],
        config_schema=[
            ConfigField("max_sentences", "Max Sentences", "number", default=3, min_value=1, max_value=10),
        ],
        permissions=["content.create"],
    ),
    NodeDefinition(
        id="ai_generate_hashtags",
        name="Generate Hashtags",
        category="ai",
        description="Generates platform-appropriate hashtags for content.",
        icon="Hash",
        color="#8b5cf6",
        inputs=[NodeIOSpec("text", "Content Text", "text", required=True)],
        outputs=[NodeIOSpec("hashtags", "Hashtags Array", "array"), NodeIOSpec("hashtags_string", "Hashtags String", "text")],
        config_schema=[
            ConfigField("count", "Number of Hashtags", "number", default=10, min_value=3, max_value=30),
            ConfigField("platform", "Platform", "select", default="instagram",
                        options=[{"value": "x", "label": "X"}, {"value": "instagram", "label": "Instagram"},
                                 {"value": "linkedin", "label": "LinkedIn"}]),
        ],
        permissions=["content.create"],
    ),
    NodeDefinition(
        id="ai_generate_image_prompt",
        name="Generate Image Prompt",
        category="ai",
        description="Creates an optimised image generation prompt from content context.",
        icon="ImagePlus",
        color="#8b5cf6",
        inputs=[NodeIOSpec("text", "Content Text", "text")],
        outputs=[NodeIOSpec("prompt", "Image Prompt", "text")],
        config_schema=[
            ConfigField("style", "Visual Style", "select", default="photorealistic",
                        options=[{"value": "photorealistic", "label": "Photorealistic"},
                                 {"value": "minimalist", "label": "Minimalist"},
                                 {"value": "illustration", "label": "Illustration"},
                                 {"value": "3d_render", "label": "3D Render"},
                                 {"value": "flat_design", "label": "Flat Design"}]),
            ConfigField("aspect_ratio", "Aspect Ratio", "select", default="1:1",
                        options=[{"value": "1:1", "label": "Square (1:1)"},
                                 {"value": "16:9", "label": "Landscape (16:9)"},
                                 {"value": "9:16", "label": "Portrait (9:16)"},
                                 {"value": "4:3", "label": "Standard (4:3)"}]),
        ],
        permissions=["content.create"],
    ),
    NodeDefinition(
        id="ai_analyse_profile",
        name="Analyse Social Profile",
        category="ai",
        description="Analyses a connected social account profile using AI to generate brand intelligence.",
        icon="Sparkles",
        color="#8b5cf6",
        inputs=[NodeIOSpec("account_id", "Social Account ID", "text")],
        outputs=[NodeIOSpec("profile_summary", "Profile Intelligence", "json")],
        config_schema=[
            ConfigField("account_id", "Social Account ID", "text", placeholder="{{trigger.account_id}}"),
        ],
        permissions=["social.view"],
    ),
    NodeDefinition(
        id="ai_recommend_time",
        name="Recommend Posting Time",
        category="ai",
        description="Recommends the optimal posting time based on historical data and platform patterns.",
        icon="Clock4",
        color="#8b5cf6",
        inputs=[NodeIOSpec("input", "Context", "json")],
        outputs=[
            NodeIOSpec("recommended_time", "Recommended Time", "text"),
            NodeIOSpec("reason", "Reasoning", "text"),
            NodeIOSpec("output", "Full Output", "json"),
        ],
        config_schema=[
            ConfigField("platform", "Platform", "select", default="x",
                        options=[{"value": "x", "label": "X"}, {"value": "instagram", "label": "Instagram"},
                                 {"value": "linkedin", "label": "LinkedIn"}, {"value": "facebook", "label": "Facebook"},
                                 {"value": "youtube", "label": "YouTube"}]),
            ConfigField("org_id", "Organisation ID", "text", placeholder="{{org.id}}"),
        ],
        permissions=["analytics.view"],
    ),
]

# ---------------------------------------------------------------------------
# SOCIAL NODES
# ---------------------------------------------------------------------------

_SOCIAL_NODES: List[NodeDefinition] = [
    NodeDefinition(
        id="social_publish",
        name="Publish Post",
        category="social",
        description="Publishes a post to a connected social account using the official platform API.",
        icon="Send",
        color="#06b6d4",
        inputs=[
            NodeIOSpec("text", "Post Text", "text", required=True),
            NodeIOSpec("media_urls", "Media URLs", "array"),
        ],
        outputs=[
            NodeIOSpec("post_id", "External Post ID", "text"),
            NodeIOSpec("platform", "Platform", "text"),
            NodeIOSpec("output", "Full Output", "json"),
        ],
        config_schema=[
            ConfigField("platform", "Platform", "select", required=True, default="x",
                        options=[{"value": "x", "label": "X"}, {"value": "instagram", "label": "Instagram"},
                                 {"value": "linkedin", "label": "LinkedIn"}, {"value": "facebook", "label": "Facebook"}]),
            ConfigField("body", "Post Body (or use input)", "textarea", placeholder="{{nodes.ai_gen.text}}"),
            ConfigField("account_id", "Social Account ID (optional, auto-select if blank)", "text"),
        ],
        permissions=["content.publish"],
    ),
    NodeDefinition(
        id="social_schedule",
        name="Schedule Post",
        category="social",
        description="Schedules a post for future publication at a specific time.",
        icon="CalendarClock",
        color="#06b6d4",
        inputs=[NodeIOSpec("text", "Post Text", "text", required=True)],
        outputs=[NodeIOSpec("schedule_id", "Schedule ID", "text"), NodeIOSpec("output", "Full Output", "json")],
        config_schema=[
            ConfigField("platform", "Platform", "select", required=True, default="x",
                        options=[{"value": "x", "label": "X"}, {"value": "linkedin", "label": "LinkedIn"},
                                 {"value": "instagram", "label": "Instagram"}, {"value": "facebook", "label": "Facebook"}]),
            ConfigField("scheduled_for", "Scheduled Time (ISO)", "text", placeholder="{{nodes.recommend_time.recommended_time}} or 2025-01-15T14:00:00Z"),
        ],
        permissions=["content.publish"],
    ),
    NodeDefinition(
        id="social_get_account",
        name="Get Social Account",
        category="social",
        description="Retrieves details of a connected social account for use in subsequent nodes.",
        icon="User",
        color="#06b6d4",
        inputs=[],
        outputs=[NodeIOSpec("account", "Account Data", "json")],
        config_schema=[
            ConfigField("platform", "Platform", "select", required=True, default="x",
                        options=[{"value": "x", "label": "X"}, {"value": "instagram", "label": "Instagram"},
                                 {"value": "linkedin", "label": "LinkedIn"}, {"value": "facebook", "label": "Facebook"},
                                 {"value": "youtube", "label": "YouTube"}]),
        ],
        permissions=["social.view"],
    ),
    NodeDefinition(
        id="social_content_validation",
        name="Content Validation",
        category="social",
        description="Validates content against platform limits, spam rules, and policy constraints before publishing.",
        icon="ShieldCheck",
        color="#06b6d4",
        inputs=[NodeIOSpec("text", "Text to Validate", "text", required=True)],
        outputs=[
            NodeIOSpec("is_valid", "Is Valid", "boolean"),
            NodeIOSpec("errors", "Validation Errors", "array"),
            NodeIOSpec("output", "Full Output", "json"),
        ],
        config_schema=[
            ConfigField("platform", "Platform", "select", required=True, default="x",
                        options=[{"value": "x", "label": "X"}, {"value": "instagram", "label": "Instagram"},
                                 {"value": "linkedin", "label": "LinkedIn"}, {"value": "facebook", "label": "Facebook"}]),
            ConfigField("check_spam", "Check Spam Patterns", "boolean", default=True),
            ConfigField("check_duplicates", "Check Duplicate Content", "boolean", default=True),
        ],
        permissions=["content.create"],
    ),
]

# ---------------------------------------------------------------------------
# LOGIC NODES
# ---------------------------------------------------------------------------

_LOGIC_NODES: List[NodeDefinition] = [
    NodeDefinition(
        id="logic_condition",
        name="Condition / IF",
        category="logic",
        description="Routes execution based on a conditional expression (true/false branching).",
        icon="GitBranch",
        color="#f59e0b",
        inputs=[NodeIOSpec("input", "Input Value", "any", required=True)],
        outputs=[
            NodeIOSpec("true", "True Branch", "any"),
            NodeIOSpec("false", "False Branch", "any"),
        ],
        config_schema=[
            ConfigField("field", "Field Expression", "expression", required=True,
                        placeholder="{{nodes.validation.is_valid}}", description="Expression to evaluate"),
            ConfigField("operator", "Operator", "select", required=True, default="equals",
                        options=[
                            {"value": "equals", "label": "Equals"},
                            {"value": "not_equals", "label": "Not Equals"},
                            {"value": "contains", "label": "Contains"},
                            {"value": "not_contains", "label": "Not Contains"},
                            {"value": "greater_than", "label": "Greater Than"},
                            {"value": "less_than", "label": "Less Than"},
                            {"value": "is_empty", "label": "Is Empty"},
                            {"value": "is_not_empty", "label": "Is Not Empty"},
                            {"value": "starts_with", "label": "Starts With"},
                            {"value": "ends_with", "label": "Ends With"},
                        ]),
            ConfigField("value", "Compare Value", "text", placeholder="true  or  approved"),
        ],
    ),
    NodeDefinition(
        id="logic_switch",
        name="Switch",
        category="logic",
        description="Routes execution to one of multiple branches based on a value.",
        icon="Shuffle",
        color="#f59e0b",
        inputs=[NodeIOSpec("input", "Input", "any", required=True)],
        outputs=[
            NodeIOSpec("case_1", "Case 1", "any"),
            NodeIOSpec("case_2", "Case 2", "any"),
            NodeIOSpec("case_3", "Case 3", "any"),
            NodeIOSpec("default", "Default", "any"),
        ],
        config_schema=[
            ConfigField("field", "Switch Field", "expression", required=True, placeholder="{{nodes.gen.platform}}"),
            ConfigField("case_1_value", "Case 1 Value", "text", placeholder="x"),
            ConfigField("case_2_value", "Case 2 Value", "text", placeholder="linkedin"),
            ConfigField("case_3_value", "Case 3 Value", "text", placeholder="instagram"),
        ],
    ),
    NodeDefinition(
        id="logic_filter",
        name="Filter",
        category="logic",
        description="Passes through execution only when a condition is met; otherwise stops that branch.",
        icon="Filter",
        color="#f59e0b",
        inputs=[NodeIOSpec("input", "Input", "any", required=True)],
        outputs=[NodeIOSpec("output", "Filtered Output", "any")],
        config_schema=[
            ConfigField("field", "Field Expression", "expression", required=True, placeholder="{{nodes.validation.is_valid}}"),
            ConfigField("operator", "Operator", "select", default="equals",
                        options=[{"value": "equals", "label": "Equals"}, {"value": "is_not_empty", "label": "Is Not Empty"},
                                 {"value": "greater_than", "label": "Greater Than"}]),
            ConfigField("value", "Value", "text", placeholder="true"),
        ],
    ),
]

# ---------------------------------------------------------------------------
# DATA NODES
# ---------------------------------------------------------------------------

_DATA_NODES: List[NodeDefinition] = [
    NodeDefinition(
        id="data_set_variable",
        name="Set Variable",
        category="data",
        description="Sets a workflow-level variable that can be read by subsequent nodes.",
        icon="Variable",
        color="#64748b",
        inputs=[NodeIOSpec("input", "Value", "any")],
        outputs=[NodeIOSpec("output", "Variable Value", "any")],
        config_schema=[
            ConfigField("variable_name", "Variable Name", "text", required=True, placeholder="my_variable"),
            ConfigField("value", "Value (or use expression)", "expression", placeholder="{{nodes.gen.text}}"),
        ],
    ),
    NodeDefinition(
        id="data_get_variable",
        name="Get Variable",
        category="data",
        description="Reads a previously set workflow variable.",
        icon="Database",
        color="#64748b",
        inputs=[],
        outputs=[NodeIOSpec("value", "Variable Value", "any")],
        config_schema=[
            ConfigField("variable_name", "Variable Name", "text", required=True, placeholder="my_variable"),
        ],
    ),
    NodeDefinition(
        id="data_template",
        name="Template",
        category="data",
        description="Constructs a text string using expression templates from other node outputs.",
        icon="FileCode",
        color="#64748b",
        inputs=[NodeIOSpec("input", "Context", "json")],
        outputs=[NodeIOSpec("text", "Rendered Text", "text")],
        config_schema=[
            ConfigField("template", "Template", "textarea", required=True,
                        placeholder="Post for {{nodes.get_account.account.platform}}: {{nodes.gen.text}}"),
        ],
    ),
    NodeDefinition(
        id="data_json_transform",
        name="JSON Transform",
        category="data",
        description="Transforms or reshapes a JSON object using field mapping.",
        icon="Braces",
        color="#64748b",
        inputs=[NodeIOSpec("input", "Input JSON", "json", required=True)],
        outputs=[NodeIOSpec("output", "Transformed JSON", "json")],
        config_schema=[
            ConfigField("mapping", "Field Mapping (JSON)", "json",
                        placeholder='{"new_key": "{{input.old_key}}"}'),
        ],
    ),
]

# ---------------------------------------------------------------------------
# TIME NODES
# ---------------------------------------------------------------------------

_TIME_NODES: List[NodeDefinition] = [
    NodeDefinition(
        id="time_delay",
        name="Delay",
        category="time",
        description="Pauses workflow execution for a specified duration.",
        icon="Timer",
        color="#ec4899",
        inputs=[NodeIOSpec("input", "Input", "any")],
        outputs=[NodeIOSpec("output", "Output", "any")],
        config_schema=[
            ConfigField("duration_seconds", "Delay Duration (seconds)", "number", default=60,
                        min_value=1, max_value=86400, description="Max 24 hours (86400 seconds)"),
        ],
    ),
    NodeDefinition(
        id="time_wait_until",
        name="Wait Until",
        category="time",
        description="Pauses workflow execution until a specific datetime.",
        icon="AlarmClock",
        color="#ec4899",
        inputs=[NodeIOSpec("input", "Input", "any")],
        outputs=[NodeIOSpec("output", "Output", "any")],
        config_schema=[
            ConfigField("wait_until", "Wait Until (ISO datetime or expression)", "expression",
                        required=True, placeholder="{{nodes.recommend_time.recommended_time}}"),
        ],
    ),
]

# ---------------------------------------------------------------------------
# UTILITY NODES
# ---------------------------------------------------------------------------

_UTILITY_NODES: List[NodeDefinition] = [
    NodeDefinition(
        id="utility_http_request",
        name="HTTP Request",
        category="utility",
        description="Makes a secure SSRF-protected HTTP request to an external API.",
        icon="Globe",
        color="#84cc16",
        inputs=[NodeIOSpec("body", "Request Body", "json")],
        outputs=[
            NodeIOSpec("status_code", "Status Code", "number"),
            NodeIOSpec("body", "Response Body", "json"),
            NodeIOSpec("output", "Full Response", "json"),
        ],
        config_schema=[
            ConfigField("url", "URL", "text", required=True, placeholder="https://api.example.com/endpoint"),
            ConfigField("method", "Method", "select", default="GET",
                        options=[{"value": "GET", "label": "GET"}, {"value": "POST", "label": "POST"},
                                 {"value": "PUT", "label": "PUT"}, {"value": "PATCH", "label": "PATCH"},
                                 {"value": "DELETE", "label": "DELETE"}]),
            ConfigField("headers", "Request Headers (JSON)", "json", placeholder='{"Content-Type": "application/json"}'),
            ConfigField("body", "Request Body (JSON)", "json", placeholder='{"key": "value"}'),
            ConfigField("timeout_seconds", "Timeout (seconds)", "number", default=15, min_value=1, max_value=60),
            ConfigField("auth_type", "Authentication", "select", default="none",
                        options=[{"value": "none", "label": "None"}, {"value": "bearer", "label": "Bearer Token"},
                                 {"value": "basic", "label": "Basic Auth"}]),
            ConfigField("auth_token", "Auth Token (use secret reference)", "secret_ref",
                        placeholder="{{secret:MY_API_TOKEN}}"),
        ],
    ),
    NodeDefinition(
        id="utility_notification",
        name="Send Notification",
        category="utility",
        description="Sends an in-app notification to the organisation member(s).",
        icon="Bell",
        color="#84cc16",
        inputs=[NodeIOSpec("input", "Context", "json")],
        outputs=[NodeIOSpec("output", "Result", "json")],
        config_schema=[
            ConfigField("title", "Notification Title", "text", required=True, placeholder="Workflow Alert"),
            ConfigField("message", "Message", "textarea", required=True, placeholder="{{nodes.gen.text}}"),
            ConfigField("type", "Type", "select", default="info",
                        options=[{"value": "info", "label": "Info"}, {"value": "success", "label": "Success"},
                                 {"value": "warning", "label": "Warning"}, {"value": "error", "label": "Error"}]),
        ],
    ),
    NodeDefinition(
        id="utility_log",
        name="Log",
        category="utility",
        description="Records a message in the workflow execution log (secrets are never logged).",
        icon="FileText",
        color="#84cc16",
        inputs=[NodeIOSpec("input", "Input", "any")],
        outputs=[NodeIOSpec("output", "Output (passthrough)", "any")],
        config_schema=[
            ConfigField("message", "Log Message", "textarea", required=True, placeholder="Step completed: {{nodes.gen.text}}"),
            ConfigField("level", "Log Level", "select", default="info",
                        options=[{"value": "info", "label": "Info"}, {"value": "warning", "label": "Warning"},
                                 {"value": "error", "label": "Error"}]),
        ],
    ),
    NodeDefinition(
        id="utility_plan_check",
        name="Plan Check",
        category="utility",
        description="Validates that the organisation's current plan permits a specific operation. Stops workflow if limit exceeded.",
        icon="CreditCard",
        color="#84cc16",
        inputs=[NodeIOSpec("input", "Context", "json")],
        outputs=[
            NodeIOSpec("allowed", "Allowed", "boolean"),
            NodeIOSpec("limit", "Plan Limit", "number"),
            NodeIOSpec("used", "Current Usage", "number"),
        ],
        config_schema=[
            ConfigField("feature", "Feature to Check", "select", required=True,
                        options=[{"value": "ai_posts_daily", "label": "Daily AI Posts"},
                                 {"value": "social_accounts", "label": "Social Accounts"},
                                 {"value": "workflow_executions", "label": "Workflow Executions"},
                                 {"value": "image_generation", "label": "Image Generation"}]),
        ],
        permissions=["billing.view"],
    ),
]

# ---------------------------------------------------------------------------
# CONTENT NODES
# ---------------------------------------------------------------------------

_CONTENT_NODES: List[NodeDefinition] = [
    NodeDefinition(
        id="content_create_draft",
        name="Create Draft",
        category="content",
        description="Creates a new content draft in the organisation's content library.",
        icon="FilePlus2",
        color="#f97316",
        inputs=[NodeIOSpec("text", "Post Body", "text", required=True)],
        outputs=[NodeIOSpec("content_id", "Content ID", "text"), NodeIOSpec("output", "Content Data", "json")],
        config_schema=[
            ConfigField("title", "Title (optional)", "text", placeholder="Auto-generated from AI"),
            ConfigField("platform", "Platform", "select", default="x",
                        options=[{"value": "x", "label": "X"}, {"value": "linkedin", "label": "LinkedIn"},
                                 {"value": "instagram", "label": "Instagram"}, {"value": "facebook", "label": "Facebook"}]),
            ConfigField("body", "Body (or use input)", "textarea", placeholder="{{nodes.gen.text}}"),
        ],
        permissions=["content.create"],
    ),
    NodeDefinition(
        id="content_request_approval",
        name="Request Approval",
        category="content",
        description="Sends a content item to the organisation's approval queue.",
        icon="UserCheck",
        color="#f97316",
        inputs=[NodeIOSpec("content_id", "Content ID", "text", required=True)],
        outputs=[
            NodeIOSpec("approved", "Approved", "boolean"),
            NodeIOSpec("output", "Approval Result", "json"),
        ],
        config_schema=[
            ConfigField("content_id", "Content ID (or use input)", "text", placeholder="{{nodes.draft.content_id}}"),
            ConfigField("timeout_hours", "Approval Timeout (hours)", "number", default=24,
                        description="Workflow pauses waiting for approval for this many hours"),
        ],
        permissions=["content.create"],
    ),
]


# ---------------------------------------------------------------------------
# BUILD REGISTRY
# ---------------------------------------------------------------------------

def _build_registry() -> Dict[str, NodeDefinition]:
    all_nodes = (
        _TRIGGER_NODES
        + _AI_NODES
        + _SOCIAL_NODES
        + _LOGIC_NODES
        + _DATA_NODES
        + _TIME_NODES
        + _UTILITY_NODES
        + _CONTENT_NODES
    )
    return {node.id: node for node in all_nodes}


NODE_REGISTRY: Dict[str, NodeDefinition] = _build_registry()


def get_node_definition(node_type: str) -> Optional[NodeDefinition]:
    """Return the NodeDefinition for a given node type ID, or None if not found."""
    return NODE_REGISTRY.get(node_type)


def get_all_nodes() -> List[Dict[str, Any]]:
    """Return all active node definitions serialized for the frontend API response."""
    result = []
    for node in NODE_REGISTRY.values():
        result.append({
            "id": node.id,
            "name": node.name,
            "category": node.category,
            "description": node.description,
            "icon": node.icon,
            "version": node.version,
            "color": node.color,
            "status": node.status,
            "inputs": [
                {"name": i.name, "label": i.label, "data_type": i.data_type, "required": i.required}
                for i in node.inputs
            ],
            "outputs": [
                {"name": o.name, "label": o.label, "data_type": o.data_type}
                for o in node.outputs
            ],
            "config_schema": [
                {
                    "key": f.key, "label": f.label, "field_type": f.field_type,
                    "required": f.required, "default": f.default,
                    "options": f.options, "placeholder": f.placeholder,
                    "description": f.description,
                    "min_value": f.min_value, "max_value": f.max_value,
                }
                for f in node.config_schema
            ],
            "permissions": node.permissions,
            "plan_requirements": node.plan_requirements,
        })
    return result


def get_nodes_by_category() -> Dict[str, List[Dict[str, Any]]]:
    """Return nodes grouped by category for the node library sidebar."""
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for node_data in get_all_nodes():
        cat = node_data["category"]
        by_cat.setdefault(cat, []).append(node_data)
    return by_cat
