from fault.fault_monitor import *

app = FastAPI(
    dependencies=[Depends(FaultMonitor())]
)

@app.get("/get_error")
async def root(request: Request):
    return request.state.fault_range

if __name__ == '__main__':
    # monitor = FaultMonitor()
    # monitor.run()
    uvicorn.run("main:app", host=SERVER_HOST_IP, port=SERVER_PORT, log_level="info")

