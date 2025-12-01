import logging
import sys
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

import config

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("feedback")

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name=config.AWS_REGION)


def get_or_create_table():
    """Get the feedback table, creating it if it doesn't exist."""
    try:
        table = dynamodb.Table(config.DYNAMODB_TABLE_NAME)
        table.load()
        return table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.info(f"Creating DynamoDB table: {config.DYNAMODB_TABLE_NAME}")
            table = dynamodb.create_table(
                TableName=config.DYNAMODB_TABLE_NAME,
                KeySchema=[
                    {'AttributeName': 'feedback_id', 'KeyType': 'HASH'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'feedback_id', 'AttributeType': 'S'},
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            table.wait_until_exists()
            logger.info(f"Table {config.DYNAMODB_TABLE_NAME} created successfully")
            return table
        else:
            raise


def save_feedback(
    question: str,
    answer: str,
    is_helpful: bool,
    feedback_text: str = "",
    session_id: str = ""
) -> bool:
    """
    Save user feedback to DynamoDB.

    Args:
        question: The user's question
        answer: The agent's response
        is_helpful: Whether the response was helpful (True/False)
        feedback_text: Optional additional feedback text
        session_id: Session identifier

    Returns:
        True if feedback was saved successfully, False otherwise
    """
    try:
        table = get_or_create_table()

        feedback_item = {
            'feedback_id': str(uuid.uuid4()),
            'session_id': session_id or str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'question': question,
            'answer': answer,
            'is_helpful': is_helpful,
            'feedback_text': feedback_text,
        }

        table.put_item(Item=feedback_item)
        logger.info(f"Feedback saved successfully: {feedback_item['feedback_id']}")
        return True

    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        return False


def get_feedback_stats() -> dict:
    """Get feedback statistics."""
    try:
        table = get_or_create_table()
        response = table.scan()
        items = response.get('Items', [])

        total = len(items)
        helpful = sum(1 for item in items if item.get('is_helpful', False))

        return {
            'total_feedback': total,
            'helpful_count': helpful,
            'not_helpful_count': total - helpful,
            'helpful_rate': (helpful / total * 100) if total > 0 else 0
        }

    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        return {
            'total_feedback': 0,
            'helpful_count': 0,
            'not_helpful_count': 0,
            'helpful_rate': 0
        }
