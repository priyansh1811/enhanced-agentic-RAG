"""Main entry point for Archon."""

import os
import sys
import argparse
import json
from typing import Optional

from .config import get_settings
from .data.acquisition import DataAcquisition
from .data.processor import DocumentProcessor
from .data.storage import VectorStore, MemoryStore
from .agents.specialist_agents import SpecialistAgents
from .evaluation.evaluator import Evaluator
from .evaluation.red_team import RedTeamTester


class Archon:
    """Main Archon agent class."""
    
    def __init__(self):
        self.settings = get_settings()
        self.vector_store = None
        self.memory_store = None
        self.specialist_agents = None
        self.evaluator = Evaluator()
        self.red_team_tester = RedTeamTester()
    
    def setup(self, force_rebuild: bool = False):
        """Set up the Archon system."""
        print("=== Archon Setup ===")
        
        # Initialize memory store
        self.memory_store = MemoryStore()
        print("✓ Memory store initialized")
        
        # Set up vector store
        self.vector_store = VectorStore()
        self.vector_store.create_collection()
        print("✓ Vector store initialized")
        
        # Check if we need to rebuild the knowledge base
        enriched_chunks_file = "data/processed/enriched_chunks.json"
        
        if force_rebuild or not os.path.exists(enriched_chunks_file):
            print("Building knowledge base...")
            self._build_knowledge_base()
        else:
            print("Loading existing knowledge base...")
            self._load_knowledge_base()
        
        # Initialize specialist agents
        db_path = "data/raw/sample_financial_data.csv"
        if not os.path.exists(db_path):
            print("Creating sample financial dataset...")
            data_acquisition = DataAcquisition()
            data_acquisition.create_sample_dataset()
        
        self.specialist_agents = SpecialistAgents(self.vector_store, db_path)
        print("✓ Specialist agents initialized")
        
        print("=== Setup Complete ===")
    
    def _build_knowledge_base(self):
        """Build the knowledge base from scratch."""
        # Download SEC filings
        print("  - Downloading SEC filings...")
        data_acquisition = DataAcquisition()
        download_results = data_acquisition.download_sec_filings()
        
        # Process documents
        print("  - Processing documents...")
        processor = DocumentProcessor()
        file_paths = download_results["file_paths"]
        
        if file_paths:
            enriched_chunks = processor.process_documents(
                file_paths, 
                "data/processed/enriched_chunks.json"
            )
        else:
            print("  - No files downloaded, creating sample data...")
            # Create some sample enriched chunks for testing
            enriched_chunks = self._create_sample_chunks()
        
        # Store in vector database
        print("  - Storing in vector database...")
        self.vector_store.add_documents(enriched_chunks)
        
        print(f"✓ Knowledge base built with {len(enriched_chunks)} chunks")
    
    def _load_knowledge_base(self):
        """Load existing knowledge base."""
        import json
        
        with open("data/processed/enriched_chunks.json", 'r', encoding='utf-8') as f:
            enriched_chunks = json.load(f)
        
        # Store in vector database
        self.vector_store.add_documents(enriched_chunks)
        print(f"✓ Knowledge base loaded with {len(enriched_chunks)} chunks")
    
    def _create_sample_chunks(self):
        """Create sample enriched chunks for testing."""
        return [
            {
                "content": "Microsoft Corporation is a multinational technology company that develops, manufactures, licenses, supports and sells computer software, consumer electronics, personal computers, and related services.",
                "metadata": {"source": "sample"},
                "enriched_metadata": {
                    "summary": "Microsoft is a global technology company focused on software and services.",
                    "keywords": ["Microsoft", "technology", "software", "services"],
                    "hypothetical_questions": ["What does Microsoft do?", "What is Microsoft's business model?"],
                    "table_summary": None
                },
                "source_file": "sample_data.txt"
            }
        ]
    
    def analyze(self, question: str) -> dict:
        """Analyze a question using the specialist agents."""
        if not self.specialist_agents:
            raise RuntimeError("Archon not set up. Call setup() first.")
        
        return self.specialist_agents.analyze_request(question)
    
    def evaluate(self, test_questions: list) -> dict:
        """Evaluate the agent's performance."""
        if not self.specialist_agents:
            raise RuntimeError("Archon not set up. Call setup() first.")
        
        def agent_func(question):
            result = self.analyze(question)
            return result.get("response", "No response generated")
        
        return self.evaluator.performance_evaluation(agent_func, test_questions)
    
    def red_team_test(self, num_questions: int = 5) -> dict:
        """Run red team testing."""
        if not self.specialist_agents:
            raise RuntimeError("Archon not set up. Call setup() first.")
        
        def agent_func(question):
            result = self.analyze(question)
            return result.get("response", "No response generated")
        
        adversarial_questions = self.red_team_tester.generate_adversarial_questions(
            num_questions=num_questions
        )
        
        return self.red_team_tester.test_agent_robustness(agent_func, adversarial_questions)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Archon: The Proactive & Adaptive Analyst")
    parser.add_argument("--setup", action="store_true", help="Set up the Archon system")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild of knowledge base")
    parser.add_argument("--question", type=str, help="Ask a question")
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation tests")
    parser.add_argument("--red-team", action="store_true", help="Run red team testing")
    parser.add_argument("--interactive", action="store_true", help="Start interactive mode")
    
    args = parser.parse_args()
    
    # Initialize Archon
    archon = Archon()
    
    if args.setup:
        archon.setup(force_rebuild=args.rebuild)
    
    elif args.question:
        if not archon.specialist_agents:
            print("Setting up Archon...")
            archon.setup()
        
        result = archon.analyze(args.question)
        print(f"\nQuestion: {args.question}")
        print(f"Response: {result.get('response', 'No response generated')}")
        
        if result.get('clarification_question'):
            print(f"Clarification needed: {result['clarification_question']}")
    
    elif args.evaluate:
        if not archon.specialist_agents:
            print("Setting up Archon...")
            archon.setup()
        
        test_questions = [
            "What is Microsoft's revenue trend over the last 2 years?",
            "What are the main risks mentioned in Microsoft's annual report?",
            "How has Microsoft's cloud business performed recently?"
        ]
        
        print("Running evaluation...")
        results = archon.evaluate(test_questions)
        print(f"\nEvaluation Results:")
        print(json.dumps(results, indent=2))
    
    elif args.red_team:
        if not archon.specialist_agents:
            print("Setting up Archon...")
            archon.setup()
        
        print("Running red team testing...")
        results = archon.red_team_test()
        print(f"\nRed Team Results:")
        print(f"Robustness Rate: {results['robustness_rate']}")
        print(f"Robust Responses: {results['robust_responses']}/{results['total_tests']}")
    
    elif args.interactive:
        if not archon.specialist_agents:
            print("Setting up Archon...")
            archon.setup()
        
        print("\n=== Archon Interactive Mode ===")
        print("Ask me anything about Microsoft's financial performance!")
        print("Type 'quit' to exit.\n")
        
        while True:
            try:
                question = input("You: ").strip()
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if question:
                    result = archon.analyze(question)
                    print(f"\nArchon: {result.get('response', 'No response generated')}")
                    
                    if result.get('clarification_question'):
                        print(f"\nClarification: {result['clarification_question']}")
                    
                    print()
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\nGoodbye!")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
