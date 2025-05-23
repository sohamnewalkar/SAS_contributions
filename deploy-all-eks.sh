#!/bin/bash

# Define the input file
input_file="scripts/cicd/awssites.properties"
echo "Deploy all AWS script"

# Read the content of the file into an array
mapfile -t sites < "$input_file"

# Read the content of the file into an array, trimming extra spaces
mapfile -t sites < <(sed 's/^[[:space:]]*//;s/[[:space:]]*$//' "$input_file")

# Iterate over the array
for entry in "${sites[@]}"; do
    IFS=: read -r site region <<< "$entry"
    
    if [[ -z "$site" || -z "$region" ]]; then
        echo "Skipping empty line."
        continue
    fi
    
    echo "Processing site: $site, region: $region"
    aws eks update-kubeconfig --name "${site}-lev-eks" --region "$region"

    echo "Updating nginx in $site"
    
    kubectl create cm nginx-base -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/nginxconf | kubectl replace -f -
    kubectl create cm nginx-acls -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/acls/${site}_acls | kubectl replace -f -
    kubectl create cm nginx-confd -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/conf.d/${site}_confd | kubectl replace -f -
    kubectl create cm nginx-defaultd -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/default.d | kubectl replace -f -
    kubectl create cm nginx-ssl -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/ssl/${site}_ssl | kubectl replace -f -
    kubectl rollout restart -n nginx deploy/nginx
    
done

