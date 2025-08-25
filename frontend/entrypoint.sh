#!/bin/sh

# Exit on any error
set -e

# Default to 'development' if APP_ENV is not set
if [ -z "$APP_ENV" ]; then
  APP_ENV="development"
fi

echo "Configuring for environment: $APP_ENV"

# Select the API URL based on the APP_ENV variable
if [ "$APP_ENV" = "production" ]; then
  API_URL="$REACT_APP_PROD_API_URL"
elif [ "$APP_ENV" = "staging" ]; then
  API_URL="$REACT_APP_STAGING_API_URL"
else
  API_URL="$REACT_APP_DEV_API_URL"
fi

echo "Using API URL: $API_URL"

# Create the final config.js file in the Nginx web root
# This will overwrite the placeholder file from the build.
cat > /usr/share/nginx/html/config.js <<EOF
window.runtimeConfig = {
  API_BASE_URL: "${API_URL}"
};
EOF

# Start Nginx in the foreground
exec nginx -g 'daemon off;'
