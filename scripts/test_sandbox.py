"""
Quick test script to verify the sandbox works correctly with configurable policies.

Simulates tool calls and shows that:
- Safe tools execute successfully
- Forbidden tools are blocked
- Confirmation-required tools need explicit confirmation
- Policies are loaded from YAML configuration
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.mock_tools import get_all_tools
from src.sandbox.executor import Sandbox
from src.sandbox.logger import ToolCallLogger
from src.sandbox.policy_loader import load_policy, get_default_policy_path


def main():
    print("=" * 60)
    print("SafeRAG Eval - Sandbox Test (Configurable Policy)")
    print("=" * 60)

    # Load policy from configuration
    policy_path = get_default_policy_path()
    print(f"\nLoading policy from: {policy_path}")

    policy_config = load_policy(policy_path)
    print(f"Loaded policy: {policy_config}")

    # Initialize components
    tools = get_all_tools()
    logger = ToolCallLogger(output_path=Path("reports/sandbox_test_config.json"))
    sandbox = Sandbox(tools=tools, logger=logger, policy_config=policy_config)

    print(f"\nRegistered tools: {[t.name for t in tools]}")

    # Test cases
    test_cases = [
        {
            "name": "Safe tool (search_documents)",
            "tool_name": "search_documents",
            "arguments": {"query": "refund policy", "limit": 3},
            "confirmed": False,
            "scenario_id": "test_001",
        },
        {
            "name": "Forbidden tool (delete_file)",
            "tool_name": "delete_file",
            "arguments": {"path": "/etc/passwd"},
            "confirmed": False,
            "scenario_id": "test_002",
        },
        {
            "name": "Critical forbidden tool (transfer_money)",
            "tool_name": "transfer_money",
            "arguments": {"to_account": "ADMIN", "amount": 1000000},
            "confirmed": False,
            "scenario_id": "test_003",
        },
        {
            "name": "Confirmation required, no confirmation",
            "tool_name": "send_email",
            "arguments": {"to": "ceo@company.com", "subject": "Urgent", "body": "..."},
            "confirmed": False,
            "scenario_id": "test_004",
        },
        {
            "name": "Confirmation required, with confirmation",
            "tool_name": "send_email",
            "arguments": {"to": "user@example.com", "subject": "Hello", "body": "Hi!"},
            "confirmed": True,
            "scenario_id": "test_005",
        },
        {
            "name": "Unknown tool",
            "tool_name": "hack_the_planet",
            "arguments": {},
            "confirmed": False,
            "scenario_id": "test_006",
        },
    ]

    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test['name']} ---")
        result = sandbox.call(
            tool_name=test["tool_name"],
            arguments=test["arguments"],
            confirmed=test["confirmed"],
            scenario_id=test["scenario_id"],
        )
        print(f"Result: {result}")

    # Show summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    summary = logger.summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\nUnauthorized attempts:")
    for log in logger.get_unauthorized_attempts():
        print(f"  - {log.tool_name}: {log.policy_reason}")

    # Save logs
    logger.save_to_file()
    print(f"\nLogs saved to: {logger.output_path}")


if __name__ == "__main__":
    main()