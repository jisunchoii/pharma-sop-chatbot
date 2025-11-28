# Pharma SOP Chatbot - Bedrock Knowledge Base

제약 산업 SOP(Standard Operating Procedure) 문서를 위한 Amazon Bedrock Knowledge Base 구축 CloudFormation 템플릿입니다.

## 개요

이 프로젝트는 S3에 저장된 SOP 문서를 OpenSearch Serverless 벡터 데이터베이스에 인덱싱하여 Amazon Bedrock Knowledge Base를 생성합니다. 이를 통해 자연어 질의를 통한 문서 검색 및 RAG(Retrieval-Augmented Generation) 기반 챗봇 구현이 가능합니다.

## 아키텍처

- **Amazon Bedrock Knowledge Base**: 문서 검색 및 RAG 엔진
- **OpenSearch Serverless**: 벡터 임베딩 저장소 (VECTORSEARCH 타입)
- **Amazon S3**: 소스 문서 저장소
- **Amazon Titan Embedding v2**: 텍스트 임베딩 모델 (1024 차원)
- **Lambda Function**: OpenSearch 인덱스 자동 생성

## 주요 기능

- 계층적 청킹(Hierarchical Chunking) 전략으로 문서 분할
  - Level 1: 1500 토큰
  - Level 2: 300 토큰
  - Overlap: 60 토큰
- HNSW 알고리즘 기반 벡터 검색 (FAISS 엔진)
- 자동화된 OpenSearch 인덱스 생성 및 구성
- IAM 역할 및 정책 자동 설정

## 사전 요구사항

1. AWS 계정 및 적절한 권한
2. S3 버킷 생성 및 SOP 문서 업로드 완료
3. Amazon Bedrock 모델 액세스 활성화 (Titan Embedding v2)
4. 지원 리전: us-east-1, us-east-2, us-west-1, us-west-2, ap-northeast-2

## 배포 방법

### AWS CLI 사용

```bash
aws cloudformation create-stack \
  --stack-name pharma-sop-kb \
  --template-body file://bedrock-knowledge-base.yaml \
  --parameters \
    ParameterKey=KnowledgeBaseName,ParameterValue=pharma-sop-kb \
    ParameterKey=S3BucketName,ParameterValue=your-sop-bucket \
    ParameterKey=S3KeyPrefix,ParameterValue=sop-documents/ \
    ParameterKey=OpenSearchCollectionName,ParameterValue=pharma-sop-collection \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-northeast-2
```

### AWS Console 사용

1. CloudFormation 콘솔 접속
2. "스택 생성" 선택
3. `bedrock-knowledge-base.yaml` 파일 업로드
4. 파라미터 입력:
   - **KnowledgeBaseName**: Knowledge Base 이름
   - **S3BucketName**: 문서가 저장된 S3 버킷 이름
   - **S3KeyPrefix**: S3 버킷 내 문서 경로 (선택사항)
   - **OpenSearchCollectionName**: OpenSearch 컬렉션 이름
5. IAM 리소스 생성 권한 승인
6. 스택 생성 실행

## 파라미터 설명

| 파라미터 | 설명 | 기본값 | 필수 |
|---------|------|--------|------|
| KnowledgeBaseName | Knowledge Base 이름 (1-100자, 영숫자 및 하이픈) | bedrock-kb | Yes |
| S3BucketName | 소스 문서가 저장된 S3 버킷 이름 | - | Yes |
| S3KeyPrefix | S3 버킷 내 문서 경로 필터 (비워두면 전체 버킷) | "" | No |
| OpenSearchCollectionName | OpenSearch 컬렉션 이름 (3-32자, 소문자) | bedrock-kb-collection | Yes |

## 생성되는 리소스

1. **IAM 역할 및 정책**
   - Bedrock Knowledge Base 서비스 역할
   - S3 읽기 권한 정책
   - OpenSearch 액세스 정책
   - Bedrock 모델 호출 정책

2. **OpenSearch Serverless**
   - 벡터 검색 컬렉션
   - 암호화 보안 정책
   - 네트워크 보안 정책
   - 데이터 액세스 정책

3. **Lambda Function**
   - OpenSearch 인덱스 자동 생성
   - 벡터 필드 매핑 구성

4. **Bedrock Knowledge Base**
   - Knowledge Base 인스턴스
   - S3 데이터 소스 연결

## 배포 후 작업

### 1. 데이터 소스 동기화

```bash
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id <KNOWLEDGE_BASE_ID> \
  --data-source-id <DATA_SOURCE_ID> \
  --region ap-northeast-2
```

Knowledge Base ID와 Data Source ID는 CloudFormation 출력에서 확인할 수 있습니다.

### 2. 동기화 상태 확인

```bash
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id <KNOWLEDGE_BASE_ID> \
  --data-source-id <DATA_SOURCE_ID> \
  --ingestion-job-id <JOB_ID> \
  --region ap-northeast-2
```

### 3. Knowledge Base 테스트

```bash
aws bedrock-agent-runtime retrieve \
  --knowledge-base-id <KNOWLEDGE_BASE_ID> \
  --retrieval-query text="SOP 문서 검색 쿼리" \
  --region ap-northeast-2
```

## 출력값

| 출력 | 설명 |
|------|------|
| BedrockKnowledgeBaseId | Knowledge Base ID |
| BedrockKnowledgeBaseRoleArn | Knowledge Base IAM 역할 ARN |
| OpenSearchServerlessCollectionArn | OpenSearch 컬렉션 ARN |
| BedrockKnowledgeBaseDataSourceId | S3 데이터 소스 ID |


## 참고 자료

- [Amazon Bedrock Knowledge Base 문서](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [OpenSearch Serverless 문서](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [Amazon Titan Embedding 모델](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
