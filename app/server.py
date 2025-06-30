import uvicorn
import os

# BaseDir
base_dir = os.path.dirname(os.path.realpath(__file__))

# path_ssl_keyfile = os.path.join(base_dir, "certs/privkey.pem")
# path_ssl_certfile = os.path.join(base_dir, "certs/fullchain.pem")
# path_ssl_keyfile = "/keys/privkey.pem"
# # path_ssl_certfile = "/keys/fullchain.pem"

if __name__ == '__main__':
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=int(os.environ.get("PORT", 8001)),
                reload=True)