"""
Quick test script to verify the sandbox works correctly.

Simulates a few tool calls and shows that:
- Safe tools execute successfully
- Forbidden tools are blocked
- Confirmation-required tools need explicit confirmation
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools.mock_tools import get_all_tools
from src.sandbox.executor import Sandbox
from src.sandbox.logger import ToolCallLogger


def main():
    print("=" * 60)
    print("SafeRAG Eval - Sandbox Test")
    print("=" * 60)

    # Initialize components
    tools = get_all_tools()
    logger = ToolCallLogger(output_path=Path("reports/sandbox_test.json"))
    sandbox = Sandbox(tools=tools, logger=logger)

    print(f"\nRegistered tools: {[t.name for t in tools]}")
    print("\n--- Test 1: Safe tool (search_documents) ---")
    result = sandbox.call(
        tool_name="search_documents",
        arguments={"query": "refund policy", "limit": 3},
        scenario_id="test_001",
    )
    print(f"Result: {result}")

    print("\n--- Test 2: Forbidden tool (delete_file) ---")
    result = sandbox.call(
        tool_name="delete_file",
        arguments={"path": "/etc/passwd"},
        scenario_id="test_002",
    )
    print(f"Result: {result}")

    print("\n--- Test 3: Critical forbidden tool (transfer_money) ---")
    result = sandbox.call(
        tool_name="transfer_money",
        arguments={"to_account": "ADMIN", "amount": 1000000},
        scenario_id="test_003",
    )
    print(f"Result: {result}")

    print("\n--- Test 4: Confirmation required, no confirmation ---")
    result = sandbox.call(
        tool_name="send_email",
        arguments={"to": "ceo@company.com", "subject": "Urgent", "body": "..."},
        confirmed=False,
        scenario_id="test_004",
    )
    print(f"Result: {result}")

    print("\n--- Test 5: Confirmation required, with confirmation ---")
    result = sandbox.call(
        tool_name="send_email",
        arguments={"to": "user@example.com", "subject": "Hello", "body": "Hi!"},
        confirmed=True,
        scenario_id="test_005",
    )
    print(f"Result: {result}")

    print("\n--- Test 6: Unknown tool ---")
    result = sandbox.call(
        tool_name="hack_the_planet",
        arguments={},
        scenario_id="test_006",
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