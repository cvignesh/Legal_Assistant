# Argument Miner Architecture & Workflow

## Overview
The Argument Miner is an AI-powered legal analysis system that extracts, normalizes, classifies, and validates prosecution and defense arguments from court judgments using a Retrieval-Augmented Generation (RAG) pipeline combined with LLM processing.

The system now includes:

- Optimized Case Miner and Fact Miner pipelines
- Enhanced Argument Normalizer
- Integrated Argument Polarity Classifier
- Faster retrieval and batching strategy
- Improved UI performance through reduced LLM calls

It supports multiple modes:

- Case ID Mode – extracts arguments from a specific judgment
- Facts Mode – uses user-provided facts as semantic retrieval signals

---

## High-Level Architecture

+-------------------+      +-------------------+      +-------------------+
|   Frontend (UI)   | <--> |   FastAPI Backend | <--> |   MongoDB/Vector  |
|  (React/TS)       |      |  (Python)         |      |   DB (Chunks)     |
+-------------------+      +-------------------+      +-------------------+

---

## Detailed Workflow (Updated Pipeline)

User Request → Router → Miner → Retriever → Normalizer → Polarity Classifier → Response

---

## Miner Execution

### Case Miner
- Direct case metadata filtering
- Combined prosecution and defense retrieval
- Reduced redundant searches
- Optimized chunk aggregation

### Fact Miner
Facts are semantic retrieval signals.
Facts → Embedding Search → Relevant Judgment Chunks

Enhancements:
- Multi-fact batching
- Reduced retrieval duplication
- Context-aware chunk merging

---

## Chunk Retrieval Layer

Responsibilities:
- Vector search
- Metadata filtering
- Chunk deduplication
- Context merging

---

## Argument Normalization

- Single-batch LLM extraction
- Structured argument formatting
- Duplicate collapse
- Noise removal

Pipeline:
Merged Chunks → Single LLM Call → Clean Argument List

---

## Argument Polarity Classifier

Normalized Arguments → Polarity Classifier → Prosecution / Defense Buckets

Benefits:
- Argument-level role classification
- Reduced metadata dependency
- Handles mixed-role chunks

---

## Optional Validation

Checks:
- Legal relevance
- Context grounding
- Argument correctness

---

## Updated Data Flow

User → API Request → Router → Miner → Retriever → Normalizer → Polarity Classifier → Response → UI

---

## Key Backend Components

- FastAPI App
- argument_miner.service
- case_miner
- fact_miner
- retriever
- normalizer
- polarity_classifier
- llm_validator
- MongoDB Vector Database

---

## Example Facts Mode Flow

Facts Input → Semantic Retrieval → Merged Chunks → LLM Normalization → Polarity Classification → Arguments Output

---

## Hackathon Talking Point

Facts are used only for semantic retrieval.
Arguments are always extracted from retrieved legal judgment text.
