@Library('OpenSlateProd')_  // https://github.com/openslate/jenkins-shared-library

def customLintFunction = {
    cf 'test', "compose run -u root:docker --rm app /bin/bash -c 'pylama -r results/pylama.log || /bin/true'"
}

def customTestFunction = {
    cf 'test', "compose run -u root:docker --rm app /bin/bash -c 'nosetests -v ./src --with-xunit --xunit-file=results/report.xml || /bin/true'"
}

def customPublishTask = {
    cfPublish()
    sh "compose-flow -e ${env.DEPLOY_ENV} --project-name ${env.REPO_NAME} compose run -u root:docker --rm app /bin/bash ./scripts/publish.sh"
}

def publishWhen = { env.TAG_NAME }

openslatePipeline {
    mentions = '@roberto <@marcusian>'
    deployEnv = 'prod'
    lint = true
    lintFunction = customLintFunction
    test = true
    testFunction = customTestFunction
    publish = publishWhen
    publishFunction = customPublishTask
    deploy = false
}
