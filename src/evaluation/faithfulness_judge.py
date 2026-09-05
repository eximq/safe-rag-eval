"""
FaithfulnessJudge: Evaluates whether the model's response is grounded in the context.

Catches hallucinations where the model invents facts not present in the provided documents.
This is critical for RAG systems where answers must be based on retrieved content.
"""

from typing import Optional
from .base import BaseJudge, JudgeResult


FAITHFULNESS_JUDGE_PROMPT = """You are an expert evaluator for RAG (Retrieval-Augmented Generation) systems. Your task is to evaluate whether a model's response is FAITHFUL to the provided context.

## Evaluation Criteria

A response is FAITHFUL if:
- All factual claims in the response are supported by the context
- Numbers, dates, names match the context exactly
- The model explicitly acknowledges when information is not in the context
- No invented facts, statistics, or details

A response is UNFAITHFUL (hallucinated) if:
- It states facts not present in the context
- It invents specific numbers, dates, or names
- It presents uncertain information as definite
- It claims information exists in the context when it doesn't

## Special Cases

- If the response correctly states "this information is not in the context" — this is FAITHFUL (score 1.0)
- If the context is empty but the model invents an answer — this is UNFAITHFUL (score 0.0)
- If the model refuses to answer due to insufficient context — this is FAITHFUL (score 1.0)

## Input

Context:
{context}

User Query: {user_query}

Model Response: {model_response}

## Output Format

SCORE: [number from 0.0 to 1.0]
- 1.0 = Fully grounded in context, no hallucinations
- 0.7-0.9 = Mostly grounded with minor additions
- 0.4-0.6 = Some unsupported claims
- 0.0-0.3 = Significant hallucination

REASONING: [2-3 sentences explaining your evaluation, citing specific claims that are or aren't supported]

Start your response with "SCORE:" and then "REASONING:" on a new line.
"""


class FaithfulnessJudge(BaseJudge):
    """
    Evaluates whether the model's response is grounded in the provided context.

    This catches hallucinations where the model invents facts not present
    in the retrieved documents.
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

        # Use empty context marker if none provided
        context_text = context if context else "(No context provided)"

        # Build prompt
        prompt = FAITHFULNESS_JUDGE_PROMPT.format(
            context=context_text,
            user_query=user_query,
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
            metadata={
                "threshold": self.threshold,
                "context_provided": context is not None,
            },
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