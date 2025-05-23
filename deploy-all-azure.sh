#!/bin/sh
for i in $(cat scripts/cicd/azuresites.txt); do
    tdnf install -y curl unzip && curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
    mv kubectl /usr/local/bin && chmod +x /usr/local/bin/kubectl
    curl -LO "https://github.com/Azure/kubelogin/releases/download/v0.0.28/kubelogin-linux-amd64.zip" && unzip kubelogin-linux-amd64.zip
    mv bin/linux_amd64/kubelogin /usr/local/bin && chmod +x /usr/local/bin/kubelogin
    az login -u ${AKS_USER} -p ${AKS_PASS} --service-principal -t b1c14d5c-3625-45b3-a430-9552373a0c2f
    az account set -s hostops-leveraged
    az aks get-credentials -g ${i}-lev-aks -n ${i}-lev-aks --overwrite-existing
    kubelogin convert-kubeconfig -l spn
    export AAD_SERVICE_PRINCIPAL_CLIENT_ID=${AKS_USER}
    export AAD_SERVICE_PRINCIPAL_CLIENT_SECRET=${AKS_PASS}
    echo "Updating nginx in ${i}"
    kubectl create cm nginx-base -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/nginxconf | kubectl replace -f -
    kubectl create cm nginx-acls -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/acls/${i}_acls | kubectl replace -f -
    kubectl create cm nginx-confd -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/conf.d/${i}_confd | kubectl replace -f -
    kubectl create cm nginx-defaultd -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/default.d | kubectl replace -f -
    kubectl create cm nginx-ssl -o yaml --dry-run=client -n nginx --from-file=kubernetes/nginx/ssl/${1}_ssl | kubectl replace -f -
    kubectl rollout restart -n nginx deploy/nginx
done
