"""Advanced reasoning engine with multi-step workflow."""

import json
from typing import List, Dict, Any, Optional, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END

from ..config import get_settings


class AgentState(TypedDict):
    """State for the agent workflow."""
    original_request: str
    clarification_question: Optional[str]
    plan: List[str]
    intermediate_steps: List[Dict[str, Any]]
    verification_history: List[Dict[str, Any]]
    final_response: Optional[str]


class ClarificationQuestion(BaseModel):
    """Structured output for clarification questions."""
    needs_clarification: bool = Field(description="Whether the request needs clarification")
    question: str = Field(description="The clarification question to ask the user")
    reasoning: str = Field(description="Why clarification is needed")


class PlanStep(BaseModel):
    """A single step in the execution plan."""
    step_number: int = Field(description="The step number")
    tool_name: str = Field(description="The name of the tool to use")
    query: str = Field(description="The query to pass to the tool")
    reasoning: str = Field(description="Why this step is needed")


class ExecutionPlan(BaseModel):
    """Complete execution plan."""
    steps: List[PlanStep] = Field(description="List of steps to execute")
    final_step: str = Field(description="Final step to synthesize results")


class VerificationResult(BaseModel):
    """Result of verification step."""
    confidence_score: int = Field(description="Confidence score from 1-5")
    is_consistent: bool = Field(description="Whether the results are internally consistent")
    is_relevant: bool = Field(description="Whether the results are relevant to the request")
    reasoning: str = Field(description="Reasoning for the verification result")


