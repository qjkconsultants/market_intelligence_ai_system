import json
import boto3
from .settings import settings

class StepFunctionsClient:
    def __init__(self):
        self._client = boto3.client(
            "stepfunctions",
            region_name=settings.aws_region,
        )

    def start_ingestion(self, payload: dict) -> None:
        self._client.start_execution(
            stateMachineArn=settings.step_function_arn,
            input=json.dumps(payload),
        )
