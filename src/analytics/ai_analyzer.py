"""
AI-Powered Survey Response Analyzer
Uses OpenRouter with cost-effective models for qualitative analysis
"""

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv(".env.local")


class AIAnalyzer:
    """AI-powered analyzer for qualitative survey responses."""

    def __init__(self):
        """Initialize OpenRouter client."""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        # Use Claude 3.5 Haiku - best balance of quality and cost for analysis
        # $1/1M input tokens, $5/1M output tokens
        self.model = "anthropic/claude-3.5-haiku"

    def analyze_dimension_responses(
        self, dimension: str, free_text_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze free text responses for a dimension to generate score modifiers.

        Args:
            dimension: Technology dimension name
            free_text_responses: List of dicts with 'respondent', 'role', 'text' keys

        Returns:
            Dict with 'modifiers' list and 'summary' string
        """
        if not free_text_responses:
            return {"modifiers": [], "summary": "No free text responses provided for analysis."}

        # Prepare context for AI
        responses_text = "\n\n".join(
            [f"[{r['role']} - {r['respondent']}]:\n{r['text']}" for r in free_text_responses]
        )

        prompt = f"""Analyze the following free text survey responses for the "{dimension}" technology dimension.

Your task is to identify qualitative factors that should modify the quantitative scores, and explain why.

Survey Responses:
{responses_text}

Please provide:
1. Score Modifiers: Identify specific factors mentioned that warrant score adjustments
   - Each modifier should be between -1.0 (very negative factor) and +1.0 (very positive factor)
   - Include the respondent name and role for each modifier
   - Explain the reasoning for each modifier

2. Summary: Brief overview of common themes and insights

Return your analysis in this JSON format:
{{
  "modifiers": [
    {{
      "respondent": "Name",
      "role": "CEO/Tech Lead/Staff",
      "value": 0.5,
      "factor": "Brief description of the factor",
      "reasoning": "Why this warrants a score adjustment"
    }}
  ],
  "summary": "2-3 sentence summary of qualitative insights"
}}

Focus on:
- Concrete capabilities or gaps mentioned beyond the quantitative scores
- Context that explains high or low quantitative ratings
- Strategic advantages or challenges
- Cultural or organizational factors affecting technology effectiveness
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technology assessment analyst. Analyze survey responses to identify qualitative factors that should adjust quantitative technology maturity scores.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            # Parse JSON response
            content = response.choices[0].message.content

            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            return result

        except Exception as e:
            print(f"Error analyzing dimension responses: {e}")
            return {"modifiers": [], "summary": f"Error analyzing responses: {str(e)}"}

    def summarize_all_feedback(self, all_responses: List[Dict[str, Any]]) -> str:
        """
        Generate a comprehensive summary of all free text feedback across organizations.

        Args:
            all_responses: List of all free text responses across all orgs

        Returns:
            Summary string for the home page
        """
        if not all_responses:
            return "No free text feedback available for analysis."

        # Group by organization
        org_responses = {}
        for r in all_responses:
            org = r.get("organization", "Unknown")
            if org not in org_responses:
                org_responses[org] = []
            org_responses[org].append(r)

        # Prepare summary context
        summary_text = f"Analyzing {len(all_responses)} free text responses from {len(org_responses)} organizations:\n\n"

        for org, responses in org_responses.items():
            summary_text += f"[{org}] - {len(responses)} responses\n"
            for r in responses[:3]:  # Limit to first 3 per org for token efficiency
                summary_text += f"  {r.get('role', 'Unknown')}: {r.get('text', '')[:150]}...\n"

        prompt = f"""Analyze the following free text survey feedback from multiple nonprofit organizations about their technology readiness.

{summary_text}

Provide a concise 2-3 paragraph summary highlighting:
1. Common themes and patterns across organizations
2. Key challenges or gaps mentioned
3. Notable strengths or innovative approaches
4. Overall sentiment about technology readiness

Keep the summary professional, actionable, and suitable for a dashboard overview.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technology consultant summarizing feedback from nonprofit organizations about their technology capabilities.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=500,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error summarizing feedback: {e}")
            return f"Error generating summary: {str(e)}"

    def consolidate_text(self, text: str, max_chars: int = 150) -> str:
        """
        Consolidate long text into concise version using LLM.

        Args:
            text: Original text to consolidate
            max_chars: Target character count (approximate)

        Returns:
            Consolidated text that preserves key insights
        """
        # If already short enough, return as-is
        if len(text) <= max_chars:
            return text

        prompt = f"""Consolidate this text to approximately {max_chars} characters while preserving key insights:

Original text ({len(text)} chars):
{text}

Requirements:
- Keep essential information and insights
- Remove redundant phrases and filler words
- Use concise, professional language
- Maintain the same tone and meaning
- Target length: {max_chars} characters (strict maximum)

Return ONLY the consolidated text, no explanations or metadata:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert editor who consolidates verbose text into concise summaries while preserving key insights. Return only the consolidated text."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100  # Keep response short
            )

            consolidated = response.choices[0].message.content.strip()

            # Remove quotes if LLM added them
            if consolidated.startswith('"') and consolidated.endswith('"'):
                consolidated = consolidated[1:-1]
            if consolidated.startswith("'") and consolidated.endswith("'"):
                consolidated = consolidated[1:-1]

            # Fallback: if still too long, hard truncate
            if len(consolidated) > max_chars + 20:
                consolidated = consolidated[:max_chars] + "..."

            return consolidated

        except Exception as e:
            print(f"Error consolidating text: {e}")
            # Fallback: simple truncation
            return text[:max_chars] + "..." if len(text) > max_chars else text

    def analyze_organization_qualitative(
        self, org_name: str, all_responses: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Comprehensive qualitative analysis for an organization across all dimensions.

        Args:
            org_name: Organization name
            all_responses: Dict mapping dimension names to lists of free text responses

        Returns:
            Dict with dimension-level analysis and overall insights
        """
        results = {"organization": org_name, "dimensions": {}, "overall_summary": ""}

        # Analyze each dimension
        for dimension, responses in all_responses.items():
            if responses:
                results["dimensions"][dimension] = self.analyze_dimension_responses(
                    dimension, responses
                )

        # Generate overall summary
        all_texts = []
        for dimension, responses in all_responses.items():
            for r in responses:
                all_texts.append({"dimension": dimension, "organization": org_name, **r})

        if all_texts:
            results["overall_summary"] = self.summarize_all_feedback(all_texts)

        return results


def extract_free_text_responses(
    sheet_data: Dict[str, List[Dict[str, Any]]], org_name: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract all free text (non-numeric) responses for an organization.

    Args:
        sheet_data: Complete sheet data from SheetsReader
        org_name: Organization name to filter by

    Returns:
        Dict mapping dimension names to lists of free text responses
    """
    dimension_responses = {
        "Program Technology": [],
        "Business Systems": [],
        "Data Management": [],
        "Infrastructure": [],
        "Organizational Culture": [],
    }

    # Dimension code mapping
    dimension_codes = {
        "PT": "Program Technology",
        "BS": "Business Systems",
        "D": "Data Management",
        "I": "Infrastructure",
        "OC": "Organizational Culture",
    }

    # Check CEO, Tech, Staff tabs
    for tab_name, role in [("CEO", "CEO"), ("Tech", "Tech Lead"), ("Staff", "Staff")]:
        records = sheet_data.get(tab_name, [])

        for record in records:
            if record.get("Organization") == org_name:
                # Extract free text responses (non-numeric)
                for key, value in record.items():
                    # Look for question IDs that match dimension pattern
                    if key.startswith(("C-", "TL-", "S-")) and value:
                        # Check if it's free text (not a number)
                        try:
                            float(str(value).strip())
                            # It's numeric, skip
                            continue
                        except (ValueError, TypeError):
                            # It's free text, extract dimension
                            parts = key.split("-")
                            if len(parts) >= 2:
                                code = parts[1]
                                dimension = dimension_codes.get(code)

                                if dimension and len(str(value).strip()) > 10:  # Meaningful text
                                    dimension_responses[dimension].append(
                                        {
                                            "respondent": record.get(
                                                "Name", record.get("Email", "Unknown")
                                            ),
                                            "role": role,
                                            "text": str(value).strip(),
                                            "question_id": key,
                                        }
                                    )

    return dimension_responses


# Example usage
if __name__ == "__main__":
    analyzer = AIAnalyzer()

    # Test with sample data
    sample_responses = [
        {
            "respondent": "Jane Smith",
            "role": "CEO",
            "text": "We have strong program delivery tools but struggle with integration between systems. Staff training is a major gap.",
        },
        {
            "respondent": "John Doe",
            "role": "Tech Lead",
            "text": "Infrastructure is solid but we need better data governance policies. Current systems are not well documented.",
        },
    ]

    result = analyzer.analyze_dimension_responses("Program Technology", sample_responses)
    print(json.dumps(result, indent=2))
