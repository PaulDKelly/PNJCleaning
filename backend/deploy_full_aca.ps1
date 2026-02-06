$RESOURCE_GROUP = "rg-pnj-cleaning"
$ACR_NAME = "ca3fbe3e88bbacr"
$APP_NAME = "pnj-cleaning-backend"
$IMAGE_TAG = Get-Date -Format "yyyyMMddHHmmss"
$IMAGE_NAME = "$ACR_NAME.azurecr.io/pnj-cleaning-backend:$IMAGE_TAG"

Write-Host "1. Building and Pushing Image to ACR ($ACR_NAME)..."
az acr build --registry $ACR_NAME --image pnj-cleaning-backend:$IMAGE_TAG .

if ($LASTEXITCODE -eq 0) {
    Write-Host "2. Updating Container App ($APP_NAME) with new image..."
    az containerapp update --name $APP_NAME --resource-group $RESOURCE_GROUP --image $IMAGE_NAME
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Deployment Complete!"
        az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query properties.configuration.ingress.fqdn --output tsv
    }
    else {
        Write-Host "❌ Failed to update Container App."
    }
}
else {
    Write-Host "❌ Failed to build image."
}
