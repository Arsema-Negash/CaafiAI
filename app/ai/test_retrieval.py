from app.ai.retrieval import search_clinical_guidelines


def check_query(
    query: str,
    expected_population: str | None = None,
    expected_topic: str | None = None,
    require_urgent_heading: bool = False,
) -> None:
    """Run a retrieval check and report whether expectations are met."""
    results = search_clinical_guidelines(query, top_k=5)

    print(f"\nQUESTION: {query}")

    for result in results:
        print(
            "ID:", result["id"],
            "| Topic:", result["topic"],
            "| Population:", result["population"],
            "| Page:", result["page"],
            "| Semantic:", round(result["score"], 3),
            "| Ranking:", round(result["ranking_score"], 3),
        )

    assert results, f"No results returned for: {query}"

    first = results[0]

    if expected_population is not None:
        assert first["population"] == expected_population, (
            f"Expected population {expected_population}, "
            f"but got {first['population']} for: {query}"
        )

    if expected_topic is not None:
        assert first["topic"] == expected_topic, (
            f"Expected topic {expected_topic}, "
            f"but got {first['topic']} for: {query}"
        )

    if require_urgent_heading:
        content = first["content"].lower()
        assert (
            "give urgent attention to the patient" in content
            or "give urgent attention to the child" in content
        ), f"Urgent heading not found in top result for: {query}"

    print("PASS:", query)


def main() -> None:
    check_query(
        "What are the emergency signs in a child with breathing problems?",
        expected_population="Child",
        expected_topic="Breathing difficulty",
        require_urgent_heading=True,
    )

    check_query(
        "What are the danger signs in an adult with breathing difficulty?",
        expected_population="Adult",
        expected_topic="Breathing difficulty",
        require_urgent_heading=True,
    )

    check_query(
        "When is wheezing or tight chest an emergency?",
        expected_topic="Wheeze/tight chest",
        require_urgent_heading=True,
    )

    print("\nAll retrieval checks passed.")


if __name__ == "__main__":
    main()
