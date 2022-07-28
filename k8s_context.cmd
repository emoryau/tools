@echo off

IF "%1" == "dev" (
	kubectl config use-context lecdazrkube02
) ELSE IF "%1" == "ist" (
	kubectl config use-context lecdazrkube02
) ELSE IF  "%1" == "qa" (
	kubectl config use-context lecqazrkube02
) ELSE IF  "%1" == "staging" (
	kubectl config use-context lecsazrkube02
) ELSE IF  "%1" == "stg" (
	kubectl config use-context lecsazrkube02
) ELSE IF  "%1" == "prod" (
	kubectl config use-context lecazrkube01
) ELSE IF  "%1" == "production" (
	kubectl config use-context lecazrkube01
) ELSE (
	echo "Unexpected environment %1"
	EXIT /B 1
)