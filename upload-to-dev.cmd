@ECHO OFF

REM Make sure context is DEV
CALL k8s_context dev

REM Fetch the pod name
FOR /F "tokens=2 delims=/ USEBACKQ" %%F IN (`kubectl get pods -o=name -l com.localedge/app^=atlas-theme`) DO (
SET pod=%%F
)
ECHO POD: %pod%

ECHO Upload atlas-bundle.min.js
kubectl cp target\dist\atlas-bundle.min.js    %pod%:/usr/share/nginx/html/atlas-theme/dist/atlas-bundle.min.js
ECHO Upload atlas-templates.min.js
kubectl cp target\dist\atlas-templates.min.js %pod%:/usr/share/nginx/html/atlas-theme/dist/atlas-templates.min.js
ECHO Upload atlas.min.css
kubectl cp target\dist\atlas.min.css          %pod%:/usr/share/nginx/html/atlas-theme/dist/atlas.min.css
ECHO Done.