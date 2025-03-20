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

def wait_for_cog_callback(url):

    while True:
        try:
            health = requests.get(url, timeout=120)
            status = health.json()["status"]

            if status == "DONE":
                time.sleep(1)
                return

        except requests.exceptions.RequestException:
            print("Service not ready yet. Retrying...")
        except Exception as err:
            print("Error: ", err)

        time.sleep(3)

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


def run_inference(inference_request):
    '''
    Run inference on a request.
    '''

    loop_url = inference_request["input"]["loop_url"]
    del inference_request["input"]["loop_url"]

    webhook = inference_request["input"]["webhook"]
    inference_request["webhook"] =  webhook
    del inference_request["input"]["webhook"]

    inference_request["webhook_events_filter"] =['completed']

    prediction_id = inference_request["input"]["prediction_id"]
    del inference_request["input"]["prediction_id"]

    response = cog_session.put(url=f'{LOCAL_URL}/predictions/{prediction_id}',
                                json=inference_request, timeout=600, headers={'Prefer':'respond-async'})


    print(response.json())
    # wait for async done

    wait_for_cog_callback(url=f'{loop_url}')

    return {"status": "COMPLETED", "id":prediction_id }


# ---------------------------------------------------------------------------- #
#                                RunPod Handler                                #
# ---------------------------------------------------------------------------- #
def handler(event):
    '''
    This is the handler function that will be called by the serverless.
    '''
    print(event["input"])
    json = run_inference({"input": event["input"]})
    print(json)
    return json["output"]


if __name__ == "__main__":
    wait_for_service(url=f'{LOCAL_URL}/health-check')

    print("Cog API Service is ready. Starting RunPod serverless handler...")

    runpod.serverless.start({"handler": handler})
