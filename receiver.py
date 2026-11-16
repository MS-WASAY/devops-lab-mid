from fastapi import FastAPI, Request
import json
import uvicorn

receiver_app = FastAPI()

@receiver_app.post("/report")
async def receive_report(request: Request):
    data = await request.json()
    with open("test-report.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("New test-report.json received and saved!")
    return {"status": "saved"}

if __name__ == "__main__":
    uvicorn.run(receiver_app, host="0.0.0.0", port=9000)
