"""
Custom Styling and Presentation Theme for ChatCollab Lab.
Includes CSS tokens, color schemes, badges for roles, and card containers.
"""

CUSTOM_CSS = """
<style>
/* Global aesthetics */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Header badge styling */
.paper-badge {
    display: inline-block;
    background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.prototype-tag {
    display: inline-block;
    background: #2d3436;
    color: #dfe6e9;
    border: 1px solid #636e72;
    padding: 3px 10px;
    border-radius: 14px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-left: 8px;
}

/* Metric KPI card */
.kpi-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(108, 92, 231, 0.15);
}

.kpi-title {
    font-size: 0.85rem;
    color: #b2bec3;
    font-weight: 500;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #f5f6fa;
}

/* Chat bubble styling */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin: 16px 0;
}

.chat-bubble {
    border-radius: 12px;
    padding: 14px 18px;
    max-width: 90%;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    line-height: 1.5;
}

.chat-ceo {
    background: linear-gradient(135deg, rgba(108, 92, 231, 0.12) 0%, rgba(108, 92, 231, 0.04) 100%);
    border-left: 4px solid #6c5ce7;
}

.chat-pm {
    background: linear-gradient(135deg, rgba(9, 132, 227, 0.12) 0%, rgba(9, 132, 227, 0.04) 100%);
    border-left: 4px solid #0984e3;
}

.chat-dev {
    background: linear-gradient(135deg, rgba(0, 184, 148, 0.12) 0%, rgba(0, 184, 148, 0.04) 100%);
    border-left: 4px solid #00b894;
}

.chat-qa {
    background: linear-gradient(135deg, rgba(225, 112, 85, 0.12) 0%, rgba(225, 112, 85, 0.04) 100%);
    border-left: 4px solid #e17055;
}

.chat-human {
    background: linear-gradient(135deg, rgba(0, 206, 201, 0.14) 0%, rgba(0, 206, 201, 0.05) 100%);
    border-left: 4px solid #00cec9;
}

.chat-system {
    background: rgba(99, 110, 114, 0.1);
    border-left: 4px solid #b2bec3;
    font-size: 0.9rem;
}

.actor-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    font-weight: 600;
    font-size: 0.95rem;
}

.role-badge {
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    text-transform: uppercase;
}

.role-ceo { background: #6c5ce7; color: white; }
.role-pm { background: #0984e3; color: white; }
.role-dev { background: #00b894; color: white; }
.role-qa { background: #e17055; color: white; }
.role-human { background: #00cec9; color: #1e272e; }
.role-system { background: #636e72; color: white; }

.event-type-tag {
    font-size: 0.7rem;
    color: #a4b0be;
    font-family: 'JetBrains Mono', monospace;
    background: rgba(255, 255, 255, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: auto;
}

.timestamp-text {
    font-size: 0.72rem;
    color: #747d8c;
    margin-left: 6px;
}

/* Callout cards for paper takeaways */
.paper-insight-box {
    border-left: 4px solid #6c5ce7;
    background: rgba(108, 92, 231, 0.08);
    padding: 14px 18px;
    border-radius: 0 10px 10px 0;
    margin: 12px 0;
}

/* Presentation slide card */
.presentation-slide-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
</style>
"""


def get_role_color(role_name: str) -> str:
    """Return HEX color matching agent role."""
    r = role_name.lower()
    if "ceo" in r:
        return "#6c5ce7"
    elif "product" in r or "pm" in r:
        return "#0984e3"
    elif "dev" in r:
        return "#00b894"
    elif "qa" in r:
        return "#e17055"
    elif "human" in r:
        return "#00cec9"
    return "#a4b0be"
