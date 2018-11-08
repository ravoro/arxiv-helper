#!/usr/bin/env bash
# Script for deploying the latest code in the repo.

# DB settings
[[ -z "$DB_NAME" ]] && { echo "DB_NAME envvar not set"; exit; }
[[ -z "$DB_HOST" ]] && { echo "DB_HOST envvar not set"; exit; }
[[ -z "$DB_USER" ]] && { echo "DB_USER envvar not set"; exit; }
[[ -z "$DB_PASS" ]] && { echo "DB_PASS envvar not set"; exit; }

# Base project directory
[[ -z "$BASE_DIR" ]] && { echo "BASE_DIR envvar not set"; exit; }

# Directory that will store (trash) the old version of site after deploy
[[ -z "$TRASH_DIR" ]] && { echo "TRASH_DIR envvar not set"; exit; }

# Directory with deploy-related files
DEPLOY_DIR="${BASE_DIR}/deploy"

# Directory with website content (the directory that will be renewed)
SITE_DIR="${BASE_DIR}/public_html"

# Directory that will store backup of current version of the site
BACKUP_DIR="${BASE_DIR}/backups"

# Directory that will temporarily store the new website content as it is being built
TMP_DIR="${BASE_DIR}/public_html_tmp"

# Git repo containing code that will be deployed
GIT_REPO="https://github.com/ravoro/arxiv-helper.git"

# Date variable used for distinguishing files by time between different deploys
DATE="$(date +%Y%m%d-%s)"


function ensure_required_files_exist() {
    REQUIRED_FILES="${SITE_DIR} ${BACKUP_DIR} ${DEPLOY_DIR}/conf.py ${DEPLOY_DIR}/wsgi.py ${DEPLOY_DIR}/apache.conf"
    for FILE in ${REQUIRED_FILES}; do
        if [ ! -e ${FILE} ]; then
            echo "Required directory (${FILE}) does not exist."
            exit
        fi
    done
}


function backup_db() {
    echo -e "\nCreating gz backup of current database ..."
    mysqldump -u ${DB_USER} -h ${DB_HOST} -p${DB_PASS} ${DB_NAME} | gzip -9 > ${BACKUP_DIR}/db-${DATE}.sql.gz
}


function backup_site() {
    echo -e "\nCreating tgz backup of current version of site ..."
    tar czf ${BACKUP_DIR}/public_html-${DATE}.tgz ${SITE_DIR}
}


function fetch_new_code() {
    echo -e "\nFetching latest code from repo ..."
    git clone ${GIT_REPO} --depth 1 ${TMP_DIR}
    rm -rf ${TMP_DIR}/.git
}


function setup_config() {
    echo -e "\nConfiguring the new code ..."
    cp ${DEPLOY_DIR}/conf.py ${TMP_DIR}/project/settings/prod.py
    cp ${DEPLOY_DIR}/wsgi.py ${TMP_DIR}/project/wsgi_prod.py
}


function trash_current_site() {
    echo -e "\nTrashing current version of the site ..."
    mkdir -p ${TRASH_DIR}
    mv ${SITE_DIR} ${TRASH_DIR}
}


function enable_new_site() {
    echo -e "\nEnabling new version of the website ..."
    mv ${TMP_DIR} ${SITE_DIR}
}


function setup_virtualenv() {
    echo -e "\nSetting up virtualenv and fetching requirements ..."
    virtualenv -p python3 ${SITE_DIR}/venv
    source ${SITE_DIR}/venv/bin/activate
    pip install -r ${SITE_DIR}/requirements.txt
    deactivate
}


function collect_static() {
    echo -e "\nCollect static ..."
    source ${SITE_DIR}/venv/bin/activate
    ${SITE_DIR}/manage.py collectstatic --settings=project.settings.prod
    deactivate
}


function migrate_db() {
    echo -e "\nMigrating any db changes ..."
    source ${SITE_DIR}/venv/bin/activate
    ${SITE_DIR}/manage.py migrate --settings=project.settings.prod
    deactivate
}


function setup_crontab() {
    echo -e "\nSetting up crontab ..."
    source ${SITE_DIR}/venv/bin/activate
    ${SITE_DIR}/manage.py crontab add --settings=project.settings.prod
    deactivate
}


function setup_apache() {
    echo -e "\nSetting up apache ..."
    cp -f ${DEPLOY_DIR}/apache.conf /etc/apache2/sites-available/arxivhelper.conf
}


function restart_apache() {
    # If running in embedded mode (instead of daemon), need to restart apache to reflect code changes
    # https://modwsgi.readthedocs.io/en/develop/user-guides/reloading-source-code.html
    echo -e "\nRestarting apache ..."
    a2ensite arxivhelper.conf
    service apache2 restart
}


ensure_required_files_exist
cd ${BASE_DIR}
backup_db
backup_site
fetch_new_code
setup_config
# TODO: Add apache "under maintenance"
trash_current_site
enable_new_site
setup_virtualenv
collect_static
migrate_db
setup_crontab
setup_apache
restart_apache
echo -e "\nDeployment done!"
