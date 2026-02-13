$RESOURCE_GROUP = "rg-pnj-cleaning"
$APP_NAME = "pnj-cleaning-backend-web"
$LOCATION = "uksouth"

# 1. Deploy Web App (Plan + App + Code)
# using 'az webapp up' which handles zipping and deploying local code
Write-Host "Deploying Web App to '$APP_NAME' in '$RESOURCE_GROUP'..."
az webapp up --name $APP_NAME --resource-group $RESOURCE_GROUP --sku B1 --runtime "PYTHON:3.9" --location $LOCATION

# 2. Configure Settings
Write-Host "Configuring Environment Variables..."
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP --settings `
    SCM_DO_BUILD_DURING_DEPLOYMENT=true `
    SUPABASE_URL="https://ruaseemcgxvbcjazhhfw.supabase.co" `
    SUPABASE_KEY="sb_publishable_dPA9xqq4yyGg6869fCuMLA_tCXIKXOu" `
    SECRET_KEY="supersecretkeyforpnjcleaning" `
    AZURE_POSTGRESQL_CONNECTIONSTRING="PlaceholderIfneeded" `
    WEBSITES_PORT=8000

# 3. Configure Startup Command
Write-Host "Setting Startup Command..."
az webapp config set --name $APP_NAME --resource-group $RESOURCE_GROUP --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

Write-Host "Deployment Completed!"
Write-Host "URL: https://$APP_NAME.azurewebsites.net"
