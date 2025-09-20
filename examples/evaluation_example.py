"""Evaluation example for Archon."""

import sys
import os
import json

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import Archon


def main():
    """Evaluation example."""
    print("=== Archon Evaluation Example ===\n")
    
    # Initialize Archon
    archon = Archon()
    
    # Set up the system
    print("Setting up Archon...")
    archon.setup()
    print("Setup complete!\n")
    
    # Test questions for evaluation
    test_questions = [
        "What is Microsoft's total revenue for 2023?",
        "How has Microsoft's revenue grown over the last 3 years?",
        "What are the main business segments of Microsoft?",
        "What risks does Microsoft face in the cloud computing market?",
        "How has Microsoft's AI business performed recently?"
    ]
    
    print("Running evaluation...")
    evaluation_results = archon.evaluate(test_questions)
    
    print("\n=== Evaluation Results ===")
    print(f"Total Questions: {evaluation_results['total_questions']}")
    print(f"Successful Responses: {evaluation_results['successful_responses']}")
    print(f"Average Response Time: {evaluation_results['avg_response_time']}s")
    print(f"Average Tokens per Response: {evaluation_results['avg_tokens_per_response']}")
    
    if 'evaluation_metrics' in evaluation_results:
        metrics = evaluation_results['evaluation_metrics']
        print(f"\nQuality Metrics:")
        print(f"  Average Relevance: {metrics['avg_relevance']}/5")
        print(f"  Average Accuracy: {metrics['avg_accuracy']}/5")
        print(f"  Average Completeness: {metrics['avg_completeness']}/5")
        print(f"  Overall Score: {metrics['avg_overall']}/5")
        print(f"  High Quality Rate: {metrics['high_quality_rate']}")
        print(f"  Low Quality Rate: {metrics['low_quality_rate']}")
    
    # Run red team testing
    print("\n=== Red Team Testing ===")
    red_team_results = archon.red_team_test(num_questions=5)
    
    print(f"Total Tests: {red_team_results['total_tests']}")
    print(f"Robust Responses: {red_team_results['robust_responses']}")
    print(f"Potentially Problematic: {red_team_results['potentially_problematic']}")
    print(f"Clearly Problematic: {red_team_results['clearly_problematic']}")
    print(f"Robustness Rate: {red_team_results['robustness_rate']}")
    
    # Save results
    results = {
        "evaluation": evaluation_results,
        "red_team": red_team_results
    }
    
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to evaluation_results.json")


if __name__ == "__main__":
    main()
