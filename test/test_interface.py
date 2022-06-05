from fastapi import FastAPI, Request, Depends
import uvicorn
from config.config import SERVER_PORT, SERVER_HOST_IP

class Simple_dep:
    def __call__(self, request: Request):
        request.state.test = 'test'

app = FastAPI(
    dependencies=[Depends(Simple_dep())]
)

@app.get("")
async def root(request: Request):
    return {"test": request.state.test}

if __name__ == '__main__':
    uvicorn.run("test_interface:app", host=SERVER_HOST_IP, port=SERVER_PORT, log_level="info")


