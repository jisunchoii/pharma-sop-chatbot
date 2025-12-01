import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Bedrock Knowledge Base Configuration
KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID", "")

# Model Configuration
DEFAULT_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
RERANKER_MODEL_ARN = f"arn:aws:bedrock:{AWS_REGION}::foundation-model/cohere.rerank-v3-5:0"

# Model Options
MODEL_OPTIONS = {
    "Claude Sonnet 4": {
        "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "max_tokens": 4096,
    },
    "Claude Sonnet 4.5": {
        "model_id": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "max_tokens": 4096,
    },
    "Claude Haiku 4.5": {
        "model_id": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "max_tokens": 4096,
    },
}

# DynamoDB Configuration
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "user_feedback")

# RAG Configuration
RAG_NUMBER_OF_RESULTS = 10
RAG_NUMBER_OF_RERANKED_RESULTS = 5
