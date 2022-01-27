from datetime import datetime
from os import path
import json
TODAY = datetime.now().strftime('%Y-%m-%d')

def run(record_type, message):

    with open(path.join('data','records',f'{TODAY}.{record_type}'),'a') as file:
        file.write(json.dumps(message))
        file.write("\n")