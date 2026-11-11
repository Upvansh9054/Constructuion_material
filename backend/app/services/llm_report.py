import json
import logging
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMDemolitionReportService:
    """Generates executive summaries, compliance audits, and circular economy buyer matching using OpenAI API."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self.api_key or self.api_key.startswith("sk-placeholder"):
                raise ValueError(
                    "OPENAI_API_KEY is not configured. Please set a valid key in backend/.env"
                )
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate_audit_summary(
        self,
        site_name: str,
        site_location: str,
        survey_notes: Optional[str],
        material_breakdown: List[Dict[str, Any]],
        total_tonnes: float,
        total_value_usd: float,
        total_carbon_offset_kg: float,
    ) -> Dict[str, str]:
        """
        Synthesizes an intelligent Demolition Material Audit Report (DMAR) using OpenAI.
        """
        # If API key is missing, return a clean structured message indicating that
        # rather than faking an AI completion
        if not self.api_key or self.api_key.startswith("sk-placeholder"):
            logger.warning("OpenAI API key missing. Returning baseline template summary.")
            return {
                "executive_summary": (
                    f"Pre-demolition material survey completed for {site_name} in {site_location}. "
                    f"A total of {total_tonnes:.2f} metric tonnes of recyclable and recoverable materials "
                    f"were identified, with an estimated secondary market value of ${total_value_usd:,.2f} "
                    f"and an embodied carbon offset potential of {total_carbon_offset_kg:,.1f} kg CO2e. "
                    f"Configure a valid OPENAI_API_KEY to activate full generative report synthesis."
                ),
                "regulatory_compliance_notes": (
                    "Standard C&D waste protocol: Ensure mandatory pre-demolition hazardous materials inspection "
                    "for asbestos-containing materials (ACMs) and lead paint before mechanical dismantling. "
                    "Segregate timber and steel at source to satisfy local landfill diversion quotas."
                ),
                "buyer_matching_insights": (
                    "High-priority streams: Concrete aggregate for local road sub-base contractors; "
                    "structural steel beams for architectural salvage and secondary electric arc furnace recyclers."
                ),
            }

        prompt = f"""
You are a senior environmental engineer and sustainable construction auditor.
Generate an executive Demolition Material Audit Report (DMAR) based on the following survey data:

Site: {site_name} ({site_location})
Surveyor Notes: {survey_notes or 'None recorded'}
Total Recoverable Mass: {total_tonnes:.2f} Metric Tonnes
Total Estimated Value: ${total_value_usd:,.2f} USD
Total Embodied Carbon Offsets: {total_carbon_offset_kg:,.1f} kg CO2e

Material Inventory Breakdown:
{json.dumps(material_breakdown, indent=2)}

Return a strict JSON object with these 3 keys:
1. "executive_summary": A professional 2-paragraph analysis highlighting recovery potential, material quality, and environmental impact.
2. "regulatory_compliance_notes": Relevant guidelines regarding source separation, handling hazards, and waste transfer certification.
3. "buyer_matching_insights": Concrete recommendations on target buyers (e.g. crushing facilities, timber salvage yards, steel mills, precast fabricators).
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert AI demolition intelligence consultant. Output valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            raw_content = response.choices[0].message.content
            return json.loads(raw_content)
        except Exception as e:
            logger.error(f"Error during OpenAI API call: {e}")
            raise


llm_report_service = LLMDemolitionReportService()
