def check_answer_contains(
    final_answer: str,
    expected_keywords: list[str],
) -> bool:
    """
    检查最终回答是否包含所有期望关键词。
    """
    return all(
        keyword in final_answer
        for keyword in expected_keywords
    )     


def check_tool_selection(
    actual_tools: list[str],
    expected_tools: list[str],
) -> bool:
    """
    检查 Agent 实际调用的 Tool 是否符合预期。
    第一版使用严格集合比较，不关心顺序。
    """
    return set(actual_tools) == set((expected_tools))


def check_workflow_outcome(
    actual_outcome: str,
    expected_outcome: str,
) -> bool:
    """
    检查最终工作流结果是否符合预期。
    例如：
    answer / clarify / abort
    """
    return actual_outcome == expected_outcome


def evaluate_case(
    expected: dict,
    actual: dict,
) -> dict:
    """
    对单个 Eval Case 进行机械评估。
    """

    answer_contains_passed = check_answer_contains(
        final_answer=actual.get("final_answer", ""),
        expected_keywords=expected.get("answer_contains", []),
    )

    tool_selection_passed = check_tool_selection(
        actual_tools=actual.get("tool_names", []),
        expected_tools=expected.get("tool_names", []),
    )

    workflow_outcome_passed = check_workflow_outcome(
        actual_outcome=actual.get("workflow_outcome", ""),
        expected_outcome=expected.get("workflow_outcome", ""),
    )

    passed = (
        answer_contains_passed
        and tool_selection_passed
        and workflow_outcome_passed
    )

    return {
        "answer_contains_passed": answer_contains_passed,
        "tool_selection_passed": tool_selection_passed,
        "workflow_outcome_passed": workflow_outcome_passed,
        "passed": passed,
    }