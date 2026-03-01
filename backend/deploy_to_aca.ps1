$ACR_NAME = "ca3fbe3e88bbacr"
$APP_NAME = "pnj-backend-web"
$RESOURCE_GROUP = "rg-pnj-cleaning"
$IMAGE_NAME = "pnj-cleaning-backend"
$TAG = "v" + (Get-Date -Format "yyyyMMdd-HHmmss")
$FULL_IMAGE = "$ACR_NAME.azurecr.io/$IMAGE_NAME:$TAG"

Write-Host "Building and pushing image $FULL_IMAGE to ACR $ACR_NAME..."
az acr build --registry $ACR_NAME --image $FULL_IMAGE .

Write-Host "Updating Container App $APP_NAME in $RESOURCE_GROUP with new image..."
az containerapp update --name $APP_NAME --resource-group $RESOURCE_GROUP --image $FULL_IMAGE

Write-Host "Deployment to Container App completed!"