class ReasoningEngine:
    """Advanced reasoning engine with multi-step workflow."""
    
    def __init__(self, tools: List[Any]):
        self.settings = get_settings()
        self.tools = {tool.name: tool for tool in tools}
        
        # Initialize LLMs for different tasks
        self.gatekeeper_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=self.settings.openai_api_key
        ).with_structured_output(ClarificationQuestion)
        
        self.planner_llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=self.settings.openai_api_key
        ).with_structured_output(ExecutionPlan)
        
        self.auditor_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=self.settings.openai_api_key
        ).with_structured_output(VerificationResult)
        
        self.synthesizer_llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            api_key=self.settings.openai_api_key
        )
        
        # Build the workflow graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the reasoning workflow graph."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("gatekeeper", self._gatekeeper_node)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("execute_tool", self._tool_executor_node)
        workflow.add_node("verification", self._verification_node)
        workflow.add_node("synthesize", self._synthesizer_node)
        
        # Add edges
        workflow.set_entry_point("gatekeeper")
        workflow.add_edge("gatekeeper", "planner")
        workflow.add_edge("planner", "execute_tool")
        workflow.add_edge("execute_tool", "verification")
        workflow.add_conditional_edges(
            "verification",
            self._router_node,
            {
                "planner": "planner",
                "execute_tool": "execute_tool", 
                "synthesize": "synthesize",
                "end": END
            }
        )
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    def _gatekeeper_node(self, state: AgentState) -> AgentState:
        """Check if the request needs clarification."""
        print("\n-- Gatekeeper Node --")
        
        prompt = f"""
        Analyze the following user request and determine if it needs clarification.
        
        User Request: {state['original_request']}
        
        A request needs clarification if it is:
        - Vague or ambiguous
        - Missing important context
        - Too broad to answer effectively
        - Contains unclear terminology
        
        If clarification is needed, provide a specific question to ask the user.
        """
        
        result = self.gatekeeper_llm.invoke(prompt)
        
        if result.needs_clarification:
            print(f"  - Clarification needed: {result.question}")
            return {
                **state,
                "clarification_question": result.question
            }
        else:
            print("  - Request is clear, proceeding to planning")
            return state
    
    def _planner_node(self, state: AgentState) -> AgentState:
        """Create an execution plan."""
        print("\n-- Planner Node --")
        
        available_tools = list(self.tools.keys())
        
        prompt = f"""
        Create an execution plan for the following request using the available tools.
        
        User Request: {state['original_request']}
        Available Tools: {', '.join(available_tools)}
        
        Create a step-by-step plan that:
        1. Uses the most appropriate tools for the request
        2. Breaks down complex requests into manageable steps
        3. Ensures comprehensive coverage of the request
        4. Includes verification steps where needed
        
        Tool Descriptions:
        - librarian_tool: Search financial documents and SEC filings
        - analyst_sql_tool: Query structured financial data for specific numbers
        - analyst_trend_tool: Analyze trends and patterns over time
        - scout_tool: Search for recent news and live information
        """
        
        plan = self.planner_llm.invoke(prompt)
        
        # Convert plan to simple list format
        plan_steps = [f"{step.step_number}. {step.tool_name}: {step.query}" 
                     for step in plan.steps]
        plan_steps.append("FINISH")
        
        print(f"  - Created plan with {len(plan_steps)} steps")
        for step in plan_steps:
            print(f"    {step}")
        
        return {
            **state,
            "plan": plan_steps,
            "intermediate_steps": []
        }
    
    def _tool_executor_node(self, state: AgentState) -> AgentState:
        """Execute the next tool in the plan."""
        print("\n-- Tool Executor Node --")
        
        if not state.get("plan") or state["plan"][0] == "FINISH":
            print("  - No more steps to execute")
            return state
        
        # Get next step
        next_step = state["plan"][0]
        remaining_plan = state["plan"][1:]
        
        print(f"  - Executing: {next_step}")
        
        # Parse step to get tool name and query
        if ". " in next_step:
            tool_name = next_step.split(". ")[1].split(":")[0]
            query = next_step.split(": ", 1)[1] if ": " in next_step else ""
        else:
            print("  - Invalid step format, skipping")
            return {**state, "plan": remaining_plan}
        
        # Execute tool
        try:
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                result = tool.invoke(query)
                
                step_result = {
                    "tool": tool_name,
                    "query": query,
                    "result": result,
                    "status": "success"
                }
            else:
                step_result = {
                    "tool": tool_name,
                    "query": query,
                    "result": f"Tool {tool_name} not found",
                    "status": "error"
                }
        except Exception as e:
            step_result = {
                "tool": tool_name,
                "query": query,
                "result": f"Error: {str(e)}",
                "status": "error"
            }
        
        # Update state
        new_intermediate_steps = state.get("intermediate_steps", []) + [step_result]
        
        return {
            **state,
            "plan": remaining_plan,
            "intermediate_steps": new_intermediate_steps
        }
    
    def _verification_node(self, state: AgentState) -> AgentState:
        """Verify the quality of tool outputs."""
        print("\n-- Verification Node --")
        
        if not state.get("intermediate_steps"):
            print("  - No steps to verify")
            return state
        
        last_step = state["intermediate_steps"][-1]
        
        prompt = f"""
        Verify the quality of the following tool execution:
        
        Original Request: {state['original_request']}
        Tool: {last_step['tool']}
        Query: {last_step['query']}
        Result: {last_step['result']}
        
        Evaluate:
        1. Is the result relevant to the original request?
        2. Is the result internally consistent?
        3. What is your confidence in the quality (1-5 scale)?
        
        Provide a confidence score and reasoning.
        """
        
        verification = self.auditor_llm.invoke(prompt)
        
        print(f"  - Verification confidence: {verification.confidence_score}/5")
        print(f"  - Reasoning: {verification.reasoning}")
        
        verification_result = {
            "confidence_score": verification.confidence_score,
            "is_consistent": verification.is_consistent,
            "is_relevant": verification.is_relevant,
            "reasoning": verification.reasoning
        }
        
        new_verification_history = state.get("verification_history", []) + [verification_result]
        
        return {
            **state,
            "verification_history": new_verification_history
        }
    
    def _router_node(self, state: AgentState) -> str:
        """Route to the next node based on current state."""
        print("\n-- Router Node --")
        
        # Check for clarification first
        if state.get("clarification_question"):
            print("  - Decision: Clarification needed, ending workflow")
            return "end"
        
        # Check if verification failed
        if state.get("verification_history"):
            last_verification = state["verification_history"][-1]
            if last_verification["confidence_score"] < 3:
                print("  - Decision: Verification failed, replanning")
                return "planner"
        
        # Check if plan is complete
        if not state.get("plan") or state["plan"][0] == "FINISH":
            print("  - Decision: Plan complete, synthesizing")
            return "synthesize"
        else:
            print("  - Decision: More steps to execute")
            return "execute_tool"
    
    def _synthesizer_node(self, state: AgentState) -> AgentState:
        """Synthesize final response from all intermediate steps."""
        print("\n-- Synthesizer Node --")
        
        # Prepare context for synthesis
        context_parts = []
        for step in state.get("intermediate_steps", []):
            context_parts.append(f"Tool: {step['tool']}\nQuery: {step['query']}\nResult: {step['result']}\n")
        
        context = "\n".join(context_parts)
        
        prompt = f"""
        Synthesize a comprehensive response to the user's request based on the following information:
        
        Original Request: {state['original_request']}
        
        Information Gathered:
        {context}
        
        Create a well-structured, informative response that:
        1. Directly addresses the user's request
        2. Synthesizes information from multiple sources
        3. Provides clear insights and analysis
        4. Cites specific data points and sources
        5. Maintains a professional, analytical tone
        """
        
        final_response = self.synthesizer_llm.invoke(prompt).content
        
        print("  - Synthesis complete")
        
        return {
            **state,
            "final_response": final_response
        }
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """Process a user request through the complete workflow."""
        initial_state = {
            "original_request": request,
            "clarification_question": None,
            "plan": [],
            "intermediate_steps": [],
            "verification_history": [],
            "final_response": None
        }
        
        result = self.graph.invoke(initial_state)
        
        return {
            "request": request,
            "response": result.get("final_response"),
            "clarification_question": result.get("clarification_question"),
            "execution_steps": result.get("intermediate_steps", []),
            "verification_history": result.get("verification_history", [])
        }
