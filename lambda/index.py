# lambda/index.py
import json
import os
import re  # 正規表現モジュールをインポート
import urllib.request
import urllib.error


# FastAPI エンドポイントURL
FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://3585-34-125-176-33.ngrok-free.app")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # FastAPIに送信するリクエストデータ
        request_data = {
            "prompt": message,
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }

        # リクエスト
        req = urllib.request.Request(
            f"{FASTAPI_URL}/generate",
            data=json.dumps(request_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        print("Sending request to FastAPI:", json.dumps(request_data))

        # FastAPIにリクエストを送信
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            print("FastAPI response:", json.dumps(response_data))

            # 応答の検証
            if not response_data.get('generated_text'):
                raise Exception("No response content from FastAPI")

            # 会話履歴を更新
            conversation_history.append({
                "role": "user",
                "content": message
            })
            conversation_history.append({
                "role": "assistant",
                "content": response_data['generated_text']
            })

            # 成功レスポンスの返却
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                    "Access-Control-Allow-Methods": "OPTIONS,POST"
                },
                "body": json.dumps({
                    "success": True,
                    "response": response_data['generated_text'],
                    "conversationHistory": conversation_history
                })
            }

    except urllib.error.HTTPError as e:
        print("HTTP Error:", str(e))
        error_message = f"FastAPI request failed: {str(e)}"
        return {
            "statusCode": e.code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": error_message
            })
        }
    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }



