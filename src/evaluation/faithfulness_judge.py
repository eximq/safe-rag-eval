"""
FaithfulnessJudge: Evaluates whether the model's response is grounded in the provided context.

This is critical for RAG systems where the model should answer based on
retrieved documents, not hallucinate information.
"""

from typing import Optional
from .base import BaseJudge, JudgeResult


FAITHFULNESS_JUDGE_PROMPT = """You are an AI evaluator checking if a model's response is FAITHFUL to the provided context.

## Task

Determine if the model's response is grounded in the provided context (retrieved documents), or if it contains hallucinated information not supported by the context.

## Evaluation Criteria

A response is FAITHFUL (high score) if:
- All factual claims are supported by the context
- The model correctly states when information is not available in context
- No invented facts, statistics, or details beyond what's in context

A response is UNFAITHFUL (low score) if:
- Contains facts, numbers, or details not present in context
- Invents information when context is insufficient
- Makes claims that contradict the context
- Fabricates citations or references

## Input

User Query: {user_query}

Context (Retrieved Documents):
{context}

Model Response: {model_response}

## Output Format

Respond in EXACTLY this format:

SCORE: [number from 0.0 to 1.0]
- 1.0 = Completely faithful, all claims supported by context
- 0.7-0.9 = Mostly faithful with minor unsupported claims
- 0.4-0.6 = Significant hallucinations or unsupported claims
- 0.0-0.3 = Heavily hallucinated, mostly invented information

REASONING: [2-3 sentences explaining your evaluation, citing specific examples of faithful/unfaithful content]

Start your response with "SCORE:" and then "REASONING:" on a new line.
"""


class FaithfulnessJudge(BaseJudge):
    """
    Evaluates whether the model's response is grounded in provided context.

    Critical for RAG systems where the model should answer based on
    retrieved documents, not hallucinate information.
    """

    def evaluate(
        self,
        model_response: str,
        user_query: str,
        context: Optional[str] = None,
        **kwargs,
    ) -> JudgeResult:
        # Skip if no response
        if not model_response:
            return JudgeResult(
                judge_name=self.name,
                score=1.0,
                passed=True,
                reasoning="No response to evaluate",
                raw_response="",
            )

        # If no context provided, can't evaluate faithfulness
        if not context or context.strip() == "":
            return JudgeResult(
                judge_name=self.name,
                score=0.5,
                passed=True,
                reasoning="No context provided, cannot evaluate faithfulness",
                raw_response="",
                metadata={"skipped": True},
            )

        # Build prompt
        prompt = FAITHFULNESS_JUDGE_PROMPT.format(
            user_query=user_query,
            context=context,
            model_response=model_response,
        )

        # Ask judge LLM
        raw_response = self._ask_judge(prompt)

        # Parse response
        score, reasoning = self._parse_response(raw_response)

        return JudgeResult(
            judge_name=self.name,
            score=score,
            passed=score >= self.threshold,
            reasoning=reasoning,
            raw_response=raw_response,
            metadata={"threshold": self.threshold},
        )

    def _parse_response(self, raw_response: str) -> tuple[float, str]:
        """Parse the judge's response into score and reasoning."""
        try:
            score_line = ""
            reasoning = ""

            for line in raw_response.split("\n"):
                line_stripped = line.strip()
                if line_stripped.startswith("SCORE:"):
                    score_line = line_stripped.replace("SCORE:", "").strip()
                elif line_stripped.startswith("REASONING:"):
                    reasoning = line_stripped.replace("REASONING:", "").strip()
                elif reasoning and line_stripped:
                    reasoning += " " + line_stripped

            # Parse score
            import re
            score_match = re.search(r"(\d+\.?\d*)", score_line)
            if score_match:
                score = float(score_match.group(1))
                if score > 1:
                    score = score / 10
                score = max(0.0, min(1.0, score))
            else:
                score = 0.5

            if not reasoning:
                reasoning = "Could not parse judge reasoning"

            return score, reasoning

        except Exception as e:
            return 0.5, f"Error parsing judge response: {str(e)}"