KBASE_ENDPOINT=ci.kbase.us \
KBASE_SECURE_CONFIG_PARAM_ORCID_CLIENT_ID=${ORCID_CLIENT_ID} \
KBASE_SECURE_CONFIG_PARAM_ORCID_CLIENT_SECRET=${ORCID_CLIENT_SECRET} \
KBASE_SECURE_CONFIG_PARAM_IS_DYNAMIC_SERVICE=yes \
DEV=yes \
docker compose up