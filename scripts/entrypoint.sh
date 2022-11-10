#!/bin/bash

# Is this kb-sdk magic?
#. /kb/deployment/user-env.sh

# More kb-sdk magic.
# python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties

if [ -f ./work/token ] ; then
  export KB_AUTH_TOKEN=$(<./work/token)
fi

if [ $# -eq 0 ] ; then
  dockerize -template ./templates/config.json.tmpl:./config/config.json
  #  ENTRYPOINT [ "dockerize" ]
  #
  #  CMD [ "-template", "./templates/config.json.tmpl:./config/config.json", \
  #    "sh", "./scripts/entrypoint.sh" ]
  sh ./scripts/start_server.sh
elif [ "${1}" = "test" ] ; then
  echo "Run Tests"
  make test
elif [ "${1}" = "init" ] ; then
  echo "Initialize module"
elif [ "${1}" = "bash" ] ; then
  bash
elif [ "${1}" = "report" ] ; then
  #  export KB_SDK_COMPILE_REPORT_FILE=./work/compile_report.json
  #  make compile
  cp ./compile_report.json ./work/compile_report.json
  echo "Compilation Report copied to ./work/compile_report.json"
else
  echo Unknown
fi