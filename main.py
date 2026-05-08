import subprocess
def curl_request(url):
    
    # Define the command to execute using curl
    command = ['curl', '--proxy','http://127.0.0.1:8085', url]

    # Execute the curl command and capture the output
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Return the stdout of the curl command
    return result.stdout

# Make a curl request to https://www.google.com/
response = curl_request('https://www.google.com/')

# Make a curl request to https://www.google.com/
print(response)
