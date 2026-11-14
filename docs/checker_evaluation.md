# Claim Checker evaluation

Run the evaluation with the ContractNLI test archive available locally:

```powershell
python -m scope.evaluation.checker_claim_evaluation --contractnli-zip .\contract-nli.zip
```

The run writes `reports/metrics/checker_claim_evaluation.json`. It contains the project-corpus and controlled-corruption checks separately from the external benchmark.

## Human-labelled benchmark

The external evaluation uses ContractNLI's official test split: 123 real non-disclosure agreements and 2,091 document/hypothesis labels. The benchmark authors formulated the hypotheses independently of SCOPE, and the benchmark supplies human labels and evidence spans for Entailment, Contradiction, and NotMentioned. Entailment is treated as supported; the other two labels are treated as unsupported. For NotMentioned rows, the evaluator supplies the highest-ranked BM25 sentence from that agreement as a retrieved passage, since there is no gold evidence span for a neutral claim.

Dataset: [ContractNLI](https://stanfordnlp.github.io/contract-nli/), Koreeda and Manning, Findings of EMNLP 2021 ([paper](https://aclanthology.org/2021.findings-emnlp.164/)). The dataset is distributed under CC BY 4.0; retain attribution when redistributing it or derived data. The archive is intentionally not committed; pass a locally obtained archive to the command above.

Current result: accuracy 0.559, unsupported detection rate 0.881, false-positive rate 0.119, and supported-claim false-rejection rate 0.815. These results indicate substantial Checker limitations. ContractNLI contains NDAs, not shipping or procurement policies, so this is a real-document legal-domain transfer evaluation, not a domain-specific accuracy estimate. BM25 neutral evidence is a retrieval simulation, not a human relevance annotation.

Three source-attributed U.S. Federal Acquisition Regulation extracts are also indexed in `data/documents/official/`. They broaden retrieval beyond fixtures but do not yet have independent human claim labels. Do not conflate them with the ContractNLI gold evaluation.
