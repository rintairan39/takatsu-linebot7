import azure.functions as func
import os
import json
import traceback
import sys

# Google API 用（.python_packages/lib/site-packages に入っている前提）
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".python_packages", "lib", "site-packages"))

try:
    import googleapiclient.discovery
    import google.oauth2.service_account
    import requests
except Exception as e:
    # インポートエラーの内容を直接返して確認できるようにする
    def main(req: func.HttpRequest) -> func.HttpResponse:
        err = traceback.format_exc()
        env = {
            "GCP_SA_B64_set": bool(os.environ.get("GCP_SA_B64")),
            "SHEET_ID_set": bool(os.environ.get("SHEET_ID")),
            "SHEET_RANGE": os.environ.get("SHEET_RANGE"),
        }
        return func.HttpResponse(
            f"IMPORT_ERROR: {json.dumps({'ok_imports': False, 'err_imports': str(e), 'env': env}, ensure_ascii=False)}",
            status_code=500,
            mimetype="application/json"
        )

else:
    def main(req: func.HttpRequest) -> func.HttpResponse:
        try:
            # --- 環境変数 ---
            sa_b64 = os.environ.get("GCP_SA_B64")
            sheet_id = os.environ.get("SHEET_ID")
            sheet_range = os.environ.get("SHEET_RANGE", "シート1!A:F")

            if not sa_b64 or not sheet_id:
                return func.HttpResponse("Missing environment variables", status_code=500)

            # --- サービスアカウント設定 ---
            import base64
            sa_json = json.loads(base64.b64decode(sa_b64).decode("utf-8"))
            creds = google.oauth2.service_account.Credentials.from_service_account_info(
                sa_json,
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
            )

            # --- Google Sheets API ---
            service = googleapiclient.discovery.build("sheets", "v4", credentials=creds)
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=sheet_id, range=sheet_range).execute()
            values = result.get("values", [])

            # --- 結果を整形 ---
            data = []
            for row in values[1:]:  # 1行目はヘッダーと想定
                item = {
                    "category": row[0] if len(row) > 0 else "",
                    "title": row[1] if len(row) > 1 else "",
                    "keywords": row[2] if len(row) > 2 else "",
                    "content": row[3] if len(row) > 3 else "",
                    "url": row[4] if len(row) > 4 else "",
                    "updated": row[5] if len(row) > 5 else "",
                }
                data.append(item)

            return func.HttpResponse(
                json.dumps({"reloaded": len(data), "sample": data[:3]}, ensure_ascii=False),
                status_code=200,
                mimetype="application/json"
            )

        except Exception:
            err = traceback.format_exc()
            return func.HttpResponse(
                json.dumps({"error": err}, ensure_ascii=False),
                status_code=500,
                mimetype="application/json"
            )
