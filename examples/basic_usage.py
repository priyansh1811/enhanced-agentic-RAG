"""Basic usage example for Archon."""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import Archon


def main():
    """Basic usage example."""
    print("=== Archon Basic Usage Example ===\n")
    
    # Initialize Archon
    archon = Archon()
    
    # Set up the system
    print("Setting up Archon...")
    archon.setup()
    print("Setup complete!\n")
    
    # Example questions
    questions = [
        "What is Microsoft's revenue trend over the last 2 years?",
        "What are the main risks mentioned in Microsoft's annual report?",
        "How has Microsoft's cloud business performed recently?",
        "What is Microsoft's strategy for AI and machine learning?"
    ]
    
    # Ask questions
    for i, question in enumerate(questions, 1):
        print(f"Question {i}: {question}")
        print("-" * 50)
        
        try:
            result = archon.analyze(question)
            
            if result.get('clarification_question'):
                print(f"Clarification needed: {result['clarification_question']}")
            else:
                print(f"Response: {result.get('response', 'No response generated')}")
                
                # Show execution steps
                steps = result.get('execution_steps', [])
                if steps:
                    print(f"\nExecution steps ({len(steps)}):")
                    for j, step in enumerate(steps, 1):
                        print(f"  {j}. {step['tool']}: {step['query'][:50]}...")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
