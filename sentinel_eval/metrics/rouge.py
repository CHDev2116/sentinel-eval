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
