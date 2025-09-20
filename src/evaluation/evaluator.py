"""Evaluation module for testing agent performance."""

import time
import json
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

from ..config import get_settings


class EvaluationResult(BaseModel):
    """Result of an evaluation."""
    question: str = Field(description="The test question")
    answer: str = Field(description="The agent's answer")
    relevance_score: int = Field(description="Relevance score from 1-5")
    accuracy_score: int = Field(description="Accuracy score from 1-5")
    completeness_score: int = Field(description="Completeness score from 1-5")
    overall_score: float = Field(description="Overall score (average)")
    reasoning: str = Field(description="Reasoning for the scores")


class Evaluator:
    """Evaluates agent performance using LLM-as-a-judge."""
    
    def __init__(self):
        self.settings = get_settings()
        self.evaluator_llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=self.settings.openai_api_key
        ).with_structured_output(EvaluationResult)
    
    def evaluate_response(
        self, 
        question: str, 
        answer: str,
        context: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate a single response using LLM-as-a-judge.
        
        Args:
            question: The original question
            answer: The agent's response
            context: Optional context for evaluation
            
        Returns:
            Evaluation result with scores and reasoning
        """
        prompt = f"""
        Evaluate the following Q&A pair as an expert financial analyst.
        
        Question: {question}
        Answer: {answer}
        {f"Context: {context}" if context else ""}
        
        Rate the answer on three dimensions (1-5 scale):
        1. Relevance: How well does the answer address the question?
        2. Accuracy: How accurate and factually correct is the information?
        3. Completeness: How comprehensive and thorough is the response?
        
        Consider:
        - Does the answer directly address what was asked?
        - Are the facts and figures accurate?
        - Is the analysis thorough and well-reasoned?
        - Does it provide actionable insights?
        - Is it well-structured and clear?
        
        Provide specific reasoning for each score.
        """
        
        result = self.evaluator_llm.invoke(prompt)
        
        # Calculate overall score
        result.overall_score = (
            result.relevance_score + 
            result.accuracy_score + 
            result.completeness_score
        ) / 3
        
        return result
    
    def evaluate_batch(
        self, 
        test_cases: List[Dict[str, str]]
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple test cases.
        
        Args:
            test_cases: List of dicts with 'question' and 'answer' keys
            
        Returns:
            List of evaluation results
        """
        results = []
        
        for i, test_case in enumerate(test_cases):
            print(f"Evaluating test case {i+1}/{len(test_cases)}")
            
            result = self.evaluate_response(
                question=test_case["question"],
                answer=test_case["answer"],
                context=test_case.get("context")
            )
            
            results.append(result)
            
            print(f"  - Overall Score: {result.overall_score:.2f}/5")
        
        return results
    
    def calculate_metrics(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """
        Calculate aggregate metrics from evaluation results.
        
        Args:
            results: List of evaluation results
            
        Returns:
            Dictionary with aggregate metrics
        """
        if not results:
            return {}
        
        total_results = len(results)
        
        avg_relevance = sum(r.relevance_score for r in results) / total_results
        avg_accuracy = sum(r.accuracy_score for r in results) / total_results
        avg_completeness = sum(r.completeness_score for r in results) / total_results
        avg_overall = sum(r.overall_score for r in results) / total_results
        
        # Count high-quality responses (overall score >= 4)
        high_quality_count = sum(1 for r in results if r.overall_score >= 4)
        high_quality_rate = high_quality_count / total_results
        
        # Count low-quality responses (overall score < 3)
        low_quality_count = sum(1 for r in results if r.overall_score < 3)
        low_quality_rate = low_quality_count / total_results
        
        return {
            "total_tests": total_results,
            "avg_relevance": round(avg_relevance, 2),
            "avg_accuracy": round(avg_accuracy, 2),
            "avg_completeness": round(avg_completeness, 2),
            "avg_overall": round(avg_overall, 2),
            "high_quality_rate": round(high_quality_rate, 2),
            "low_quality_rate": round(low_quality_rate, 2)
        }
    
    def performance_evaluation(
        self, 
        agent_func, 
        test_questions: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate agent performance including speed and cost.
        
        Args:
            agent_func: Function that takes a question and returns an answer
            test_questions: List of test questions
            
        Returns:
            Performance evaluation results
        """
        results = []
        total_time = 0
        total_tokens = 0
        
        for i, question in enumerate(test_questions):
            print(f"Testing question {i+1}/{len(test_questions)}")
            
            start_time = time.time()
            try:
                response = agent_func(question)
                end_time = time.time()
                
                response_time = end_time - start_time
                total_time += response_time
                
                # Estimate token usage (rough approximation)
                estimated_tokens = len(question + str(response)) // 4
                total_tokens += estimated_tokens
                
                # Evaluate the response
                evaluation = self.evaluate_response(question, str(response))
                
                results.append({
                    "question": question,
                    "answer": str(response),
                    "response_time": response_time,
                    "estimated_tokens": estimated_tokens,
                    "evaluation": evaluation.dict()
                })
                
                print(f"  - Response time: {response_time:.2f}s")
                print(f"  - Overall score: {evaluation.overall_score:.2f}/5")
                
            except Exception as e:
                print(f"  - Error: {e}")
                results.append({
                    "question": question,
                    "answer": f"Error: {str(e)}",
                    "response_time": 0,
                    "estimated_tokens": 0,
                    "evaluation": None
                })
        
        # Calculate aggregate metrics
        successful_results = [r for r in results if r["evaluation"] is not None]
        
        if successful_results:
            avg_response_time = total_time / len(successful_results)
            avg_tokens = total_tokens / len(successful_results)
            
            # Calculate evaluation metrics
            evaluations = [r["evaluation"] for r in successful_results]
            metrics = self.calculate_metrics(evaluations)
            
            return {
                "total_questions": len(test_questions),
                "successful_responses": len(successful_results),
                "avg_response_time": round(avg_response_time, 2),
                "avg_tokens_per_response": round(avg_tokens, 0),
                "total_tokens": total_tokens,
                "evaluation_metrics": metrics
            }
        else:
            return {
                "total_questions": len(test_questions),
                "successful_responses": 0,
                "error": "No successful responses to evaluate"
            }
