# 헤르 AI API 공통 설정 (3개 프로젝트 공통)
# api_key = HERMES_API_KEY (환경변수에서 로드)

HERMES_API_BASE_CLAUDE = "https://h-chat-api.autoever.com/claude-code/v2"
HERMES_MODEL_CLAUDE = "claude-sonnet-4-6"

HERMES_API_BASE_GPT = "https://internal-apigw-kr.hmg-corp.io/hchat-in/api/v3/openai/deployments/gpt-5.4"
HERMES_MODEL_GPT = "gpt-5.4"

# 사용법:
# import os
# from openai import OpenAI
# client = OpenAI(api_key=os.environ["HERMES_API_KEY"], base_url=HERMES_API_BASE_CLAUDE)
# response = client.chat.completions.create(model=HERMES_MODEL_CLAUDE, messages=[...])
