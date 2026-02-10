"""BAQI AI CrewAI multi-agent system for investment recommendations."""

import json
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task, LLM

from app.agents.tools.transaction_tool import TransactionQueryTool
from app.agents.tools.psx_tool import PSXPredictionTool
from app.agents.tools.halal_screening_tool import HalalScreeningTool
from app.agents.tools.portfolio_tool import PortfolioReadTool
from app.agents.models.output_schemas import InvestmentRecommendationOutput
from app.config import settings

CONFIG_DIR = Path(__file__).parent / "config"


def _load_yaml(filename: str) -> dict:
    with open(CONFIG_DIR / filename) as f:
        return yaml.safe_load(f)


class BaqiCrew:
    """Assembles and runs the 6-agent BAQI AI investment crew."""

    def __init__(self):
        self.agents_config = _load_yaml("agents.yaml")
        self.tasks_config = _load_yaml("tasks.yaml")
        self.llm = LLM(
            model="anthropic/claude-sonnet-4-5-20250929",
            max_tokens=4096,
            api_key=settings.anthropic_api_key,
        )

    def _make_agent(self, key: str, tools: list = None) -> Agent:
        cfg = self.agents_config[key]
        return Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            tools=tools or [],
            llm=self.llm,
            verbose=True,
            max_iter=10,
        )

    def _make_task(self, key: str, agent: Agent, context_tasks: list = None, **kwargs) -> Task:
        cfg = self.tasks_config[key]
        # Interpolate variables into description
        description = cfg["description"]
        for k, v in kwargs.items():
            description = description.replace("{" + k + "}", str(v))
        return Task(
            description=description,
            expected_output=cfg["expected_output"],
            agent=agent,
            context=context_tasks or [],
        )

    def run(self, inputs: dict) -> dict:
        """
        Run the full recommendation pipeline.

        inputs: {
            user_id, income, age, quiz_answers, risk_profile,
            baqi_amount, halal_preference, spending_data
        }
        """
        # --- Create agents ---
        spending_agent = self._make_agent("spending_analyzer", [TransactionQueryTool()])
        risk_agent = self._make_agent("risk_profiler")
        market_agent = self._make_agent("market_sentiment")
        halal_agent = self._make_agent("halal_compliance", [HalalScreeningTool()])
        investment_agent = self._make_agent("investment_agent", [PSXPredictionTool()])

        # --- Pre-compute some values for task inputs ---
        # Get default risk allocation based on profile
        risk_profile = inputs.get("risk_profile", "moderate")
        allocations = {
            "conservative": {"equity_pct": 20, "fixed_income_pct": 60, "mutual_fund_pct": 20},
            "moderate": {"equity_pct": 40, "fixed_income_pct": 30, "mutual_fund_pct": 30},
            "aggressive": {"equity_pct": 60, "fixed_income_pct": 10, "mutual_fund_pct": 30},
        }
        alloc = allocations.get(risk_profile, allocations["moderate"])

        # Get PSX predictions and halal data for the recommendation task
        psx_tool = PSXPredictionTool()
        psx_data = psx_tool._run("ALL")
        halal_tool = HalalScreeningTool()
        candidate_tickers = "LUCK,SYS,ENGRO,FFC,OGDC,PPL,MARI,SEARL,TRG,EFERT,FCCL,MEBL,UNITY"
        halal_data = halal_tool._run(candidate_tickers)

        # --- Create tasks ---
        t1 = self._make_task("analyze_spending", spending_agent,
            spending_data=inputs.get("spending_data", "{}"),
            income=inputs.get("income", 150000))

        t2 = self._make_task("assess_risk", risk_agent, context_tasks=[t1],
            age=inputs.get("age", 28),
            income=inputs.get("income", 150000),
            quiz_answers=inputs.get("quiz_answers", "[3,3,3,3,3]"),
            risk_profile=risk_profile,
            baqi_amount=inputs.get("baqi_amount", 15000))

        t3 = self._make_task("analyze_market", market_agent)

        t4 = self._make_task("screen_halal", halal_agent, context_tasks=[t3],
            halal_preference=inputs.get("halal_preference", True),
            candidate_tickers=candidate_tickers)

        t5 = self._make_task("generate_recommendation", investment_agent,
            context_tasks=[t1, t2, t3, t4],
            baqi_amount=inputs.get("baqi_amount", 15000),
            risk_profile=risk_profile,
            equity_pct=alloc["equity_pct"],
            fixed_income_pct=alloc["fixed_income_pct"],
            mutual_fund_pct=alloc["mutual_fund_pct"],
            halal_preference=inputs.get("halal_preference", True),
            market_outlook="bullish",
            top_sectors="Cement, Technology, Oil & Gas, Fertilizer, Islamic Banking",
            psx_predictions=psx_data,
            halal_stocks=halal_data)

        # --- Assemble and run crew ---
        crew = Crew(
            agents=[spending_agent, risk_agent, market_agent, halal_agent, investment_agent],
            tasks=[t1, t2, t3, t4, t5],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        # Try to parse the final task output as JSON
        raw = str(result.raw) if hasattr(result, 'raw') else str(result)
        output = self._extract_json(raw)

        return output

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from LLM output that may contain markdown fences or prose."""
        # Try direct parse first
        try:
            return json.loads(text.strip())
        except (json.JSONDecodeError, ValueError):
            pass

        # Try extracting from markdown code fence
        import re
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except (json.JSONDecodeError, ValueError):
                pass

        # Try finding first { ... } block
        start = text.find('{')
        if start != -1:
            depth = 0
            for i in range(start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i + 1])
                        except (json.JSONDecodeError, ValueError):
                            break

        return {"raw_output": text}
