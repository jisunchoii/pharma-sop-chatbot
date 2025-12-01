import logging
import sys
import boto3
from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel
from strands.agent.conversation_manager import SlidingWindowConversationManager

import config

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("agent")

# Initialize Bedrock Agent Runtime client for RAG
bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=config.AWS_REGION,
    config=Config(
        read_timeout=300,
        connect_timeout=300,
        retries=dict(max_attempts=3, mode="adaptive"),
    )
)

# Conversation manager for maintaining context
conversation_manager = SlidingWindowConversationManager(window_size=10)


def get_bedrock_model(model_name: str) -> BedrockModel:
    """Get Bedrock model based on model name."""
    model_config = config.MODEL_OPTIONS.get(model_name, config.MODEL_OPTIONS["Claude Sonnet 4.5"])

    return BedrockModel(
        boto_client_config=Config(
            read_timeout=300,
            connect_timeout=300,
            retries=dict(max_attempts=3, mode="adaptive"),
        ),
        model_id=model_config["model_id"],
        max_tokens=model_config["max_tokens"],
    )


@tool
def retrieve_from_knowledge_base(query: str) -> str:
    """
    Retrieve relevant information from the Bedrock Knowledge Base with reranking.

    This tool searches the pharma SOP knowledge base and returns relevant document chunks
    that can help answer questions about pharmaceutical procedures, regulations, and guidelines.

    Args:
        query: The search query to find relevant SOP information

    Returns:
        Retrieved and reranked document chunks with source information
    """
    if not config.KNOWLEDGE_BASE_ID:
        return "Error: Knowledge Base ID is not configured. Please set the KNOWLEDGE_BASE_ID environment variable."

    try:
        # Build retrieval configuration with reranking
        retrieval_config = {
            "vectorSearchConfiguration": {
                "numberOfResults": config.RAG_NUMBER_OF_RESULTS,
                "rerankingConfiguration": {
                    "type": "BEDROCK_RERANKING_MODEL",
                    "bedrockRerankingConfiguration": {
                        "modelConfiguration": {
                            "modelArn": config.RERANKER_MODEL_ARN
                        },
                        "numberOfRerankedResults": config.RAG_NUMBER_OF_RERANKED_RESULTS
                    }
                }
            }
        }

        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=config.KNOWLEDGE_BASE_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration=retrieval_config
        )

        results = response.get("retrievalResults", [])

        if not results:
            return "No relevant information found in the knowledge base for the given query."

        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            content = result.get("content", {}).get("text", "")
            score = result.get("score", 0)
            location = result.get("location", {})

            # Extract source information
            source_info = ""
            if "s3Location" in location:
                uri = location["s3Location"].get("uri", "")
                source_info = f"Source: {uri}"

            formatted_results.append(
                f"[Result {i}] (Relevance Score: {score:.4f})\n"
                f"{content}\n"
                f"{source_info}"
            )

        return "\n\n---\n\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Error retrieving from knowledge base: {e}")
        return f"Error retrieving from knowledge base: {str(e)}"


def create_sop_agent(model_name: str = "Claude Sonnet 4.5") -> Agent:
    """Create the SOP chatbot agent with RAG capabilities."""

    system_prompt = """당신은 제약 회사의 SOP(Standard Operating Procedure) 전문 챗봇입니다.

당신의 역할:
1. 사용자의 SOP 관련 질문에 대해 정확하고 전문적인 답변을 제공합니다.
2. Knowledge Base에서 관련 정보를 검색하여 근거 기반의 답변을 합니다.
3. 답변 시 반드시 참조한 SOP 문서 번호를 명시합니다.
4. GMP, GDP 등 제약 규정에 맞는 정확한 정보를 제공합니다.

답변 가이드라인:
- 질문을 받으면 먼저 retrieve_from_knowledge_base 도구를 사용하여 관련 정보를 검색하세요.
- 검색된 정보를 바탕으로 명확하고 구조화된 답변을 제공하세요.
- SOP 문서 번호, 섹션, 버전 등을 정확히 인용하세요.
- 불확실한 정보는 추측하지 말고, 추가 확인이 필요하다고 안내하세요.
- 한국어로 답변하세요.

질문 유형별 답변 형식:
- Fact Retrieval: 해당 SOP 번호와 섹션을 명시하고 절차를 설명
- Summary: 핵심 내용을 요약하여 구조화된 형태로 제공
- Definition: SOP 기준의 정확한 정의 제공
- Comparison: 관련 SOP 목록 비교 제공
- Conditional: 조건에 따른 절차 차이 설명
- Location: 해당 정보가 위치한 SOP 문서 및 섹션 안내
- Yes/No: 명확한 예/아니오 답변 후 근거 SOP 제시
"""

    model = get_bedrock_model(model_name)

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[retrieve_from_knowledge_base],
        conversation_manager=conversation_manager
    )

    return agent


def run_agent(query: str, model_name: str = "Claude Sonnet 4.5") -> str:
    """Run the SOP agent with the given query."""
    try:
        agent = create_sop_agent(model_name)
        response = agent(query)
        return str(response)
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return f"Error: {str(e)}"


async def run_agent_stream(query: str, model_name: str = "Claude Sonnet 4.5"):
    """Run the SOP agent with streaming response."""
    try:
        agent = create_sop_agent(model_name)
        async for event in agent.stream_async(query):
            if "data" in event:
                yield event["data"]
    except Exception as e:
        logger.error(f"Error in streaming agent: {e}")
        yield f"Error: {str(e)}"


def clear_conversation():
    """Clear the conversation history."""
    global conversation_manager
    conversation_manager = SlidingWindowConversationManager(window_size=10)
