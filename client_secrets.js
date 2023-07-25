const fs = require('fs');

let clientSecrets = {
    web: {
        client_id: process.env.GOOGLE_CLIENT_ID,
        project_id: process.env.GOOGLE_PROJECT_ID,
        auth_uri:"https://accounts.google.com/o/oauth2/auth",
        token_uri:"https://oauth2.googleapis.com/token",
        auth_provider_x509_cert_url:"https://www.googleapis.com/oauth2/v1/certs",
        client_secret:process.env.GCP_SECRET,
        redirect_uris:["http://localhost:8080","http://localhost:8080/"],
        javascript_origins:["https://chat.openai.com"],
    }
}

fs.writeFileSync('client_secrets.json', JSON.stringify(clientSecrets));
