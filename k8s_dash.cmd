@echo off

IF "%1" == "dev" (
	az aks browse --resource-group hnp-localedge-eastus-kubernetes-dev-rg --name lecdazrkube01
) ELSE IF "%1" == "ist" (
	az aks browse --resource-group hnp-localedge-eastus-kubernetes-dev-rg --name lecdazrkube01
) ELSE IF  "%1" == "qa" (
	az aks browse --resource-group hnp-localedge-eastus-kubernetes-qa-rg --name lecqazrkube01
) ELSE IF  "%1" == "staging" (
	az aks browse --resource-group hnp-localedge-eastus-kubernetes-staging-rg --name lecsazrkube01
) ELSE IF  "%1" == "stg" (
	az aks browse --resource-group hnp-localedge-eastus-kubernetes-staging-rg --name lecsazrkube01
) ELSE IF  "%1" == "prod" (
	az aks browse --resource-group hnp-localedge-eastus-kubernetes-prod-rg --name lecazrkube01
) ELSE IF  "%1" == "production" (
	az aks browse --resource-group hnp-localedge-eastus-kubernetes-prod-rg --name lecazrkube01
) ELSE (
	echo "Unexpected environment %1"
	EXIT /B 1
)