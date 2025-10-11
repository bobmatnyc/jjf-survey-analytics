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
            except Exception as e:
                print(f"Warning: AI analysis failed for {org_name}: {e}")

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

        # Count completed surveys
        ceo_complete = len([r for r in ceo_data if r.get("Date")])
        tech_complete = len([r for r in tech_data if r.get("Date")])
        staff_complete = len([r for r in staff_data if r.get("Date")])

        # Count fully complete organizations
        orgs_with_ceo = {r.get("CEO Organization") for r in ceo_data if r.get("Date")}
        orgs_with_tech = {r.get("Organization") for r in tech_data if r.get("Date")}
        orgs_with_staff = {r.get("Organization") for r in staff_data if r.get("Date")}
        fully_complete = len(orgs_with_ceo & orgs_with_tech & orgs_with_staff)

        return {
            "total_organizations": total_orgs,
            "total_surveys_expected": total_orgs * 3,
            "surveys_completed": ceo_complete + tech_complete + staff_complete,
            "surveys_pending": (total_orgs * 3) - (ceo_complete + tech_complete + staff_complete),
            "completion_percentage": (
                round(((ceo_complete + tech_complete + staff_complete) / (total_orgs * 3)) * 100)
                if total_orgs > 0
                else 0
            ),
            "fully_complete_orgs": fully_complete,
            "ceo_complete": ceo_complete,
            "tech_complete": tech_complete,
            "staff_complete": staff_complete,
            "ceo_percentage": round((ceo_complete / total_orgs) * 100) if total_orgs > 0 else 0,
            "tech_percentage": round((tech_complete / total_orgs) * 100) if total_orgs > 0 else 0,
            "staff_percentage": round((staff_complete / total_orgs) * 100) if total_orgs > 0 else 0,
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
