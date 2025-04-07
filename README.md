# Genie Tooling: CodeQuilt Specification

**Author:** Kal Aeolian
**Status:** Research / Specification Draft (CodeQuilt v0.7.1)
**Date:** 2025-04-08

---

***WIP***

This is a work in progress. It compiles and runs in the big language models but the tradeoff depends on the hit level in the corpus. 

## The Challenge: Reliable & Efficient Code Generation with LLMs

Large Language Models (LLMs) are powerful code generators but can suffer from output truncation (hitting token limits) and inefficient token usage, especially with repetitive code or large identifier sets. This impacts reliability and cost in automated workflows.

## CodeQuilt: A Solution for Compressed Code Representation

CodeQuilt is a specification for representing source code (primarily Python) in a compressed, text-based format optimized for LLM interaction. It acts as a textual "blueprint" designed to:

* **Maximize Token Density:** Represent code using significantly fewer LLM API tokens than the original source.
* **Increase Generation Reliability:** Reduce the likelihood of hitting output token limits, ensuring a complete representation is received more often.
* **Improve Efficiency:** Lower the token cost for transmitting code concepts to/from the LLM during generation, debugging, or modification.

## Core Concepts of CodeQuilt v0.7.1-semantic

This version employs a multi-pronged compression strategy tailored for LLMs:

* **Implied Corpus Dictionary:** A standard dictionary (defined by the spec version) maps common Python elements (`print`, `len`, `ValueError`, `self`, `os`, `path`, etc.) to short `c<n>` references, minimizing redundancy for frequent items. This dictionary is not sent in the header.
* **Dynamic Dictionary:** A small, per-message header (`D:`) maps `d<n>` references only to identifiers specific to the current code snippet and not found in the standard corpus dictionary.
* **Dense Fixed Tokens:** Single ASCII characters represent core syntax (keywords like `def`->`D`, operators `and`->`&`, structure `newline`->`N`, `indent`->`>`).
* **Semantic Pattern Tokens:** Compact tokens (e.g., `LOG(...)`, `ATTR(...)`, `RETN(...)`) represent common multi-line code patterns (like logging, checks, common assignments), allowing the LLM to generate these patterns using fewer tokens.
* **Efficient Literal Handling:** Short literals are embedded directly; long/multiline ones use Base64 in an optional `X:` header.
* **Comment Removal:** Non-functional comments are discarded by default.

## Why This Approach Reduces Tokens

* **Corpus & Dynamic Dictionaries:** Heavily reduce token usage for repeated identifiers (common functions, variables) compared to writing them out repeatedly.
* **Semantic Tokens:** Replace entire code blocks (e.g., a try/except/log pattern) with a single, parameterized token, offering significant savings on common logic structures.
* **Fixed Tokens & Structure:** Map multi-character keywords/operators and structural whitespace to single characters.
* **Focus on LLM Tokenizers:** Uses ASCII characters and structures that LLM tokenizers typically handle efficiently (avoiding multi-byte UTF-8 penalties).

## Benefits

* **Lower API Costs:** Significantly fewer tokens sent/received per code unit, especially for larger or repetitive code.
* **Improved Reliability:** Less chance of hitting output limits, leading to more complete generations.
* **Faster Interaction:** Reduced data transfer can speed up iterative development or agentic loops.
* **Context Window Management:** Helps fit more complex code concepts within limited context windows.

## Intended Usage

1.  **Prompting:** Provide the LLM with the CodeQuilt spec, the implied Corpus Dictionary content, semantic token definitions, and instruct it to generate CodeQuilt, prioritizing semantic tokens and corpus references for maximum compression.
2.  **Generation:** LLM generates the compact CodeQuilt string.
3.  **Reconstruction:** A dedicated parser uses the spec version (to know the corpus dict and fixed tokens), the header (`D:`, `X:`), and the body tokens to reconstruct the full Python code.

## Specification Details

The complete technical specification, including EBNF, token mappings, the standard Corpus Dictionary for the current version, semantic token definitions, and reconstruction notes, can be found here:
➡️ Read the full CodeQuilt v0.7.1 Specification `(Link to the detailed spec file)`

## Project Status & Contributing

`genie-tooling` and CodeQuilt are research initiatives. This specification (v0.7.1) is a draft reflecting findings on optimizing for LLM token efficiency. Feedback, analysis, benchmarking results, and discussion are highly welcome via Issues.

## License

MIT License (Assuming MIT)