from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import certifi  # Import certifi for CA certificates

# Connection string with SSL enabled
uri = "mongodb+srv://lenno:91CSjNjdYExsWIkK@cluster0.p5luf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, tlsCAFile=certifi.where(), server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
