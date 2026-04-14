from fastapi import FastAPI
import redis
import boto3
import uuid
from datetime import datetime

app = FastAPI()

# Redis connection (same URL as your worker)
r = redis.Redis.from_url(
    "rediss://default:gQAAAAAAAX6eAAIncDIyOWNhN2MzOWUxNDk0MmVhYjAzZTIzN2RkNGM5ZDg1Y3AyOTc5NTA@pro-lemur-97950.upstash.io:6379",
    ssl_cert_reqs=None,
    decode_responses=True
)

# Storj/R2 connection - UPDATE THESE WITH YOUR REAL KEYS
s3 = boto3.client('s3',
    endpoint_url='https://f76d2ce8d05a169a24d24d6895c13dd7.r2.cloudflarestorage.com',
    aws_access_key_id='8a88c9ea5c1eab615f51fc6d339e5550',
    aws_secret_access_key='0dab2a649eef436523a727b883ef8267731187d906f196e8d47990ea5c012057',
    region_name='auto')

@app.get("/")
def health():
    return {"status": "live", "service": "sportsai-api"}

@app.post("/upload")
def create_upload(filename: str):
    job_id = str(uuid.uuid4())
    
    # Generate presigned URL for direct upload to R2
    upload_url = s3.generate_presigned_url('put_object',
        Params={'Bucket': 'sportsai-videos', 'Key': f'{job_id}/{filename}'},
        ExpiresIn=3600)
    
    # Add to Redis queue for your local worker
    r.lpush("video_queue", f"{job_id}/{filename}")
    r.set(f"job:{job_id}:status", "queued")
    
    return {
        "jobId": job_id,
        "uploadUrl": upload_url,
        "status": "queued"
    }

@app.get("/status/{job_id}")
def check_status(job_id: str):
    status = r.get(f"job:{job_id}:status") or "unknown"
    output = r.get(f"job:{job_id}:output")
    return {"jobId": job_id, "status": status, "output": output}