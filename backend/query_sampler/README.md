# RAT: Query Sampler
#### Access the documentation for the backend at: https://searchstudies.org/rat-backend-documentation/

## Setting Up the Query Sampler

1. **Get a developer token to use the Google Ads API**  
   https://developers.google.com/google-ads/api/docs/get-started/dev-token?hl=en

2. **Set up your Google Ads account**
https://developers.google.com/google-ads/api/docs/oauth/overview?hl=en

3. **This simple tutorial shows how to set it all up**  
 https://www.danielherediamejias.com/python-keyword-planner-google-ads-api/

4. **Create your user credentials and change the token in your google-ads.yaml**
    ```bash
    python generate_user_credentials.py --client_secrets_path=client.json
    ```
5. **Start the Query Sampler**
    ```bash
    python query_sampler_controller_start.py