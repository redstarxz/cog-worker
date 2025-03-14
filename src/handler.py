import time
import subprocess

import runpod
import requests
from requests.adapters import HTTPAdapter, Retry

LOCAL_URL = "http://127.0.0.1:5000"

cog_session = requests.Session()
retries = Retry(total=10, backoff_factor=0.1, status_forcelist=[502, 503, 504])
cog_session.mount('http://', HTTPAdapter(max_retries=retries))


# ----------------------------- Start API Service ---------------------------- #
# Call "python -m cog.server.http" in a subprocess to start the API service.
subprocess.Popen(["python", "-m", "cog.server.http", "--upload-url", "https://upload.10xi.top/upload"])


# ---------------------------------------------------------------------------- #
#                              Automatic Functions                             #
# ---------------------------------------------------------------------------- #
def wait_for_service(url):
    '''
    Check if the service is ready to receive requests.
    '''
    while True:
        try:
            health = requests.get(url, timeout=120)
            status = health.json()["status"]

            if status == "READY":
                time.sleep(1)
                return

        except requests.exceptions.RequestException:
            print("Service not ready yet. Retrying...")
        except Exception as err:
            print("Error: ", err)

        time.sleep(0.2)


def run_inference(inference_request,prediction_id):
    '''
    Run inference on a request.
    '''

    # 兼容cog, 需要支持迷瞪的场景, 并且回调里需要带上id来查询. 需要对input再包装一层
    print(prediction_id)
    print(inference_request)

    response = cog_session.put(url=f'{LOCAL_URL}/predictions/{prediction_id}',
                                json=inference_request, timeout=600, headers={'Prefer':'respond-async'})
    print("实际发送的请求头:", response.request.headers)

    return response.json()


# ---------------------------------------------------------------------------- #
#                                RunPod Handler                                #
# ---------------------------------------------------------------------------- #
def handler(event):
    '''
    This is the handler function that will be called by the serverless.
    '''
    json = run_inference(
        {
            "input": event["input"]["cog"],
            "webhook": event["input"]["webhook"],
            "webhook_events_filter": event["input"]["webhook_events_filter"],
        },
        event["input"]["prediction_id"]
    )
    print(json)
    return json


if __name__ == "__main__":
    wait_for_service(url=f'{LOCAL_URL}/health-check')

    print("Cog API Service is ready. Starting RunPod serverless handler...")

    runpod.serverless.start({"handler": handler})
