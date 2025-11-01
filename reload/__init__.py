import sys, os
# ここを追加： wwwroot/.python_packages/lib/site-packages をパスに通す
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".python_packages", "lib", "site-packages"))

import azure.functions as func
import googleapiclient.discovery  # ここで失敗しないはず

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("reloaded: 0 docs", status_code=200)
