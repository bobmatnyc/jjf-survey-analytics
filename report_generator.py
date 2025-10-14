"""
Report Generator for JJF Survey Analytics
Generates per-organization and aggregate reports
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai_analyzer import AIAnalyzer, extract_free_text_responses
from maturity_rubric import MaturityRubric


class ReportGenerator:
    """Generates reports for survey analytics data."""

    def __init__(self, sheet_data: Dict[str, List[Dict[str, Any]]], enable_ai: bool = True):
        """
        Initialize report generator with sheet data.

        Args:
            sheet_data: Dictionary containing all tab data from Google Sheets
            enable_ai: Whether to enable AI-powered qualitative analysis
        """
        self.sheet_data = sheet_data
        self.questions_lookup = self._build_questions_lookup()
        self.rubric = MaturityRubric()
        self.enable_ai = enable_ai

        # Initialize AI analyzer if enabled
        self.ai_analyzer = None
        if self.enable_ai:
            try:
                self.ai_analyzer = AIAnalyzer()
            except Exception as e:
                print(f"Warning: AI analyzer not available: {e}")
                self.enable_ai = False

    def _build_questions_lookup(self) -> Dict[str, Dict[str, Any]]:
        """Build lookup dictionary for questions and answer keys."""
        questions = {}
        questions_data = self.sheet_data.get("Questions", [])

        for row in questions_data:
            question_id = row.get("Question ID", "")
            if question_id:
                questions[question_id] = {
                    "question": row.get("QUESTION", ""),
                    "category": row.get("Category", "General"),
                    "answer_keys": {
                        1: row.get("Answer 1", ""),
                        2: row.get("Answer 2", ""),
                        3: row.get("Answer 3", ""),
                        4: row.get("Answer 4", ""),
                        5: row.get("Answer 5", ""),
                        6: row.get("Answer 6", ""),
                        7: row.get("Answer 7", ""),
                    },
                }

        return questions

    def _extract_numeric_responses(self, record: Dict[str, Any]) -> Dict[str, float]:
        """Extract numeric responses (ignoring text/open-ended)."""
        numeric_responses = {}

        for key, value in record.items():
            if key.startswith(("C-", "TL-", "S-")) and value:
                try:
                    # Try to convert to float
                    num_value = float(str(value).strip())
                    # Only include if it's a valid rating (0-5, excluding 6 which is N/A)
                    if 0 <= num_value <= 5:
                        numeric_responses[key] = num_value
                except (ValueError, TypeError):
                    # Skip text responses
                    continue

        return numeric_responses

    def generate_organization_report(self, org_name: str) -> Optional[Dict[str, Any]]:
        """
        Generate comprehensive report for a single organization.

        Args:
            org_name: Organization name

        Returns:
            Dictionary containing report data with maturity assessment
        """
        # Find intake record
        intake_data = self.sheet_data.get("Intake", [])
        intake_record = None
        for row in intake_data:
            if row.get("Organization Name:") == org_name:
                intake_record = row
                break

        if not intake_record:
            return None

        # Get CEO data
        ceo_data = self.sheet_data.get("CEO", [])
        ceo_record = None
        for row in ceo_data:
            if row.get("CEO Organization") == org_name:
                ceo_record = row
                break

        # Get Tech data
        tech_data = self.sheet_data.get("Tech", [])
        tech_records = [row for row in tech_data if row.get("Organization") == org_name]

        # Get Staff data
        staff_data = self.sheet_data.get("Staff", [])
        staff_records = [row for row in staff_data if row.get("Organization") == org_name]

        # Calculate maturity assessment
        org_responses = {
            "CEO": self._extract_numeric_responses(ceo_record) if ceo_record else {},
            "Tech": self._extract_numeric_responses(tech_records[0]) if tech_records else {},
            "Staff": self._extract_numeric_responses(staff_records[0]) if staff_records else {},
        }

        maturity_assessment = self.rubric.calculate_overall_maturity(org_responses)

        # AI-powered qualitative analysis
        ai_insights = None
        if self.enable_ai and self.ai_analyzer:
            try:
                free_text_responses = extract_free_text_responses(self.sheet_data, org_name)
                ai_insights = self.ai_analyzer.analyze_organization_qualitative(
                    org_name, free_text_responses
                )

                # Consolidate AI dimension summaries
                if ai_insights and "dimensions" in ai_insights:
                    for dimension, analysis in ai_insights["dimensions"].items():
                        if "summary" in analysis and analysis["summary"]:
                            # Target 120 characters for dimension summaries
                            analysis["summary"] = self.ai_analyzer.consolidate_text(
                                analysis["summary"], max_chars=120
                            )
            except Exception as e:
                print(f"Warning: AI analysis failed for {org_name}: {e}")

        # Consolidate maturity description if AI is available
        if self.enable_ai and self.ai_analyzer and maturity_assessment.get("maturity_description"):
            try:
                # Target 55 characters for overall description
                maturity_assessment["maturity_description"] = self.ai_analyzer.consolidate_text(
                    maturity_assessment["maturity_description"], max_chars=55
                )
            except Exception as e:
                print(f"Warning: Could not consolidate maturity description: {e}")

        # Generate aggregate summary if AI is available
        if self.enable_ai and self.ai_analyzer and maturity_assessment:
            try:
                aggregate_summary = self._generate_aggregate_summary(
                    maturity_assessment, ai_insights
                )
                maturity_assessment["aggregate_summary"] = aggregate_summary
            except Exception as e:
                print(f"Warning: Could not generate aggregate summary: {e}")
                maturity_assessment["aggregate_summary"] = None

        # Build report sections
        report = {
            "header": self._build_org_header(org_name, intake_record),
            "maturity": maturity_assessment,  # Quantitative maturity assessment
            "ai_insights": ai_insights,  # NEW: Qualitative AI analysis with modifiers
            "timeline": self._build_org_timeline(
                intake_record, ceo_record, tech_records, staff_records
            ),
            "contacts": self._build_org_contacts(ceo_record, tech_records, staff_records),
            "intake": self._build_org_intake_insights(intake_record),
            "responses": self._build_org_responses(ceo_record, tech_records, staff_records),
            "export": self._build_org_export_data(org_name),
        }

        return report

    def generate_aggregate_report(self) -> Dict[str, Any]:
        """
        Generate aggregate report across all organizations.

        Returns:
            Dictionary containing aggregate report data with 7 sections
        """
        intake_data = self.sheet_data.get("Intake", [])
        ceo_data = self.sheet_data.get("CEO", [])
        tech_data = self.sheet_data.get("Tech", [])
        staff_data = self.sheet_data.get("Staff", [])

        report = {
            "header": self._build_aggregate_header(),
            "overview": self._build_aggregate_overview(
                intake_data, ceo_data, tech_data, staff_data
            ),
            "breakdown": self._build_aggregate_breakdown(ceo_data, tech_data, staff_data),
            "timeline": self._build_aggregate_timeline(
                intake_data, ceo_data, tech_data, staff_data
            ),
            "table": self._build_aggregate_table(intake_data, ceo_data, tech_data, staff_data),
            "insights": self._build_aggregate_insights(ceo_data, tech_data, staff_data),
            "recommendations": self._build_aggregate_recommendations(
                intake_data, ceo_data, tech_data, staff_data
            ),
        }

        return report

    # Organization Report Section Builders

    def _build_org_header(self, org_name: str, intake_record: Dict) -> Dict[str, Any]:
        """Build organization report header section."""
        return {
            "organization_name": org_name,
            "intake_date": (
                intake_record.get("Date", "N/A")[:10] if intake_record.get("Date") else "N/A"
            ),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _build_org_summary(
        self, ceo_record: Optional[Dict], tech_records: List[Dict], staff_records: List[Dict]
    ) -> Dict[str, Any]:
        """Build organization summary metrics."""
        total_surveys = 3  # CEO, Tech, Staff
        completed = 0

        if ceo_record and ceo_record.get("Date"):
            completed += 1
        if any(r.get("Date") for r in tech_records):
            completed += 1
        if any(r.get("Date") for r in staff_records):
            completed += 1

        completion_pct = round((completed / total_surveys) * 100) if total_surveys > 0 else 0

        return {
            "total_surveys": total_surveys,
            "completed_surveys": completed,
            "pending_surveys": total_surveys - completed,
            "completion_percentage": completion_pct,
            "ceo_complete": bool(ceo_record and ceo_record.get("Date")),
            "tech_complete": any(r.get("Date") for r in tech_records),
            "staff_complete": any(r.get("Date") for r in staff_records),
            "total_responses": (
                len([k for k in (ceo_record or {}).keys() if k.startswith("C-")])
                + sum(len([k for k in r.keys() if k.startswith("TL-")]) for r in tech_records)
                + sum(len([k for k in r.keys() if k.startswith("S-")]) for r in staff_records)
            ),
        }

    def _build_org_timeline(
        self,
        intake_record: Dict,
        ceo_record: Optional[Dict],
        tech_records: List[Dict],
        staff_records: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Build organization activity timeline."""
        timeline = []

        # Intake event
        if intake_record.get("Date"):
            timeline.append(
                {
                    "date": intake_record.get("Date", "")[:10],
                    "event_type": "Intake",
                    "description": "Organization intake completed",
                    "icon": "clipboard-check",
                    "color": "gray",
                }
            )

        # CEO survey event
        if ceo_record and ceo_record.get("Date"):
            timeline.append(
                {
                    "date": ceo_record.get("Date", "")[:10],
                    "event_type": "CEO Survey",
                    "description": f"{ceo_record.get('Name', 'CEO')} completed survey",
                    "icon": "user-tie",
                    "color": "blue",
                }
            )

        # Tech Lead survey events
        for tech in tech_records:
            if tech.get("Date"):
                timeline.append(
                    {
                        "date": tech.get("Date", "")[:10],
                        "event_type": "Tech Lead Survey",
                        "description": f"{tech.get('Name', 'Tech Lead')} completed survey",
                        "icon": "laptop-code",
                        "color": "purple",
                    }
                )

        # Staff survey events
        for staff in staff_records:
            if staff.get("Date"):
                timeline.append(
                    {
                        "date": staff.get("Date", "")[:10],
                        "event_type": "Staff Survey",
                        "description": f"{staff.get('Name', 'Staff')} completed survey",
                        "icon": "users",
                        "color": "green",
                    }
                )

        # Sort by date
        timeline.sort(key=lambda x: x["date"], reverse=True)

        return timeline

    def _build_org_contacts(
        self, ceo_record: Optional[Dict], tech_records: List[Dict], staff_records: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Build organization contacts list."""
        contacts = []

        # CEO contact
        if ceo_record:
            contacts.append(
                {
                    "name": ceo_record.get("Name", ""),
                    "email": ceo_record.get("CEO Email", ""),
                    "role": ceo_record.get("CEO Role", "CEO"),
                    "type": "CEO",
                    "survey_complete": bool(ceo_record.get("Date")),
                    "submission_date": (
                        ceo_record.get("Date", "")[:10] if ceo_record.get("Date") else None
                    ),
                }
            )

        # Tech Lead contacts
        for tech in tech_records:
            contacts.append(
                {
                    "name": tech.get("Name", ""),
                    "email": tech.get("Login Email", ""),
                    "role": "Tech Lead",
                    "type": "Tech Lead",
                    "survey_complete": bool(tech.get("Date")),
                    "submission_date": tech.get("Date", "")[:10] if tech.get("Date") else None,
                }
            )

        # Staff contacts
        for staff in staff_records:
            contacts.append(
                {
                    "name": staff.get("Name", ""),
                    "email": staff.get("Login Email", ""),
                    "role": "Staff",
                    "type": "Staff",
                    "survey_complete": bool(staff.get("Date")),
                    "submission_date": staff.get("Date", "")[:10] if staff.get("Date") else None,
                }
            )

        return contacts

    def _build_org_intake_insights(self, intake_record: Dict) -> Dict[str, Any]:
        """Build intake information insights."""
        return {
            "ai_usage": intake_record.get(
                "Please select which of these best describes how AI is currently being used in your organization:",
                "Not specified",
            ),
            "ai_policy": intake_record.get("Do you have an AI policy in place?", "Not specified"),
            "comments": intake_record.get(
                "Do you have any suggestions or comments for us on the Technology Strategy?", ""
            ),
            "raw_data": intake_record,
        }

    def _build_org_responses(
        self, ceo_record: Optional[Dict], tech_records: List[Dict], staff_records: List[Dict]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Build organization survey responses by category."""
        responses_by_category = defaultdict(list)

        # Process CEO responses
        if ceo_record:
            for key, value in ceo_record.items():
                if key.startswith("C-") and value:
                    question_info = self.questions_lookup.get(key, {})
                    category = question_info.get("category", "General")

                    response = {
                        "question_id": key,
                        "question_text": question_info.get("question", key),
                        "answer_value": value,
                        "answer_text": self._get_answer_text(value, question_info),
                        "respondent": ceo_record.get("Name", "CEO"),
                        "role": "CEO",
                    }
                    responses_by_category[category].append(response)

        # Process Tech responses
        for tech in tech_records:
            for key, value in tech.items():
                if key.startswith("TL-") and value:
                    question_info = self.questions_lookup.get(key, {})
                    category = question_info.get("category", "General")

                    response = {
                        "question_id": key,
                        "question_text": question_info.get("question", key),
                        "answer_value": value,
                        "answer_text": self._get_answer_text(value, question_info),
                        "respondent": tech.get("Name", "Tech Lead"),
                        "role": "Tech Lead",
                    }
                    responses_by_category[category].append(response)

        # Process Staff responses
        for staff in staff_records:
            for key, value in staff.items():
                if key.startswith("S-") and value:
                    question_info = self.questions_lookup.get(key, {})
                    category = question_info.get("category", "General")

                    response = {
                        "question_id": key,
                        "question_text": question_info.get("question", key),
                        "answer_value": value,
                        "answer_text": self._get_answer_text(value, question_info),
                        "respondent": staff.get("Name", "Staff"),
                        "role": "Staff",
                    }
                    responses_by_category[category].append(response)

        return dict(responses_by_category)

    def _build_org_export_data(self, org_name: str) -> Dict[str, Any]:
        """Build export metadata for organization."""
        return {
            "organization_name": org_name,
            "export_timestamp": datetime.now().isoformat(),
            "formats_available": ["PDF", "CSV", "JSON"],
        }

    # Aggregate Report Section Builders

    def _build_aggregate_header(self) -> Dict[str, Any]:
        """Build aggregate report header."""
        return {
            "title": "JJF Survey Analytics - Aggregate Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": "Aggregate",
        }

    def _build_aggregate_overview(
        self,
        intake_data: List[Dict],
        ceo_data: List[Dict],
        tech_data: List[Dict],
        staff_data: List[Dict],
    ) -> Dict[str, Any]:
        """Build aggregate overview metrics."""
        total_orgs = len(intake_data)

        # Count unique organizations per survey type (FIXED: count orgs, not responses)
        orgs_with_ceo = {
            r.get("CEO Organization") or r.get("Organization")
            for r in ceo_data
            if r.get("Date") and (r.get("CEO Organization") or r.get("Organization"))
        }
        orgs_with_tech = {
            r.get("Organization") for r in tech_data if r.get("Date") and r.get("Organization")
        }
        orgs_with_staff = {
            r.get("Organization") for r in staff_data if r.get("Date") and r.get("Organization")
        }

        # Organizations with at least one survey
        responding_orgs = orgs_with_ceo | orgs_with_tech | orgs_with_staff
        responding_orgs_count = len(responding_orgs)

        # Count completed survey types (not individual responses)
        ceo_complete = len(orgs_with_ceo)  # 3 orgs
        tech_complete = len(orgs_with_tech)  # 2 orgs
        staff_complete = len(orgs_with_staff)  # 2 orgs (not 4 responses!)
        surveys_completed = ceo_complete + tech_complete + staff_complete  # 7 total

        # Expected surveys based on responding organizations
        expected_surveys = responding_orgs_count * 3  # 3 orgs × 3 = 9

        # Count fully complete organizations
        fully_complete = len(orgs_with_ceo & orgs_with_tech & orgs_with_staff)

        return {
            "total_organizations": total_orgs,  # 28 (intake)
            "responding_organizations": responding_orgs_count,  # 3 (NEW)
            "total_surveys_expected": expected_surveys,  # 9 (not 84)
            "surveys_completed": surveys_completed,  # 7 (not 9)
            "surveys_pending": expected_surveys - surveys_completed,  # 2
            "completion_percentage": (
                round((surveys_completed / expected_surveys) * 100)
                if expected_surveys > 0
                else 0
            ),  # 78% (not 11%)
            "fully_complete_orgs": fully_complete,  # 1 (Hadar)
            "ceo_complete": ceo_complete,  # 3 orgs
            "tech_complete": tech_complete,  # 2 orgs
            "staff_complete": staff_complete,  # 2 orgs
            "ceo_percentage": (
                round((ceo_complete / responding_orgs_count) * 100)
                if responding_orgs_count > 0
                else 0
            ),
            "tech_percentage": (
                round((tech_complete / responding_orgs_count) * 100)
                if responding_orgs_count > 0
                else 0
            ),
            "staff_percentage": (
                round((staff_complete / responding_orgs_count) * 100)
                if responding_orgs_count > 0
                else 0
            ),
        }

    def _build_aggregate_breakdown(
        self, ceo_data: List[Dict], tech_data: List[Dict], staff_data: List[Dict]
    ) -> Dict[str, Any]:
        """Build aggregate breakdown by survey type."""
        return {
            "by_survey_type": {
                "CEO": {
                    "completed": len([r for r in ceo_data if r.get("Date")]),
                    "pending": len([r for r in ceo_data if not r.get("Date")]),
                    "total_responses": sum(
                        len([k for k in r.keys() if k.startswith("C-")])
                        for r in ceo_data
                        if r.get("Date")
                    ),
                },
                "Tech Lead": {
                    "completed": len([r for r in tech_data if r.get("Date")]),
                    "pending": len([r for r in tech_data if not r.get("Date")]),
                    "total_responses": sum(
                        len([k for k in r.keys() if k.startswith("TL-")])
                        for r in tech_data
                        if r.get("Date")
                    ),
                },
                "Staff": {
                    "completed": len([r for r in staff_data if r.get("Date")]),
                    "pending": len([r for r in staff_data if not r.get("Date")]),
                    "total_responses": sum(
                        len([k for k in r.keys() if k.startswith("S-")])
                        for r in staff_data
                        if r.get("Date")
                    ),
                },
            }
        }

    def _build_aggregate_timeline(
        self,
        intake_data: List[Dict],
        ceo_data: List[Dict],
        tech_data: List[Dict],
        staff_data: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Build aggregate activity timeline."""
        timeline = []

        # Collect all events
        for intake in intake_data:
            if intake.get("Date"):
                timeline.append(
                    {
                        "date": intake.get("Date", "")[:10],
                        "event_type": "Intake",
                        "organization": intake.get("Organization Name:", "Unknown"),
                        "count": 1,
                    }
                )

        for ceo in ceo_data:
            if ceo.get("Date"):
                timeline.append(
                    {
                        "date": ceo.get("Date", "")[:10],
                        "event_type": "CEO Survey",
                        "organization": ceo.get("CEO Organization", "Unknown"),
                        "count": 1,
                    }
                )

        for tech in tech_data:
            if tech.get("Date"):
                timeline.append(
                    {
                        "date": tech.get("Date", "")[:10],
                        "event_type": "Tech Survey",
                        "organization": tech.get("Organization", "Unknown"),
                        "count": 1,
                    }
                )

        for staff in staff_data:
            if staff.get("Date"):
                timeline.append(
                    {
                        "date": staff.get("Date", "")[:10],
                        "event_type": "Staff Survey",
                        "organization": staff.get("Organization", "Unknown"),
                        "count": 1,
                    }
                )

        # Sort by date descending
        timeline.sort(key=lambda x: x["date"], reverse=True)

        # Limit to recent 20 events
        return timeline[:20]

    def _build_aggregate_table(
        self,
        intake_data: List[Dict],
        ceo_data: List[Dict],
        tech_data: List[Dict],
        staff_data: List[Dict],
    ) -> List[Dict[str, Any]]:
        """Build aggregate organization status table."""
        org_status = []

        for intake in intake_data:
            org_name = intake.get("Organization Name:", "")
            if not org_name:
                continue

            # Find matching records
            ceo_record = next((r for r in ceo_data if r.get("CEO Organization") == org_name), None)
            tech_records = [r for r in tech_data if r.get("Organization") == org_name]
            staff_records = [r for r in staff_data if r.get("Organization") == org_name]

            # Calculate status
            ceo_complete = bool(ceo_record and ceo_record.get("Date"))
            tech_complete = any(r.get("Date") for r in tech_records)
            staff_complete = any(r.get("Date") for r in staff_records)

            completed = sum([ceo_complete, tech_complete, staff_complete])
            completion_pct = round((completed / 3) * 100)

            org_status.append(
                {
                    "organization": org_name,
                    "intake_date": intake.get("Date", "")[:10] if intake.get("Date") else "N/A",
                    "ceo_status": "Complete" if ceo_complete else "Pending",
                    "tech_status": "Complete" if tech_complete else "Pending",
                    "staff_status": "Complete" if staff_complete else "Pending",
                    "completion_percentage": completion_pct,
                    "overall_status": (
                        "Complete"
                        if completed == 3
                        else ("In Progress" if completed > 0 else "Not Started")
                    ),
                }
            )

        # Sort by completion percentage descending
        org_status.sort(key=lambda x: x["completion_percentage"], reverse=True)

        return org_status

    def _build_aggregate_insights(
        self, ceo_data: List[Dict], tech_data: List[Dict], staff_data: List[Dict]
    ) -> Dict[str, Any]:
        """Build aggregate insights and statistics."""
        # Collect all numeric responses
        all_responses = []

        for ceo in ceo_data:
            if ceo.get("Date"):
                for key, value in ceo.items():
                    if key.startswith("C-") and value:
                        if str(value).strip().isdigit():
                            all_responses.append(int(value))

        for tech in tech_data:
            if tech.get("Date"):
                for key, value in tech.items():
                    if key.startswith("TL-") and value:
                        if str(value).strip().isdigit():
                            all_responses.append(int(value))

        for staff in staff_data:
            if staff.get("Date"):
                for key, value in staff.items():
                    if key.startswith("S-") and value:
                        if str(value).strip().isdigit():
                            all_responses.append(int(value))

        # Calculate statistics
        if all_responses:
            avg_score = round(sum(all_responses) / len(all_responses), 2)
            min_score = min(all_responses)
            max_score = max(all_responses)
        else:
            avg_score = min_score = max_score = 0

        return {
            "total_responses": len(all_responses),
            "average_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "high_scores": len([r for r in all_responses if r >= 6]),
            "low_scores": len([r for r in all_responses if r <= 2]),
        }

    def _build_aggregate_recommendations(
        self,
        intake_data: List[Dict],
        ceo_data: List[Dict],
        tech_data: List[Dict],
        staff_data: List[Dict],
    ) -> List[str]:
        """Build aggregate recommendations."""
        recommendations = []

        total_orgs = len(intake_data)
        ceo_complete = len([r for r in ceo_data if r.get("Date")])
        tech_complete = len([r for r in tech_data if r.get("Date")])
        staff_complete = len([r for r in staff_data if r.get("Date")])

        # CEO completion rate
        if ceo_complete < total_orgs * 0.5:
            recommendations.append(
                f"Focus on CEO survey completion: Only {ceo_complete}/{total_orgs} ({round((ceo_complete/total_orgs)*100)}%) completed"
            )

        # Tech completion rate
        if tech_complete < total_orgs * 0.5:
            recommendations.append(
                f"Increase Tech Lead engagement: Only {tech_complete} surveys completed"
            )

        # Staff completion rate
        if staff_complete < total_orgs * 0.5:
            recommendations.append(
                f"Prioritize Staff survey collection: Only {staff_complete} responses received"
            )

        # Overall completion
        total_expected = total_orgs * 3
        total_complete = ceo_complete + tech_complete + staff_complete
        if total_complete < total_expected * 0.75:
            recommendations.append(
                f"Overall survey completion is {round((total_complete/total_expected)*100)}% - target 75%+ for robust analysis"
            )

        if not recommendations:
            recommendations.append(
                "Strong survey completion rates across all categories - continue current outreach efforts"
            )

        return recommendations

    # Utility Methods

    def _generate_aggregate_summary(
        self, maturity_assessment: Dict[str, Any], ai_insights: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate an executive summary that consolidates insights from all dimensions.

        Args:
            maturity_assessment: Maturity assessment with dimension scores
            ai_insights: AI insights with dimension summaries (optional)

        Returns:
            A comprehensive 5-7 sentence summary (~600 characters) highlighting:
            - Overall organizational maturity
            - 2-3 key strengths with specific scores
            - 2-3 critical gaps requiring attention
            - Strategic priorities and recommendations
            - Implementation timeline or next steps
        """
        overall_score = maturity_assessment.get("overall_score", 0)
        maturity_level = maturity_assessment.get("maturity_level", "Unknown")
        variance_analysis = maturity_assessment.get("variance_analysis", {})

        if not variance_analysis:
            return "No dimension data available for analysis."

        # Collect dimension scores
        dimension_scores = {
            dim: analysis["weighted_score"]
            for dim, analysis in variance_analysis.items()
            if "weighted_score" in analysis
        }

        if not dimension_scores:
            return "No dimension scores available for analysis."

        # Identify strengths (top 2 highest scoring dimensions)
        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
        strengths = sorted_dimensions[:2]
        gaps = sorted_dimensions[-2:]

        # Build context for AI
        dimension_summaries = []
        for dim, score in sorted_dimensions:
            level = self._get_maturity_level_name(score)
            summary_line = f"{dim}: {level} ({score:.1f}/5.0)"

            # Add AI summary if available
            if ai_insights and "dimensions" in ai_insights:
                dim_insights = ai_insights["dimensions"].get(dim, {})
                if "summary" in dim_insights and dim_insights["summary"]:
                    summary_line += f" - {dim_insights['summary']}"

            dimension_summaries.append(summary_line)

        # Create prompt for aggregate summary with expanded requirements
        prompt = f"""Based on these technology maturity assessments for a nonprofit organization, create a comprehensive 5-7 sentence executive summary (~600 characters):

Overall Score: {overall_score:.1f}/5.0 ({maturity_level})

Dimension Assessments:
{chr(10).join(dimension_summaries)}

Requirements:
- Paragraph 1 (2 sentences): Overall assessment and maturity characterization
- Paragraph 2 (2-3 sentences): Key strengths with specific dimension scores and what's working well (mention: {strengths[0][0]} at {strengths[0][1]:.1f} and {strengths[1][0]} at {strengths[1][1]:.1f})
- Paragraph 3 (2 sentences): Critical gaps with specific dimension scores and business impact (mention: {gaps[0][0]} at {gaps[0][1]:.1f} and {gaps[1][0]} at {gaps[1][1]:.1f})
- Final sentence: Top strategic priority with actionable next step

Length: 500-600 characters (5-7 sentences)
Tone: Professional, executive-level, actionable
Format: Three paragraphs separated by line breaks

Executive Summary:"""

        # Use existing AI infrastructure to generate
        if self.ai_analyzer:
            try:
                # Generate summary with AI - increased max_tokens for longer output
                response = self.ai_analyzer.client.chat.completions.create(
                    model=self.ai_analyzer.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert technology consultant creating comprehensive executive summaries for nonprofit organizations. Provide detailed, actionable insights in 5-7 sentences organized into three paragraphs."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=400  # Increased from 150 to accommodate longer summary
                )

                summary = response.choices[0].message.content.strip()

                # Remove quotes if LLM added them
                if summary.startswith('"') and summary.endswith('"'):
                    summary = summary[1:-1]
                if summary.startswith("'") and summary.endswith("'"):
                    summary = summary[1:-1]

                # Consolidate to target length if needed (increased from 200 to 600)
                if len(summary) > 650:
                    summary = self.ai_analyzer.consolidate_text(summary, max_chars=600)

                return summary
            except Exception as e:
                print(f"Error generating aggregate summary with AI: {e}")
                # Fall through to fallback

        # Fallback: construct basic summary without AI (expanded version)
        summary_parts = []

        # Overall assessment
        summary_parts.append(
            f"The organization demonstrates {maturity_level.lower()} technology maturity "
            f"with an overall score of {overall_score:.1f}/5.0"
        )

        # Strengths
        if strengths:
            summary_parts.append(
                f"Strong performance in {strengths[0][0]} ({strengths[0][1]:.1f}) "
                f"and {strengths[1][0]} ({strengths[1][1]:.1f}) provides a solid operational foundation, "
                f"demonstrating effective practices in these critical areas"
            )

        # Gaps
        if gaps:
            summary_parts.append(
                f"However, critical gaps in {gaps[0][0]} ({gaps[0][1]:.1f}) "
                f"and {gaps[1][0]} ({gaps[1][1]:.1f}) present significant risks and require immediate attention "
                f"to prevent operational challenges and ensure sustainable growth"
            )

        # Strategic recommendation with implementation guidance
        if overall_score < 2.5:
            summary_parts.append(
                "Top Priority: Establish foundational technology systems and build core technical capacity "
                "through systematic investment in infrastructure, training, and standardized processes"
            )
        elif overall_score < 3.5:
            summary_parts.append(
                "Top Priority: Focus on system integration and process optimization while addressing "
                "identified gaps through targeted improvements and cross-functional collaboration"
            )
        else:
            summary_parts.append(
                "Top Priority: Pursue strategic innovation and advanced capabilities by leveraging "
                "existing strengths while continuously monitoring and improving lower-performing areas"
            )

        return ". ".join(summary_parts) + "."

    def _get_maturity_level_name(self, score: float) -> str:
        """Get maturity level name for a given score."""
        if score < 2.0:
            return "Building (Early)"
        elif score < 2.5:
            return "Building (Late)"
        elif score < 3.5:
            return "Emerging"
        elif score < 4.5:
            return "Thriving (Early)"
        else:
            return "Thriving (Advanced)"

    def _get_answer_text(self, value: Any, question_info: Dict) -> str:
        """Get answer text from answer key lookup."""
        if not question_info or "answer_keys" not in question_info:
            return str(value)

        value_str = str(value).strip()
        if value_str.isdigit():
            answer_num = int(value_str)
            if 1 <= answer_num <= 7:
                answer_text = question_info["answer_keys"].get(answer_num, "")
                if answer_text:
                    return answer_text

        return str(value)

    def generate_feedback_summary(self) -> Optional[str]:
        """
        Generate AI-powered summary of all free text feedback for the home page.

        Returns:
            Summary string or None if AI not available
        """
        if not self.enable_ai or not self.ai_analyzer:
            return None

        try:
            # Collect all free text responses across all organizations
            all_responses = []

            # Get all organization names from Intake
            intake_data = self.sheet_data.get("Intake", [])
            org_names = [
                row.get("Organization Name:")
                for row in intake_data
                if row.get("Organization Name:")
            ]

            for org_name in org_names:
                free_text = extract_free_text_responses(self.sheet_data, org_name)

                for dimension, responses in free_text.items():
                    for response in responses:
                        all_responses.append(
                            {"organization": org_name, "dimension": dimension, **response}
                        )

            if not all_responses:
                return "No qualitative feedback available for analysis."

            # Generate AI summary
            summary = self.ai_analyzer.summarize_all_feedback(all_responses)
            return summary

        except Exception as e:
            print(f"Error generating feedback summary: {e}")
            return None
