import os
import zipfile
import json
import urllib.request
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/lenovo/climora")
DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
SCRATCH_DIR = PROJECT_ROOT / "scratch"
SCRATCH_DIR.mkdir(exist_ok=True)
ZIP_PATH = SCRATCH_DIR / "dist_posix.zip"

APP_ID = "dipd0dx7w10zl"
BRANCH_NAME = "main"
REGION = "ap-south-1"

print("Step 1: Packaging frontend/dist with POSIX forward slashes...")
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(DIST_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            arcname = os.path.relpath(full_path, DIST_DIR).replace("\\", "/")
            zf.write(full_path, arcname=arcname)
            print(f"  Added: {arcname}")

print(f"ZIP package created: {ZIP_PATH} ({ZIP_PATH.stat().st_size} bytes)")

print("\nStep 2: Calling aws amplify create-deployment...")
cmd = [
    "aws", "amplify", "create-deployment",
    "--app-id", APP_ID,
    "--branch-name", BRANCH_NAME,
    "--region", REGION,
    "--output", "json"
]
res = subprocess.run(cmd, capture_output=True, text=True, check=True)
deployment_info = json.loads(res.stdout)
job_id = deployment_info["jobId"]
zip_upload_url = deployment_info["zipUploadUrl"]
print(f"Deployment created: JobId = {job_id}")

print("\nStep 3: Uploading ZIP archive to S3 presigned URL via PUT...")
with open(ZIP_PATH, "rb") as f:
    zip_bytes = f.read()

req = urllib.request.Request(
    zip_upload_url,
    data=zip_bytes,
    headers={"Content-Type": "application/zip"},
    method="PUT"
)
with urllib.request.urlopen(req) as resp:
    print(f"Upload completed with HTTP status: {resp.status}")

print("\nStep 4: Starting Amplify deployment...")
cmd_start = [
    "aws", "amplify", "start-deployment",
    "--app-id", APP_ID,
    "--branch-name", BRANCH_NAME,
    "--job-id", job_id,
    "--region", REGION,
    "--output", "json"
]
res_start = subprocess.run(cmd_start, capture_output=True, text=True, check=True)
start_info = json.loads(res_start.stdout)
status = start_info["jobSummary"]["status"]
print(f"Start deployment triggered: initial status = {status}")

print("\nStep 5: Polling deployment status...")
import time
for i in range(20):
    time.sleep(3)
    cmd_poll = [
        "aws", "amplify", "get-job",
        "--app-id", APP_ID,
        "--branch-name", BRANCH_NAME,
        "--job-id", job_id,
        "--region", REGION,
        "--output", "json"
    ]
    res_poll = subprocess.run(cmd_poll, capture_output=True, text=True, check=True)
    poll_info = json.loads(res_poll.stdout)
    current_status = poll_info["job"]["summary"]["status"]
    print(f"  Check {i+1}: status = {current_status}")
    if current_status in ["SUCCEED", "FAILED"]:
        break

if current_status == "SUCCEED":
    print("\nSUCCESS: Amplify deployment succeeded!")
    print(f"Live URL: https://{BRANCH_NAME}.{APP_ID}.amplifyapp.com")
else:
    print(f"\nDeployment finished with status: {current_status}")

