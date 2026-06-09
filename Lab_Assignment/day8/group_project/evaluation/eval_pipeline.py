import json
import os
import sys
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ContextualRelevancyMetric, ContextualPrecisionMetric
from deepeval.test_case import LLMTestCase

# Đảm bảo có thể import thư mục src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task10_generation import generate_with_citation

def run_evaluation():
    # Load golden dataset
    dataset_path = os.path.join(os.path.dirname(__file__), 'golden_dataset.json')
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    test_cases = []
    
    print("Generating responses for test cases...")
    for idx, item in enumerate(dataset):
        query = item['input']
        expected_output = item['expected_output']
        
        # Generate actual output from our pipeline
        try:
            result = generate_with_citation(query)
            actual_output = result.get('answer', '')
            retrieval_context = [doc['content'] for doc in result.get('sources', [])]
        except Exception as e:
            print(f"Error generating response for query {idx+1}: {e}")
            actual_output = ""
            retrieval_context = []

        test_case = LLMTestCase(
            input=query,
            actual_output=actual_output,
            expected_output=expected_output,
            retrieval_context=retrieval_context
        )
        test_cases.append(test_case)
        print(f"Prepared test case {idx+1}/{len(dataset)}")

    # Define metrics
    answer_relevancy = AnswerRelevancyMetric(threshold=0.7)
    faithfulness = FaithfulnessMetric(threshold=0.7)
    contextual_relevancy = ContextualRelevancyMetric(threshold=0.7)
    contextual_precision = ContextualPrecisionMetric(threshold=0.7)

    # Evaluate
    print("\nRunning evaluation (this may take a while)...")
    results = evaluate(
        test_cases,
        [answer_relevancy, faithfulness, contextual_relevancy, contextual_precision]
    )
    
    # Analyze and save results
    save_results_to_markdown(results)

def save_results_to_markdown(results):
    output_path = os.path.join(os.path.dirname(__file__), 'results.md')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# RAG Pipeline Evaluation Results\n\n")
        f.write("Evaluation performed using DeepEval.\n\n")
        
        # We would typically aggregate scores here, but DeepEval handles its own reporting.
        # This is a placeholder for where we'd parse DeepEval's output object if needed.
        f.write("## Summary\n\n")
        f.write("Please check the terminal output for the detailed DeepEval metrics summary.\n")
        
        f.write("\n## Test Cases Analysis\n\n")
        # In a real scenario, we'd iterate through results and highlight worst performers
        f.write("See terminal for detailed pass/fail status per test case.\n")
        
    print(f"\nResults summary saved to {output_path}")

if __name__ == "__main__":
    # Ensure OPENAI_API_KEY is set as DeepEval requires it by default for its evaluators
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "mock_key":
         print("WARNING: DeepEval typically requires a valid OPENAI_API_KEY to run its metric models (GPT-4/GPT-3.5) for evaluation.")
         print("Setting a dummy key for syntax checking, but real evaluation will fail without a real key.")
         os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-test-purposes"
         
    # Only run the first 2 cases for a quick test if no real key is present to avoid long hangs/errors
    run_evaluation()
