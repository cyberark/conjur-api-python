echo "Building API container..."
docker-compose --file "$CONPOSE_FILE_PATH" --project-directory "${PWD}" build test

echo "Generating certificate..."
docker-compose --file "$CONPOSE_FILE_PATH" --project-directory "${PWD}" up openssl

echo "Starting Conjur..."
docker-compose --file "$CONPOSE_FILE_PATH" --project-directory "${PWD}" up -d conjur
docker-compose --file "$CONPOSE_FILE_PATH" --project-directory "${PWD}" exec -T conjur conjurctl wait

echo "Configuring Conjur..."
admin_api_key=$(docker-compose --file "$CONPOSE_FILE_PATH" --project-directory "${PWD}" exec -T conjur conjurctl role retrieve-key dev:user:admin | tr -d '\r')
export CONJUR_AUTHN_API_KEY=$admin_api_key
export DEBUG=$DEBUG
conjur_host_port=$(docker-compose --file "$CONPOSE_FILE_PATH" --project-directory "${PWD}" port conjur 80)
conjur_port="${conjur_host_port##*:}"
export TEST_HOSTNAME=conjur-https

cat <<ENV >.env
CONJUR_AUTHN_API_KEY=$admin_api_key
DEBUG=$DEBUG
ENV

