$RESOURCE_GROUP = "rg-pnj-cleaning"
$ENV_NAME = "env-pnj-web"
$APP_NAME = "pnj-backend-web"
$IMAGE = "ca3fbe3e88bbacr.azurecr.io/pnj-cleaning-backend:cli-containerapp-20260202091056284595"

Write-Host "Deploying to NEW Environment $ENV_NAME..."

# Deploy with all fixes applied
az containerapp create --name $APP_NAME --resource-group $RESOURCE_GROUP `
    --environment $ENV_NAME `
    --image $IMAGE `
    --target-port 8000 `
    --ingress external `
    --min-replicas 1 `
    --env-vars "SUPABASE_URL=https://ruaseemcgxvbcjazhhfw.supabase.co" "SUPABASE_KEY=sb_publishable_dPA9xqq4yyGg6869fCuMLA_tCXIKXOu" "SECRET_KEY=supersecretkeyforpnjcleaning" `
    --startup-probe-path "/login" --startup-probe-port 8000 `
    --readiness-probe-path "/login" --readiness-probe-port 8000 `
    --liveness-probe-path "/login" --liveness-probe-port 8000

Write-Host "Deployment initiated."
