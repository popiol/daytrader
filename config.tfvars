inp = {
  app = {
    name = "${APP_NAME}"
    ver = "${APP_VER}"
    id = "${APP_NAME}_${APP_VER}"
  }

  aws_region = "${AWS_REGION}"

  aws_user = "${AWS_USER}"

  temporary = "${TEMP_DEPLOY}"

  notify_email_addr = "${NOTIFY_EMAIL_ADDR}"
}