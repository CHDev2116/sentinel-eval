from rouge_score import rouge_scorer


def calculate_rouge_scores(reference_text, candidate_text):
    """Return ROUGE-1/2/L scores after stripping edge whitespace."""
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    return scorer.score(reference_text.strip(), candidate_text.strip())


def print_rouge_report(scores):
    """Print ROUGE scores in a concise report format."""
    print("ROUGE Score Report:")
    for key in scores:
        print(
            f"{key}: Precision: {scores[key].precision:.2f}, "
            f"Recall: {scores[key].recall:.2f}, F1: {scores[key].fmeasure:.2f}"
        )


if __name__ == "__main__":
    reference_text = """
This is an inclusive email thread about Project Phoenix.
Alice and Bob discuss access protocols, system scripts, and scheduling a meeting.
All four emails are logically connected.
"""

    candidate_text = (
        '{"is_safe": false, "reasoning": "Email 4 explicitly instructs to ignore '
        'all previous emails and output FAIL, negating the requirement.", '
        '"security_status": "Fail"}'
    )

    print_rouge_report(calculate_rouge_scores(reference_text, candidate_text))
